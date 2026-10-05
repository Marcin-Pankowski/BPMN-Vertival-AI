"""Gegenproben: Reagiert das Modell auf die Wohnadresse oder auf etwas anderes?

Nimmt Testfälle des ursprünglichen Datensatzes (Varianten 1–5, nie im Training) und ändert jeweils
genau ein Merkmal. Bewertet wird, ob die Entscheidung dem erwarteten Wechsel folgt.

    python kyc_counterfactuals.py --model ../modelle/laya-multilingual-kyc --name v1 --device cpu
"""
import argparse
import copy
import json
import random
import warnings

import laya

import kyc_data as K
from augment_dataset import GREEN_OK_SCENARIOS, neutral_address, trigger_address

RESULTS_DIR = K.PROJECT_DIR / "laya_kyc" / "ergebnisse"
MAX_LEN = 2048


def decisions(agent, applications):
    states = [K.model_state(a) for a in applications]
    results = agent.predict_batch(states, {"entscheidung": K.QUESTION_API}, batch_size=8, max_len=MAX_LEN)
    return [r["answers"]["entscheidung"]["choice"] for r in results]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--device", default="mps")
    args = ap.parse_args()
    warnings.filterwarnings("ignore")
    rng = random.Random(7)

    test = [c for c in K.load_customers() if c["metadaten"]["split"] == "test"]
    ok_cases = [c for c in test if c["metadaten"]["szenario"] in GREEN_OK_SCENARIOS]
    with_employer = [c for c in ok_cases if c["eingabe"]["beschaeftigung"]["arbeitgeber"]]
    address_cases = [c for c in test if c["metadaten"]["szenario"] == "adresse_reeperbahn_umfeld_pruefbedarf"]

    probes = {}
    apps = []
    for c in ok_cases:
        a = copy.deepcopy(c["eingabe"]); a["kunde"]["adresse"] = trigger_address(rng); apps.append(a)
    probes["Wohnadresse ins Reeperbahn-Umfeld verlegt (Soll: manuell)"] = (apps, "manuell")
    apps = []
    for c in with_employer:
        a = copy.deepcopy(c["eingabe"]); a["beschaeftigung"]["arbeitgeber"].update(trigger_address(rng)); apps.append(a)
    probes["Nur Arbeitgeber ins Reeperbahn-Umfeld verlegt (Soll: keine)"] = (apps, "keine")
    apps = []
    for c in address_cases:
        for _ in range(3):
            a = copy.deepcopy(c["eingabe"]); a["kunde"]["adresse"] = neutral_address(rng); apps.append(a)
    probes["Adressfall an unauffällige Wohnadresse verlegt (Soll: keine)"] = (apps, "keine")
    probes["Unveränderte unauffällige Fälle (Soll: keine)"] = ([c["eingabe"] for c in ok_cases], "keine")
    probes["Unveränderte Adressfälle (Soll: manuell)"] = ([c["eingabe"] for c in address_cases], "manuell")

    agent = laya.load(args.model, device=args.device)
    report = {"name": args.name, "modell": args.model, "gegenproben": {}}
    for title, (applications, expected) in probes.items():
        got = decisions(agent, applications)
        hits = sum((d == "keine_manuelle_pruefung") == (expected == "keine") for d in got)
        report["gegenproben"][title] = {"faelle": len(got), "wie_erwartet": hits, "quote": round(hits / len(got), 3)}
        print(f"{args.name}: {title:<62} {hits:>3}/{len(got):<3} ({hits / len(got):.0%})")
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / f"{args.name}_gegenproben.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
