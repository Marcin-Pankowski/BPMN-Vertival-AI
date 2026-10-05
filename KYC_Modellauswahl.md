# Modellauswahl für die KYC-Demo

Stand: 3. Oktober 2026.

Wir wählen **convaiinnovations/laya-multilingual** für die Entscheidung über manuellen Prüfbedarf. Die vorgesehene Hardware ist der vom Nutzer angegebene **Mac M1 mit 64 GB gemeinsamem Arbeitsspeicher**. Das lokale Training wurde mit **PyTorch MPS** durchgeführt (Apple M1 Max, 64 GB): 3 Epochen in 97,6 Minuten bei ca. 9,5 GB Speicher. Durchführung, Ergebnisse und Grenzen stehen in KYC_Trainingsergebnisse.md.

## Modell und Trainingsweg

Laya Multilingual ist ein offenes Entscheidungsmodell mit rund **322 Millionen Parametern** unter **Apache-2.0**. Es verwendet einen mehrsprachigen mmBERT-Encoder und einen Entscheidungsteil. Für die deutschen KYC-Texte laden wir ausdrücklich den mehrsprachigen Checkpoint. [Offizielle Modellkarte](https://huggingface.co/convaiinnovations/laya-multilingual).

Das Projekt veröffentlicht ein [Trainingsskript für Apple Silicon](https://github.com/NandhaKishorM/laya/blob/main/notebooks/laya_finetune_typed_decisions_mps.py) mit MPS, CPU-Fallback, kleinen Batches, Gradientenakkumulation und Gradient Checkpointing. Es verwendet standardmäßig den englischen Checkpoint und einen anderen Beispieldatensatz. Modellpfad, Datenaufbereitung und Trainingsziele müssen für Laya Multilingual und unser KYC-Schema angepasst werden. [Projekt und Trainingsdokumentation](https://github.com/NandhaKishorM/laya#fine-tuning).

64 GB RAM lassen für dieses kompakte Modell einen ersten lokalen Trainingsversuch erwarten. Diese Planungseinschätzung ersetzt keine Messung: Speicherbedarf und Laufzeit hängen von Eingabelängen, Batchgröße und trainierten Parametern ab. Wir beginnen mit kleinen Batches. Ein erster Versuch kann nur den Entscheidungsteil anpassen und den Encoder festhalten; bei zusätzlichem Bedarf beziehen wir den Encoder mit kleiner Lernrate ein. Die Skripte sind dafür anzupassen. LoRA ist für diesen ersten Versuch nicht erforderlich.

Laya Multilingual hat standardmäßig ein Eingabelimit von **1.024 Tokens**; der Encoder unterstützt laut Modellkarte bis zu **8.192 Tokens**. Vor dem Training messen wir die tatsächlichen Längen einschließlich Frage und Antwortoptionen. Wir verwenden eine kompakte, deterministische Darstellung aller fachlich relevanten Eingabefelder. Falls erforderlich erhöhen wir das Limit nach einem Speicher- und Kompatibilitätstest. Relevante Felder und Unterlagen dürfen nicht still abgeschnitten werden. [Kontextgrenzen und Genauigkeit bei langen Dokumenten](https://huggingface.co/convaiinnovations/laya-multilingual).

## Entscheidungen und Begründungen

Die drei Antwortoptionen entsprechen dem vorhandenen Datensatz:

- `keine_manuelle_pruefung`
- `manuelle_pruefung`
- `unklar`

`unklar` führt zur manuellen Prüfung. Regeltrigger R1–R4 erzwingen diese Weiterleitung unabhängig von der Modellentscheidung (R4 USA-Bezug nur im Prozess, nicht im Training). R5 (bestätigter Sanktionstreffer) lehnt im Prozess ab, bevor das Modell aufgerufen wird; eine Ablehnung ist keine Antwortoption des Modells. Nur `eingabe` wird als Fallinhalt verwendet; Metadaten und Sollbewertungen bleiben außerhalb des Modellinputs. Die fiktive Demo-Richtlinie wird als gemeinsame Aufgabenbeschreibung mitgegeben.

Für die überwachte Anpassung wird `sollbewertung.entscheidung` in einen Klassenindex bzw. eine One-Hot-Zielverteilung über diese drei Optionen umgewandelt. Die Zielverteilung beschreibt das Label und keine gemessene fachliche Sicherheit.

Laya erzeugt keine freien Begründungen oder Feldbelege. Dieser Teil der ursprünglichen Demo benötigt eine zusätzliche Komponente: weitere strukturierte Fragen zu Prüfgründen und Belegkandidaten oder einen separaten Textgenerierungsschritt mit einem Sprachmodell. Beides muss anhand der tatsächlichen Eingabe geprüft werden. Die Sollbegründung darf im Betrieb nicht als vermeintliche Modellbegründung angezeigt werden. Modellwahrscheinlichkeiten werden zunächst zur Evaluation protokolliert.

## Training und Vergleich

Wir vergleichen zuerst das unveränderte Basismodell mit der später angepassten Variante: 4.000 Trainingsfälle, 500 Validierungsfälle und 500 Testfälle. Die bestehenden Familien bleiben getrennt. Bewertet werden übersehener Prüfbedarf, unnötige Weiterleitungen und korrekte Feldbelege. Für die 50 Adressfälle gibt es im Test nur fünf Beispiele; zusätzliche unabhängig formulierte Adressfälle und Gegenbeispiele sind für eine belastbare Bewertung nötig.

Die Kalibrierung der Wahrscheinlichkeiten erfolgt ausschließlich auf zurückgehaltenen Validierungsdaten. Der Abschlusstest wird weder zum Training noch zum Einstellen von Schwellenwerten verwendet. Die Modellkarte weist ausdrücklich darauf hin, dass der mehrsprachige Checkpoint ab Werk überkonfident und nicht kalibriert ist. [Modellgrenzen](https://huggingface.co/convaiinnovations/laya-multilingual#limits).

## Betrachtete Alternative

**Qwen3.5-4B mit LLM2Jev** bleibt ein Vergleichskandidat, falls die kompakte Entscheidungsversion auf unseren Daten zu schwach ist oder wir zusätzlich freie Textgenerierung benötigen. Die bevorzugte Variante für den ersten lokalen KYC-Versuch ist Laya Multilingual. [Qwen-Modellkarte](https://huggingface.co/Qwen/Qwen3.5-4B), [LLM2Jev](https://github.com/Yinsongxu/LLM2Jev).
