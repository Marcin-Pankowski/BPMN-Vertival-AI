# Training und Ergebnisse: Laya Multilingual für die KYC-Demo

Stand: 3. Oktober 2026. Alle Daten sind synthetisch; die Sollbewertungen folgen der fiktiven Demo-Richtlinie.

## Kurzfassung

| Modell | Testsplit (500 Fälle): fälschlich automatisch freigegeben | Testsplit: unnötig manuell | Demo K01–K11 richtiger Endpfad |
| --- | ---: | ---: | ---: |
| Laya Multilingual ohne Anpassung | 5 | 246 von 250 | 5 von 11 |
| Laya Multilingual nach Anpassung | 0 | 0 | 10 von 11 |

Das Training verändert das Verhalten deutlich: Ohne Anpassung schickt das Modell fast jeden Fall zur manuellen Prüfung. Nach der Anpassung ist der synthetische Testsplit fehlerfrei. Dieses Ergebnis zeigt vor allem, dass das Modell die Formulierungsvorlagen des Datensatzes gelernt hat. Die anders formulierten Demo-Fälle zeigen die Grenze: K10 wird mit angezeigter Sicherheit 1,00 automatisch freigegeben, obwohl ein Nachweis zur Schenkung fehlt.

## Durchführung

| Punkt | Umsetzung |
| --- | --- |
| Basismodell | `convaiinnovations/laya-multilingual` (mmBERT-Encoder, ~322 Mio. Parameter, Apache-2.0), Paket `laya` 0.3.24 |
| Hardware | Apple M1 Max, 64 GB, PyTorch MPS |
| Daten | `KYC_Trainingsdaten_5000.json`: 4.000 Training, 500 Validierung, 500 Test (SHA-256 `1527a5ea…ac28`) |
| Eingabe | Nur `eingabe`, als `pfad: wert`-Zeilen; Pfade entsprechen den Belegpfaden. Konstante Felder `prozessphase` und `identitaetspruefung` entfallen. Davor steht eine kompakte Fassung der Demo-Richtlinie. |
| Frage | Laya-`choice` mit `keine_manuelle_pruefung`, `manuelle_pruefung`, `unklar` |
| Länge | Trainingsdaten 804–1.017 Tokens bei Limit 1.024; kein Fall wird abgeschnitten (Prüfung bricht sonst ab). K02 und K06 sind mit 1.035 bzw. 1.039 Tokens länger und werden in der Demo mit erhöhtem Limit bewertet, nicht gekürzt. |
| Verfahren | Vollständige Anpassung von Encoder und Entscheidungsteil nach dem offiziellen MPS-Skript: Kreuzentropie plus RL-Term mit `proper_reward`, AdamW (Encoder 2,5e-5, Kopf 1e-4), Cosinus-Schedule, Gradient Checkpointing, effektive Batchgröße 32 |
| Laufzeit | 3 Epochen in 97,6 Minuten, ca. 9,5 GB MPS-Speicher |
| Auswahl | Beste Epoche nach Pfadfehlern auf Validierung: Epoche 2 |
| Kalibrierung | Temperatur auf Validierung angepasst; bei fehlerfreier Validierung bleibt sie bei 1,0. Die Wahrscheinlichkeiten sind daher faktisch **nicht kalibriert**. |
| Test | Einmalig nach Abschluss des Trainings ausgewertet, nicht zur Auswahl verwendet |

Verlauf auf der Validierung:

| Epoche | Trainings-CE | Genauigkeit 3 Klassen | fälschlich freigegeben | unnötig manuell |
| ---: | ---: | ---: | ---: | ---: |
| 0 (Basis) | – | 0,460 | 7 | 245 |
| 1 | 0,448 | 0,988 | 0 | 6 |
| 2 | 0,013 | 1,000 | 0 | 0 |
| 3 | 0,000 | 1,000 | 0 | 0 |

## Ergebnisse im Testsplit

