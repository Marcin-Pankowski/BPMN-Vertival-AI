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

```bash
git clone https://github.com/Marcin-Pankowski/BPMN-Vertival-AI.git
cd BPMN-Vertival-AI
./start_demo.sh
```

Beim ersten Start lädt `start_demo.sh` das Demo-Modell v2 als ZIP aus dem Release [modelle](https://github.com/Marcin-Pankowski/BPMN-Vertival-AI/releases/tag/modelle) (ca. 600 MB), legt die Python-Umgebung `.venv/` aus `requirements.txt` an (lädt PyTorch, einige Minuten) und baut den Prozessdienst mit Maven (Java 21). Details: [Quickstart.md](Quickstart.md).

## Modelle

Die Modelle sind zu groß für Git und liegen als ZIP im Release [modelle](https://github.com/Marcin-Pankowski/BPMN-Vertival-AI/releases/tag/modelle). Im Projektordner entpacken (`unzip <datei>.zip`), sie landen unter `modelle/`.

| ZIP | Inhalt | Nötig für |
| --- | --- | --- |
| `laya-multilingual-kyc-v2.zip` | Modell v2, aktiv im Laya-Dienst | Demo (lädt `start_demo.sh` automatisch) |
| `laya-multilingual-kyc.zip` | Modell v1 | Vergleiche und Gegenproben |
| `laya-multilingual-base.zip` | Basismodell `convaiinnovations/laya-multilingual` (Apache-2.0) | Training, Vergleich ohne Anpassung |

Die Trainingsprotokolle liegen im Repository unter `modelle/*_arbeit/`. Den Zwischenstand nach Epoche 1, ab dem v2 weitertrainiert wurde, enthält das Release nicht.

Nicht im Repository sind außerdem `.venv/` und `kyc-prozess/target/`; beides erzeugt `start_demo.sh` selbst.
