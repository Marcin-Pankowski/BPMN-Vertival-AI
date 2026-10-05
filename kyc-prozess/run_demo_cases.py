"""Ende-zu-Ende-Demo: startet für jeden Demo-Fall (K01–K15) eine Prozessinstanz im Kogito-Dienst.

Voraussetzung: Laya-Dienst (Port 8000) und Kogito-Dienst (Port 8080) laufen.
Fälle mit manueller Prüfung bleiben als offene Aufgabe der Gruppe kyc-reviewers stehen.

    python3 run_demo_cases.py
    python3 run_demo_cases.py --decide approve    # offene Aufgaben anschließend abschließen
"""
import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

KOGITO_URL = "http://localhost:8080"
REVIEWER = "user=anna&group=kyc-reviewers"
CASES_FILE = Path(__file__).resolve().parent.parent / "laya_kyc" / "demo_cases.json"


def http(method, path, payload=None):
    request = urllib.request.Request(KOGITO_URL + path, method=method,
                                     data=json.dumps(payload).encode() if payload is not None else None,
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read() or "null")
    except urllib.error.HTTPError as e:
        return e.code, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decide", choices=["approve", "reject"])
    args = ap.parse_args()

    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))["kunden"]
    hits = 0
    for case in cases:
        # regelpruefung berechnet der Prozess selbst
        application = {k: v for k, v in case["eingabe"].items() if k != "regelpruefung"}
        status, result = http("POST", "/kyc_review", {"application": application})
        if status != 201:
            print(f"{case['kunden_id']}: Start fehlgeschlagen (HTTP {status})")
            continue
        active = http("GET", f"/kyc_review/{result['id']}")[0] == 200
        if active:
            path, expected = "manuelle Prüfung (offen)", "manuelle Prüfung"
        elif result["rule_result"] == "reject":
            path, expected = "Ablehnung (Regeln)", "Ablehnung"
        else:
            path, expected = "Freigabe (automatisch)", "Freigabe"
        ok = case["expected_path"].split("→")[-1].strip().startswith(expected)   # letzter Schritt des Pfads
        hits += ok
        llm = result["llm_result"] or {"decision": "-"}
        p = llm.get("probabilities") or {}
        rules = ",".join(result["triggered_rules"]) or "-"
        print(f"{case['kunden_id']}  Regeln {result['rule_result']:<6} {rules:<6} Laya {llm['decision']:<24} "
              f"p(keine)={p.get('keine_manuelle_pruefung', 0):.2f}  ->  {path:<26} {'✓' if ok else '✗'} "
              f"(erwartet: {case['expected_path']})")
    print(f"\n{hits}/{len(cases)} Fälle mit erwartetem Endpfad")

    _, tasks = http("GET", f"/usertasks/instance?{REVIEWER}")
    open_tasks = [t for t in tasks if t["status"]["name"] in ("Ready", "Reserved")]
    print(f"Offene manuelle Prüfungen: {len(open_tasks)}  (GET {KOGITO_URL}/usertasks/instance?{REVIEWER})")
    if args.decide:
        for task in open_tasks:
            url = f"/usertasks/instance/{task['id']}/transition?{REVIEWER}"
            if task["status"]["name"] == "Ready":
                http("POST", url, {"transitionId": "claim"})
            http("POST", url, {"transitionId": "complete", "data": {"decision": args.decide, "comment": "Demo"}})
        print(f"{len(open_tasks)} Aufgaben mit '{args.decide}' abgeschlossen")


if __name__ == "__main__":
    main()
