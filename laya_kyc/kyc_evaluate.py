"""Evaluation eines Laya-Checkpoints auf einem Split der KYC-Daten.

Der Checkpoint wird über `laya.load` geladen, also über denselben Weg wie im Betrieb.
Bewertet werden die Modellentscheidung und der BPMN-Pfad:
automatische Freigabe nur bei grünem Regelergebnis UND Modellentscheidung
`keine_manuelle_pruefung`; sonst manuelle Prüfung.

Beispiel:
    python kyc_evaluate.py --model ../modelle/laya-multilingual-base --split validation --name basis
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch

import laya
from laya.common import QTYPES, temp_bucket

import kyc_data as K

RESULTS_DIR = K.PROJECT_DIR / "laya_kyc" / "ergebnisse"


def compute_metrics(customers, probs):
    pred = probs.argmax(1)
    n = len(customers)
    gold = np.array([K.target_index(c) for c in customers])
    needs_review = np.array([c["sollbewertung"]["manuelle_pruefung_erforderlich"] for c in customers])
    green = np.array([not K.has_rule_trigger(c["eingabe"]) for c in customers])
    model_release = pred == K.OPTIONS.index("keine_manuelle_pruefung")
    auto_release = green & model_release          # BPMN: Regeln grün und LLM "keine"

    def path_block(mask):
        g, f = needs_review[mask], auto_release[mask]
        return {
            "faelle": int(mask.sum()),
            "faelschlich_automatisch_freigegeben": int((g & f).sum()),
            "unnoetig_manuell": int((~g & ~f).sum()),
            "korrekt_weitergeleitet": int((g & ~f).sum()),
            "korrekt_freigegeben": int((~g & f).sum()),
            "genauigkeit_pfad": round(float((g == ~f).mean()), 4) if mask.any() else None,
        }

    p_gold = probs[np.arange(n), gold]
    confidence = probs.max(1)
    correct = pred == gold
    bins = np.linspace(0, 1, 11)
    ece = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        in_bin = (confidence > lo) & (confidence <= hi)
        if in_bin.any():
            ece += in_bin.mean() * abs(correct[in_bin].mean() - confidence[in_bin].mean())

    confusion = {g: {p: 0 for p in K.OPTIONS} for g in K.OPTIONS}
    for g_i, p_i in zip(gold, pred):
        confusion[K.OPTIONS[g_i]][K.OPTIONS[p_i]] += 1

    errors_by_scenario = defaultdict(lambda: {"faelle": 0, "pfad_fehler": 0})
    for c, g, f in zip(customers, needs_review, auto_release):
        entry = errors_by_scenario[c["metadaten"]["szenario"]]
        entry["faelle"] += 1
        entry["pfad_fehler"] += int(g == f)

    return {
        "faelle": n,
        "modell": {
            "genauigkeit_3_klassen": round(float(correct.mean()), 4),
            "nll": round(float(-np.log(np.clip(p_gold, 1e-12, 1)).mean()), 4),
            "ece_10_bins": round(float(ece), 4),
            "vorhersagen": dict(Counter(K.OPTIONS[i] for i in pred)),
            "verwechslungsmatrix_soll_zu_ist": confusion,
        },
        "bpmn_pfad_alle": path_block(np.ones(n, bool)),
        "bpmn_pfad_regelgruen": path_block(green),
        "szenarien": dict(sorted(errors_by_scenario.items())),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--split", choices=["train", "validation", "test"], required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--data", default=str(K.DATA_FILE), help="Datensatz (JSON mit kunden)")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--batch", type=int, default=8)
    args = ap.parse_args()

    model_path = str(Path(args.model).resolve())
    agent = laya.load(model_path, device=args.device)
    customers = [c for c in K.load_customers(args.data) if c["metadaten"]["split"] == args.split]
    items = K.build_items(agent.tok, customers, agent.cfg["max_len"], agent.cfg["head_max_len"])

    temperature = agent.temperature_by_options.get(temp_bucket(QTYPES["choice"], len(K.OPTIONS)),
                                                   agent.temperature[QTYPES["choice"]])
    logits = K.option_logits(agent.model.float(), items, agent.tok.pad_token_id, agent.device, args.batch)
    probs = torch.softmax(logits / temperature, -1).numpy()

    # Gegenprobe: dieselben Wahrscheinlichkeiten über die öffentliche Laya-API.
    api_results = agent.predict_batch([K.model_state(c["eingabe"]) for c in customers[:3]],
                                      {"entscheidung": K.QUESTION_API})
    for i, result in enumerate(api_results):
        answer = result["answers"]["entscheidung"]
        p_api = np.array([answer["probabilities"][o] for o in K.OPTIONS])
        if np.abs(p_api - probs[i]).max() > 0.02:
            raise SystemExit(f"API-Gegenprobe weicht ab: {p_api} vs {probs[i]}")

    result = {"name": args.name, "modell": model_path, "split": args.split, "temperatur": temperature,
              **compute_metrics(customers, probs)}
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stem = RESULTS_DIR / f"{args.name}_{args.split}"
    stem.with_suffix(".json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    with open(stem.with_name(stem.name + "_vorhersagen.jsonl"), "w") as f:
        for c, p in zip(customers, probs):
            f.write(json.dumps({
                "kunden_id": c["kunden_id"],
                "szenario": c["metadaten"]["szenario"],
                "regelergebnis": c["eingabe"]["regelpruefung"]["ergebnis"],
                "soll": c["sollbewertung"]["entscheidung"],
                "modell": K.OPTIONS[int(p.argmax())],
                "wahrscheinlichkeiten": {o: round(float(v), 4) for o, v in zip(K.OPTIONS, p)},
            }, ensure_ascii=False) + "\n")

    m, a, g = result["modell"], result["bpmn_pfad_alle"], result["bpmn_pfad_regelgruen"]
    print(f"{args.name} / {args.split}: Genauigkeit 3 Klassen {m['genauigkeit_3_klassen']:.3f}, "
          f"NLL {m['nll']:.3f}, ECE {m['ece_10_bins']:.3f}, Vorhersagen {m['vorhersagen']}")
    print(f"  BPMN alle:       fälschlich freigegeben {a['faelschlich_automatisch_freigegeben']}, "
          f"unnötig manuell {a['unnoetig_manuell']}, Pfadgenauigkeit {a['genauigkeit_pfad']}")
    print(f"  BPMN regelgrün:  fälschlich freigegeben {g['faelschlich_automatisch_freigegeben']}, "
          f"unnötig manuell {g['unnoetig_manuell']}, Pfadgenauigkeit {g['genauigkeit_pfad']}")
    print(f"  gespeichert: {stem}.json")


if __name__ == "__main__":
    main()