BPMN-Pfad: automatische Freigabe nur bei grünem Regelergebnis und Laya-Entscheidung `keine_manuelle_pruefung`. Unter den 425 regelgrünen Testfällen:

| Modell | korrekt freigegeben | korrekt weitergeleitet | fälschlich freigegeben | unnötig manuell |
| --- | ---: | ---: | ---: | ---: |
| ohne Anpassung | 4 | 170 | 5 | 246 |
| nach Anpassung | 250 | 175 | 0 | 0 |

Ohne Anpassung sagt das Modell in 472 von 500 Testfällen `manuelle_pruefung`. Die angepasste Variante trifft alle 500 Sollentscheidungen einschließlich der 15 `unklar`-Fälle.

## Demo-Fälle K01–K11 (Modell v1)

Die elf Fälle stehen in `laya_kyc/demo_cases.py`. Stammdaten und Freitexte stammen aus KYC_Beispieldaten.md; fehlende Beträge, Kontozwecke und Unterlagenauszüge wurden synthetisch ergänzt. Ihre Formulierungen weichen teilweise von den Trainingsvorlagen ab.

| Fall | Erwartet | ohne Anpassung | nach Anpassung |
| --- | --- | --- | --- |
| K01, K02, K05, K06, K08 | Freigabe | manuell (unnötig) | Freigabe |
| K03, K11 | manuell | manuell | manuell |
| K04, K07, K09 | Regel → manuell | manuell | manuell |
| K10 | unklar → manuell | **Freigabe** | **Freigabe (1,00)** |

K10 ist der wichtigste Befund. In den Trainingsdaten haben alle 200 belegten Schenkungen eine Unterlage und die Formulierung „Schenkung meiner Eltern“; alle 175 offenen Schenkungen haben keine Unterlage und eine Vorlage mit „möchte ich nicht weiter erläutern“. K10 nennt „eine Schenkung meiner Eltern“ ohne Unterlage. Das Modell gibt frei. Ersetzt man in K10 nur einen Freitext durch die Trainingsformulierung, wechselt die Entscheidung:

| K10-Variante | keine | manuell | unklar |
| --- | ---: | ---: | ---: |
| Original | 1,00 | 0,00 | 0,00 |
| Mittelherkunft-Text wie Trainingsvorlage | 0,00 | 1,00 | 0,00 |
| Vermögenstext wie Trainingsvorlage | 0,00 | 0,00 | 1,00 |

Das Modell hat an dieser Stelle die Formulierung gelernt, nicht das Fehlen des Nachweises. Die angezeigte Sicherheit ist dabei keine verlässliche Aussage über die Richtigkeit.

## Empfindlichkeit für die Feldreihenfolge

Bei der Anbindung an Kogito fiel auf, dass das Modell stark auf die Reihenfolge der Eingabezeilen reagiert. Mit denselben Angaben in zufällig gemischter JSON-Feldreihenfolge wechselte die Entscheidung bei 8 der 11 Demo-Fälle in mindestens einer von drei Varianten; K03 wäre dann automatisch freigegeben worden. Alle Trainingsfälle haben dieselbe Feldreihenfolge, das Modell hat also auch die Position der Zeilen gelernt.

Behoben ist das in der Eingabedarstellung (`laya_kyc/kyc_data.py`, `FIELD_ORDER`): Die Zeilen werden unabhängig von der Reihenfolge des eingehenden JSON immer in der Reihenfolge der Trainingsdaten ausgegeben. Für alle 5.000 Trainingsfälle und K01–K11 ist die Darstellung unverändert; die Kennzahlen oben bleiben gültig. Nach der Korrektur ergeben 55 gemischte Varianten der Demo-Fälle keine Abweichung mehr. Ein robusteres Modell würde mit wechselnder Feldreihenfolge trainiert.

## Version 2: entkoppelte Daten (aktives Modell)

