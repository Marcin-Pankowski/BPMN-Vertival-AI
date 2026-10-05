# KYC-Prüfprozess als Kogito-Microservice

Ausführbare Fassung von `../KYC_Pruefprozess.bpmn` mit Kogito 10.2.0 auf Quarkus 3.27.2 (Java 21), mit Weboberfläche zum manuellen Testen und Dashboard für den Ablauf einzelner Instanzen. Alles läuft im Arbeitsspeicher.

## Architektur

```
Browser (http://localhost:8080)
  Antrag prüfen · Manuelle Prüfung · Dashboard (bpmn-js)
        │
        ▼
┌──────────────────────── Kogito (Port 8080) ────────────────────────┐
│ POST /kyc_review {application}                                      │
│ Prüfung nach Regeln   DMN KYC_RuleCheck (R1–R5, COLLECT)            │
│        │  rule_result = green | review | reject (R5 → Ablehnung)    │
│ Prüfung mit LLM       LayaAssessmentService ──REST──► Laya (8000)   │
│        │  llm_result.decision                                       │
│ Gateway: green UND keine_manuelle_pruefung → Freigabe               │
│          sonst → User Task „ManualReview“ (Gruppe kyc-reviewers)    │
│ Entscheidung: approve → Freigabe, reject → Ablehnung,               │
│               ungültig/fehlend → Aufgabe wird erneut erstellt       │
│ HistoryListener → InstanceHistoryStore → /api/dashboard/...         │
└─────────────────────────────────────────────────────────────────────┘
```

| Datei | Inhalt |
| --- | --- |
| `src/main/resources/KYC_Pruefprozess.bpmn` | Prozess `kyc_review` |
| `src/main/resources/KYC_RuleCheck.dmn` | Entscheidungstabelle R1–R5 (`TriggeredRules`) und `RuleResult`; R4 = USA-Bezug, R5 = bestätigter Sanktionstreffer (Ablehnung) |
| `src/main/java/de/piu/kyc/LayaAssessmentService.java` | Service-Task: ergänzt `regelpruefung`, ruft Laya, Fehler → manuelle Prüfung |
| `src/main/java/de/piu/kyc/LayaClient.java` | REST-Client (`quarkus.rest-client.laya.url`, Umgebungsvariable `LAYA_URL`) |
| `src/main/java/de/piu/kyc/dashboard/` | Event-Listener, Instanzprotokoll im Speicher, REST-API für das Dashboard |
| `src/main/resources/META-INF/resources/` | Weboberfläche (`index.html`, `app.js`, `app.css`, bpmn-js 18.31.0 lokal unter `vendor/`) |
| `src/test/java/de/piu/kyc/KycProcessTest.java` | 9 Tests aller Pfade mit gemocktem Laya-Dienst, inkl. Knotenprotokoll, R4 und Ablehnung durch R5 |
| `run_demo_cases.py` | Ende-zu-Ende-Lauf der Demo-Fälle K01–K15 über die REST-API |
| `../laya_kyc/laya_service.py` | Laya-Dienst (FastAPI, lädt `../modelle/laya-multilingual-kyc-v2`; anderes Modell per `LAYA_MODEL`) |

Bezeichner im Code sind englisch. Die Feldnamen im Antrag (`kunde`, `screening`, …) und die Laya-Entscheidungen (`keine_manuelle_pruefung`, …) bleiben deutsch: Sie sind Teil des Datensatzschemas, mit dem Laya trainiert wurde.

Abweichungen vom Planungsentwurf, die jBPM verlangt oder die Ausführung absichern:

- Zusammenführende Gateways vor „Freigabe“, „Ablehnung“ und „Manuelle Prüfung“ (jBPM erlaubt an diesen Knoten nur eine eingehende Kante).
- Rückweg „keine gültige Entscheidung“ vom Entscheidungs-Gateway zur manuellen Prüfung (sonst geht die Instanz bei `skip` oder Tippfehlern in einen Fehlerzustand).
- Technische Fehler der LLM-Prüfung führen zu `decision = fehler` und damit zur manuellen Prüfung, wie in der Planung vorgesehen.
- Regel R4 (USA-Bezug) wurde nach dem Training ergänzt. `LayaAssessmentService` gibt nur die trainierten Regeln R1–R3 an Laya weiter; R4 erzwingt die manuelle Prüfung allein über das Regelergebnis.
- Regel R5 (Sanktionsscreening `bestaetigter_treffer`) ist der einzige Ausschlussgrund: `rule_result = reject`, Ablehnung ohne LLM-Prüfung, `llm_result` bleibt leer. Der Status liegt außerhalb des Trainingsschemas; Laya sieht ihn nie. Demo-Fall K15.

