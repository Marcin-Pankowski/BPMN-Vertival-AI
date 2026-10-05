# Vertical AI: KYC-Prüfung mit BPMN, Regeln und einem lokal trainierten Entscheidungsmodell

Vortrag und Demo: Ein KYC-Prüfprozess bei der Kontoeröffnung kombiniert DMN-Regeln, das lokal trainierte Entscheidungsmodell Laya Multilingual und die manuelle Prüfung als User Task. Der Prozess läuft als Kogito-Microservice. Alle Daten sind vollständig synthetisch, die Richtlinie ist fiktiv.

## Inhalt

| Pfad | Inhalt |
| --- | --- |
| [Quickstart.md](Quickstart.md) | Demo starten und vorführen (`start_demo.sh`) |
| [KYC_Demo_Planung.md](KYC_Demo_Planung.md) | Prozess, Regeln R1–R5, Demo-Fälle, Ablauf des Vortrags |
| [KYC_Beispieldaten.md](KYC_Beispieldaten.md) | Demo-Kunden K01–K15 |
| [KYC_Trainingsergebnisse.md](KYC_Trainingsergebnisse.md) | Training, Ergebnisse, gefundene Abkürzungen des Modells |
| [KYC_Modellauswahl.md](KYC_Modellauswahl.md) | Warum Laya Multilingual |
| [KYC_Trainingsdaten_README.md](KYC_Trainingsdaten_README.md) | Synthetische Trainingsdaten (5.000 bzw. 6.000 Fälle) |
| `KYC_Pruefprozess.bpmn` | Fachlicher Prozessentwurf |
| `laya_kyc/` | Training, Auswertung, Gegenproben, Laya-REST-Dienst |
| `kyc-prozess/` | Kogito-Prozessdienst mit Weboberfläche, siehe [kyc-prozess/README.md](kyc-prozess/README.md) |
| `praesentation/` | Präsentation; `build_deck.js` erzeugt `Vertical_AI_KYC.pptx` |

## Nicht im Repository

- **Modelle** (`modelle/`, je ca. 650 MB): Das Basismodell `convaiinnovations/laya-multilingual` von Hugging Face nach `modelle/laya-multilingual-base/` laden. Das angepasste Modell v2 entsteht mit `laya_kyc/kyc_train.py` auf `KYC_Trainingsdaten_6000.json` (siehe KYC_Trainingsergebnisse.md). Die Trainingsprotokolle liegen unter `modelle/*_arbeit/`.
- **Python-Umgebung** (`.venv/`): Python 3.12 mit laya 0.3.24, torch 2.14.1, transformers 5.18.0, fastapi 0.142.2, uvicorn 0.54.0, numpy und jsonschema.
- **Build-Ausgaben** (`kyc-prozess/target/`): `start_demo.sh` baut den Prozessdienst bei Bedarf mit Maven (Java 21).