Stand: 4. Oktober 2026. Im Workshop eingegebene Fälle zeigten eine zweite Abkürzung: Karl Jones und Tim Uphaus wohnen an der Reeperbahn und wurden trotzdem automatisch freigegeben. Gegenproben belegen die Ursache: Alle 50 Reeperbahn-Fälle des Datensatzes waren Selbstständige mit Rücklagenbestätigung, und kein anderer Fall hatte dieses Dokument. Das Modell v1 hat den Dokumenttyp gelernt, nicht die Wohnadresse.

| Gegenprobe auf Testfällen (je ein Merkmal geändert) | v1 | v2 |
| --- | ---: | ---: |
| Wohnadresse ins Reeperbahn-Umfeld verlegt (Soll: manuell) | 0/250 | 250/250 |
| Nur Arbeitgeber ins Reeperbahn-Umfeld verlegt (Soll: keine) | 185/185 | 185/185 |
| Adressfall an unauffällige Wohnadresse verlegt (Soll: keine) | 0/15 | 15/15 |
| Unveränderte Fälle (Soll wie Datensatz) | 255/255 | 255/255 |

Die unveränderten Testfälle waren bei v1 fehlerfrei. Deshalb fiel die Abkürzung in der normalen Testauswertung nicht auf; erst die Gegenproben zeigen sie.

**Daten:** `KYC_Trainingsdaten_6000.json` ergänzt den Originaldatensatz um 1.000 abgeleitete Varianten (`laya_kyc/augment_dataset.py`). Jede Variante bleibt in Familie und Split ihrer Vorlage; das Original bleibt unverändert.

| Neue Variante | Anzahl | Soll |
| --- | ---: | --- |
| Wohnadresse im Reeperbahn-Umfeld bei sonst unauffälligen Fällen aller Art | 400 | manuell |
| Bisherige Adressfälle an unauffälliger Wohnadresse (auch PLZ 20359 ohne Listenstraße) | 150 | keine |
| Selbstständige mit passender Rücklagenbestätigung | 150 | keine |
| Nur der Arbeitgeber im Reeperbahn-Umfeld | 100 | keine |
| „Selbstständig“, aber Gehaltsersparnisse und Arbeitgeberbestätigung | 200 | manuell |

**Training:** Ein erster Lauf mit dem Verfahren von v1 wurde in Epoche 2 instabil (Trainingsfehler stieg von 0,70 auf über 1,2). Weitertrainiert wurde ab dessen Stand nach Epoche 1, mit reiner Kreuzentropie ohne RL-Term (`--ce-only`) und kleinerer Lernrate (Encoder 1e-5, Kopf 5e-5), 2 Epochen in 66 Minuten. Modell: `modelle/laya-multilingual-kyc-v2`.

| Testsplit | v1: fälschlich freigegeben | v1: unnötig manuell | v2: fälschlich freigegeben | v2: unnötig manuell |
| --- | ---: | ---: | ---: | ---: |
| neuer Datensatz (621 Fälle) | 75 | 29 | 0 | 0 |
| ursprünglicher Datensatz (500 Fälle) | 0 | 0 | 0 | 0 |

Demo-Fälle K01–K14 (Prozess mit Regeln R1–R4): v1 11 von 14, v2 13 von 14. v2 behebt K12 (Tim Uphaus) und K13 (Karl Jones) und gibt K14 (Marcin Pankowski, nur Arbeitgeber an der Reeperbahn) weiterhin frei. **K10 bleibt falsch**: Die Abkürzung „Schenkung meiner Eltern“ wurde nicht entkoppelt.

Nachtrag 5. Oktober 2026: Mit K15 (bestätigter Sanktionstreffer, Regel R5) gibt es 15 Demo-Fälle. K15 wird im Prozess durch R5 abgelehnt, bevor Laya aufgerufen wird; das Modell spielt dafür keine Rolle. Ende-zu-Ende über Kogito mit v2: 14 von 15, falsch ist weiterhin nur K10.

