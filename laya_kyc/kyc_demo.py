"""Live-Demo ohne Kogito: BPMN-Pfad Regeln → Laya → Freigabe, manuelle Prüfung oder Ablehnung für K01–K15.

Beispiele:
    python kyc_demo.py                       # angepasstes Modell, alle Demo-Fälle
    python kyc_demo.py --compare             # zusätzlich Basismodell ohne Anpassung
    python kyc_demo.py --case K11 --show-input
"""
import argparse
import warnings
from pathlib import Path

import laya

import kyc_data as K
from demo_cases import CASES

FINETUNED_MODEL = K.PROJECT_DIR / "modelle" / "laya-multilingual-kyc-v2"
# Trainiert wurde mit 1.024 Tokens. Längere Demo-Fälle werden nicht abgeschnitten, sondern mit
# erhöhtem Limit bewertet (mmBERT-Encoder: bis 8.192) und in der Ausgabe markiert.
MAX_LEN = 2048


def process_path(application, decision):
    """BPMN: automatische Freigabe nur bei grünen Regeln und Laya `keine_manuelle_pruefung`.

    R5 (bestätigter Sanktionstreffer) lehnt im Prozess ab, bevor Laya gefragt wird; die Laya-Antwort
    wird hier nur zum Vergleich angezeigt."""
    if application["screening"]["sanktionsscreening_status"] == "bestaetigter_treffer":
        return "Ablehnung (R5)"
    rules = list(application["regelpruefung"]["ausgeloeste_regeln"])
    if K.has_us_nexus(application):
        rules.append("R4")
    if rules:
        return f"Prüfbedarf ({', '.join(rules)}) → manuelle Prüfung"
    if decision == "keine_manuelle_pruefung":
        return "Freigabe"
    return "manuelle Prüfung" + (" (Laya unklar)" if decision == "unklar" else "")


def endpoint(path):
    """Endpunkt eines Pfadtexts: Freigabe, Ablehnung oder manuelle Prüfung."""
    path = path.strip()
    return next((e for e in ("Freigabe", "Ablehnung") if path.startswith(e)), "manuelle Prüfung")


def token_lengths(agent, cases):
    """Tokenlänge je Fall; bricht ab, falls auch das erhöhte Limit nicht reicht."""
    without_target = [{**c, "sollbewertung": {"entscheidung": "unklar"}} for c in cases]
    return [len(it["ids"]) for it in K.build_items(agent.tok, without_target, MAX_LEN, agent.cfg["head_max_len"])]


def assess(agent, cases):
    states = [K.model_state(c["eingabe"]) for c in cases]
    results = agent.predict_batch(states, {"entscheidung": K.QUESTION_API}, max_len=MAX_LEN)
    if any(r["usage"]["truncated"] for r in results):
        raise SystemExit("Eingabe wurde abgeschnitten; MAX_LEN erhöhen.")
    return [r["answers"]["entscheidung"] for r in results]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=str(FINETUNED_MODEL))
    ap.add_argument("--compare", action="store_true", help="Basismodell ohne Anpassung daneben zeigen")
    ap.add_argument("--case", help="nur diesen Fall, z. B. K11")
    ap.add_argument("--show-input", action="store_true")
    ap.add_argument("--device", default="mps")
    args = ap.parse_args()
    warnings.filterwarnings("ignore")

    cases = [c for c in CASES if not args.case or c["kunden_id"] == args.case]
    name = "basis" if Path(args.model).resolve() == K.BASE_MODEL else "angepasst"
    models = [(name, args.model)]
    if args.compare and name != "basis":
        models.insert(0, ("basis", str(K.BASE_MODEL)))
    agents = {n: laya.load(path, device=args.device) for n, path in models}
    answers = {n: assess(a, cases) for n, a in agents.items()}
    first_agent = next(iter(agents.values()))
    tokens = token_lengths(first_agent, cases)
    trained_len = first_agent.cfg["max_len"]

    hits = {n: 0 for n, _ in models}
    for i, case in enumerate(cases):
        app = case["eingabe"]
        print(f"\n{case['kunden_id']}  {app['kunde']['vorname']} {app['kunde']['nachname']}, "
              f"{app['beschaeftigung']['beruf']}  |  Regeln: {app['regelpruefung']['ergebnis']}  |  "
              f"{tokens[i]} Tokens" + (f" (über Trainingslänge {trained_len})" if tokens[i] > trained_len else ""))
        if args.show_input:
            print("  " + K.case_text(app).replace("\n", "\n  "))
        print(f"  erwartet:   {case['expected_path']}")
        for n, _ in models:
            answer = answers[n][i]
            p = answer["probabilities"]
            path = process_path(app, answer["choice"])
            ok = endpoint(path) == endpoint(case["expected_path"].split("→")[-1])
            hits[n] += ok
            print(f"  {n:<10}  {'✓' if ok else '✗'} {path:<40} "
                  f"keine {p['keine_manuelle_pruefung']:.2f} | manuell {p['manuelle_pruefung']:.2f} | "
                  f"unklar {p['unklar']:.2f}")

    print()
    for n, _ in models:
        print(f"{n}: {hits[n]}/{len(cases)} Fälle mit erwartetem Endpfad")
    print("Hinweis: Laya liefert Entscheidung und Wahrscheinlichkeiten, keine Begründung oder Feldbelege.")


if __name__ == "__main__":
    main()