## Starten

Alles in einem Schritt: `../start_demo.sh` startet beide Dienste, führt `run_demo_cases.py` aus und lässt die Dienste bis Strg+C laufen (Logs unter `../logs/`; Optionen im Skriptkopf).

Einzeln:

```bash
# 1. Laya-Dienst (Terminal 1)
cd laya_kyc && ../.venv/bin/uvicorn laya_service:app --port 8000

# 2. Prozessdienst (Terminal 2)
cd kyc-prozess
mvn package                                   # Build + Tests
java -jar target/quarkus-app/quarkus-run.jar  # oder: mvn quarkus:dev

# 3. Browser
open http://localhost:8080
```

Optional per Skript: `python3 run_demo_cases.py` startet K01–K15, `--decide approve` schließt die offenen Prüfungen ab.

## Weboberfläche

| Bereich | Funktion |
| --- | --- |
| Antrag prüfen | Vorlage K01–K15 wählen, Felder im Formular oder als JSON ändern, Prozess starten. Ergebnis: DMN-Regeltabelle mit Treffern, Laya-Wahrscheinlichkeiten, Pfad. |
| Manuelle Prüfung | Offene Aufgaben der Gruppe `kyc-reviewers` mit Antrag, Regeln und Laya-Ergebnis; Freigeben oder Ablehnen mit Kommentar (claim + complete). |
| Dashboard | Kennzahlen, Instanzliste (aktualisiert alle 2 s) und BPMN-Diagramm mit bpmn-js: durchlaufene Knoten und Kanten grün, wartender Knoten orange, nicht erreichte blass; Badges mit DMN- und Laya-Ergebnis am jeweiligen Task; Zeitleiste mit Dauer je Schritt. |

Kogito entfernt abgeschlossene Instanzen sofort aus seinem Speicher. Das Dashboard nutzt deshalb ein eigenes Protokoll (`HistoryListener`), das bis zu 1.000 Instanzen im Arbeitsspeicher hält. „Leeren“ löscht es; nach einem Neustart ist es leer.

## REST-Aufrufe

Prozess starten. `application` entspricht `eingabe` der Trainingsdaten; `regelpruefung` berechnet der Prozess selbst und überschreibt einen mitgelieferten Wert.

```bash
curl -X POST localhost:8080/kyc_review -H 'Content-Type: application/json' -d '{"application": {...}}'
```

Die Antwort enthält `id`, `rule_result`, `triggered_rules` und `llm_result` (bei Ablehnung durch R5 `null`, weil Laya nicht aufgerufen wird). Bei automatischer Freigabe und bei Ablehnung durch Regeln ist die Instanz danach beendet (`GET /kyc_review/{id}` → 404; Verlauf weiter unter `/api/dashboard/instances/{id}`).

Manuelle Prüfung (User-Task-API von Kogito 10):

```bash
Q='user=anna&group=kyc-reviewers'
curl "localhost:8080/usertasks/instance?$Q"                                   # offene Aufgaben
curl -X POST "localhost:8080/usertasks/instance/$TASK/transition?$Q" \
     -H 'Content-Type: application/json' -d '{"transitionId":"claim"}'
curl -X POST "localhost:8080/usertasks/instance/$TASK/transition?$Q" \
     -H 'Content-Type: application/json' \
     -d '{"transitionId":"complete","data":{"decision":"approve","comment":"geklärt"}}'
```

Weitere Endpunkte:

| Endpunkt | Inhalt |
| --- | --- |
| `POST /KYC_RuleCheck` mit `{"Application": {...}}` | nur die DMN-Regeln |
| `GET /api/dashboard/instances` | Instanzliste |
| `GET /api/dashboard/instances/{id}` | Verlauf mit Schritten, DMN- und Laya-Ergebnis, manueller Entscheidung |
| `GET /api/dashboard/status` | Erreichbarkeit des Laya-Dienstes |
| `GET /q/swagger-ui` | alle Endpunkte |

## Grenzen

- Prozessinstanzen, Aufgaben und Dashboard-Protokoll liegen nur im Arbeitsspeicher; nach Neustart sind sie weg.
- Keine Authentifizierung: Benutzer und Gruppe kommen als Query-Parameter.
- Laya liefert keine Begründungen oder Feldbelege (siehe `../KYC_Trainingsergebnisse.md`).