Die Lehre für den Vortrag: Ein fehlerfreier Test auf vorlagenbasierten Daten beweist wenig. Gezielte Gegenproben, die genau ein Merkmal ändern, zeigen, worauf das Modell tatsächlich reagiert. Entkoppelte Trainingsdaten beheben eine Abkürzung, aber nur die, die man gefunden hat.

## Bewertung und Grenzen

- Training hilft bei dieser Aufgabe deutlich: Das Basismodell kennt die fiktive Richtlinie nicht und ist praktisch unbrauchbar für eine automatische Freigabe.
- 100 % im Testsplit beweisen keine Qualität für echte Kundenfälle. Die Splits trennen Familien, aber dieselben Vorlagen kommen in allen Splits vor.
- Ein unabhängig formulierter, fachlich geprüfter Testdatensatz ist vor jeder weitergehenden Aussage nötig. K01–K11 sind dafür ein erster, sehr kleiner Ansatz.
- Mehr Variation in den Trainingsdaten wäre der nächste Schritt, insbesondere belegte und unbelegte Schenkungen mit gleichen Formulierungen und sich nur im Nachweis unterscheidend.
- Eine sinnvolle Kalibrierung benötigt Validierungsdaten, auf denen das Modell Fehler macht.
- Laya liefert keine Begründungen und Feldbelege. Dafür bleibt eine zusätzliche Komponente erforderlich.
- Regeltrigger R1–R4 erzwingen unabhängig vom Modell die manuelle Prüfung; das Modell kann sie nicht aufheben. R4 (USA-Bezug) wurde nach dem Training eingeführt; das Modell selbst bewertet US-Fälle weiterhin nach der ursprünglichen Richtlinie.
- R5 (bestätigter Sanktionstreffer) lehnt ab, bevor das Modell gefragt wird. Den Screening-Status „bestätigter Treffer“ kennt das Modell aus dem Training nicht; es erhält solche Fälle im Prozess nie.

## Dateien und Befehle

| Pfad | Inhalt |
| --- | --- |
| `modelle/laya-multilingual-base/` | Basismodell ohne Anpassung |
| `modelle/laya-multilingual-kyc/` | Modell v1; Trainingsangaben in `rl_agent_config.json` unter `kyc_training` |
| `modelle/laya-multilingual-kyc-v2/` | Modell v2 (aktiv im Laya-Dienst), trainiert auf `KYC_Trainingsdaten_6000.json` |
| `laya_kyc/augment_dataset.py` | Erzeugt `KYC_Trainingsdaten_6000.json` und die zugehörige Validierung |
| `laya_kyc/kyc_counterfactuals.py` | Gegenproben: je ein Merkmal geändert |
| `modelle/laya-multilingual-kyc_arbeit/training.log` | Vollständiges Trainingsprotokoll |
| `laya_kyc/kyc_data.py` | Eingabedarstellung, Richtlinientext, Frage, Abschneideprüfung |
| `laya_kyc/kyc_train.py` | Training auf MPS |
| `laya_kyc/kyc_evaluate.py` | Auswertung je Split, mit Gegenprobe über die Laya-API |
| `laya_kyc/kyc_demo.py`, `laya_kyc/demo_cases.py` | Demo ohne Kogito, Fälle K01–K15 (K15: Ablehnung durch R5) |
| `laya_kyc/laya_service.py` | REST-Dienst für den Prozess (`POST /assessment`) |
| `laya_kyc/ergebnisse/` | Kennzahlen und Einzelvorhersagen je Modell und Split |

```bash
cd laya_kyc
../.venv/bin/python kyc_demo.py --compare               # Demo: Basis und angepasst
../.venv/bin/python kyc_demo.py --case K11 --show-input
../.venv/bin/python kyc_evaluate.py --model ../modelle/laya-multilingual-kyc-v2 --split test --name v2 --data ../KYC_Trainingsdaten_6000.json
../.venv/bin/python kyc_counterfactuals.py --model ../modelle/laya-multilingual-kyc-v2 --name v2
../.venv/bin/python kyc_train.py --epochs 3               # Training wiederholen (ca. 1,5–2 Stunden)
```
