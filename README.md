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

## Klonen und starten

Das Demo-Modell v2 (`modelle/laya-multilingual-kyc-v2/`, 678 MB) liegt per [Git LFS](https://git-lfs.com) im Repository. Git LFS muss vor dem Klonen installiert sein (`brew install git-lfs && git lfs install`), sonst kommen nur Platzhalter an; nachträglich hilft `git lfs pull`.

```bash
git clone https://github.com/Marcin-Pankowski/BPMN-Vertival-AI.git
cd BPMN-Vertival-AI
./start_demo.sh
```

Beim ersten Start legt `start_demo.sh` die Python-Umgebung `.venv/` aus `requirements.txt` an (lädt PyTorch, einige Minuten) und baut den Prozessdienst mit Maven (Java 21). Details: [Quickstart.md](Quickstart.md).

## Nicht im Repository

- **Basismodell und Modell v1** (je ca. 650 MB): nur für Training und Vergleiche nötig, nicht für die Demo. Das Basismodell `convaiinnovations/laya-multilingual` von Hugging Face nach `modelle/laya-multilingual-base/` laden; v1 entsteht mit `laya_kyc/kyc_train.py` auf `KYC_Trainingsdaten_5000.json` (siehe KYC_Trainingsergebnisse.md). Die Trainingsprotokolle liegen unter `modelle/*_arbeit/`.
- **Python-Umgebung** (`.venv/`) und **Build-Ausgaben** (`kyc-prozess/target/`): erzeugt `start_demo.sh` selbst.
