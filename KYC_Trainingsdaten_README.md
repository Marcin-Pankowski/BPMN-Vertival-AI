# Verwendung der synthetischen KYC-Trainingsdaten

Die Datei KYC_Trainingsdaten_5000.json enthält genau 5.000 unterschiedliche synthetische Kundenprofile zur Prüfung nach erfolgreicher Identifizierung und vor Kontoanlage. Sie dient dem geplanten KYC-Modellbeispiel. Grundlage sind Antragsdaten, Selbstauskünfte, synthetische Screening-Ergebnisse und gegebenenfalls eingereichte Unterlagenauszüge. Als Entscheidungsmodell wurde Laya Multilingual für ein lokales Training auf einem Mac M1 mit 64 GB RAM ausgewählt. Trainingsverfahren und Grenzen stehen in KYC_Modellauswahl.md. Das Training wurde am 3. Oktober 2026 ausgeführt; Ergebnisse stehen in KYC_Trainingsergebnisse.md.

## Dateien

- KYC_Trainingsdaten_6000.json: Version 1.1 mit 1.000 zusätzlichen, abgeleiteten Varianten gegen Scheinzusammenhänge (Adresse vs. Dokumenttyp, Arbeitgeberadresse, Widerspruch selbstständig/Gehalt); erzeugt mit `laya_kyc/augment_dataset.py`, Prüfergebnis in KYC_Trainingsdaten_6000_Validierung.json. Grundlage für Modell v2, siehe KYC_Trainingsergebnisse.md.

- KYC_Trainingsdaten_5000.json: vollständiger Datensatz als UTF-8-JSON mit dem Array `kunden`.
- KYC_Trainingsdaten.schema.json: JSON Schema für den Datensatz und seine Eingabe- und Zielfelder.
- KYC_Trainingsdaten_Validierung.json: Prüfergebnisse, Verteilungen, Dateigröße und SHA-256-Prüfsumme.

## Struktur eines Kundenfalls

Jedes Element in `kunden` enthält:

| Feld | Zweck | Beim Training verwenden |
| --- | --- | --- |
| `kunden_id` | Eindeutige synthetische Kennung | Für Zuordnung und Auswertung |
| `metadaten` | Split, Ausgangsfamilie, Variante und Szenario | Für Auswahl und Auswertung |
| `eingabe` | Kundenangaben, Antrag, Unterlagen und Regelprüfung | Als Modellinput |
| `sollbewertung` | Manueller Prüfbedarf, Entscheidung, Begründung, Belege und Fragen | Als Trainingsziel |

**Nur `eingabe` wird dem Modell als Eingabe gegeben.** Der Szenarioname und die Sollbewertung verraten die Zielentscheidung und gehören ebenso wie Split und Familienkennung nicht in den Modellinput.

Die Sollbewertung hat zwei Entscheidungsebenen: `manuelle_pruefung_erforderlich` ist ein Boolean. `entscheidung` ist `manuelle_pruefung`, `keine_manuelle_pruefung` oder `unklar`. Bei `unklar` ist die Weiterleitung zur manuellen Prüfung erforderlich und der Boolean deshalb `true`. Belege verweisen mit Feldpfaden und den zugehörigen Werten auf die konkrete Eingabe. Das Modell wird auf den manuellen Prüfbedarf trainiert; eine endgültige Ablehnung ist keine Zielklasse.

## Enthaltene Kundenfelder

- Erfolgreich abgeschlossene Identitätsprüfung und aktueller Prozesszeitpunkt vor Kontoanlage.
- Name, Geburtsdatum und Staatsangehörigkeiten.
- Kundenadresse: PLZ, Straße, Hausnummer, Ort und Land.
- Kunde selbst wirtschaftlich berechtigt: ausschließlich `Ja` oder `Nein`.
- Beruf, Beschäftigungsstatus und vom Kunden angegebenes monatliches Nettoeinkommen.
- Optionaler Arbeitgeber: Name, Straße, PLZ, Hausnummer, Ort und Land. Bei Selbstständigkeit und Ruhestand steht hier `null`.
- Entstehung des Gesamtvermögens als Freitext sowie getrennte Angaben zur Herkunft der vorgesehenen Ersteinzahlung.
- US-Steuerpflicht, FATCA-US-Person-Status und steuerliche Ansässigkeit laut Selbstauskunft.
- Auslandswohnsitz als `Ja`/`Nein` und Liste zusätzlicher Adressen.
- Beantragter Kontotyp, Kontozweck und Freitext zur geplanten Nutzung.
- Synthetische PEP-/Screening-Ergebnisse, gegebenenfalls eingereichte Unterlagenauszüge und berechnetes Ergebnis der drei Demo-Regeln.

PLZ und Hausnummern sind Strings. Führende Nullen, internationale Postleitzahlen und Hausnummernzusätze bleiben erhalten. Widerspruchsfälle können absichtlich Unterschiede zwischen strukturierten Antragsfeldern und einer Erklärung oder Unterlage enthalten; diese Unterschiede sind Teil des zu bewertenden Sachverhalts.

## Aufteilung

| Split | Kunden | Manuell erforderlich | Kein manueller Bedarf | Durch Regeln markiert |
| --- | ---: | ---: | ---: | ---: |
| train | 4000 | 2000 | 2000 | 860 |
| validation | 500 | 250 | 250 | 65 |
| test | 500 | 250 | 250 | 75 |

Die 1.000 Ausgangsfamilien enthalten je fünf individuell ausgestaltete Kundenfälle. Alle Varianten einer Familie liegen im selben Split. Auch jede Teilmenge hat bewusst gleich viele Fälle mit und ohne manuellen Prüfbedarf. Diese 50/50-Verteilung beschreibt die Demo, nicht die Häufigkeit solcher Fälle bei einer Bank.

Es gibt 1.000 Kunden mit Regeltrigger. Unter den 4.000 regelgrünen Kunden benötigen 1.500 laut Demo-Richtlinie eine manuelle Prüfung; 2.500 benötigen keine. Für den eigentlichen LLM-Zusatznutzen ist insbesondere die Qualität auf den regelgrünen Kunden aus `test` auszuwerten. Das Bestehen der drei Regeln allein wäre für diese Fälle kein ausreichender Klassifikator.

## Falltypen

Drei Regeltrigger werden beibehalten: R1 Kunde selbst wirtschaftlich berechtigt `Nein`; R2 PEP `Ja`; R3 möglicher Screening-Treffer ungeklärt. Jeder dieser Trigger bedeutet manuelle Prüfung nach der fiktiven Demo-Richtlinie. Die später im Prozess ergänzten Regeln R4 (USA-Bezug, manuelle Prüfung) und R5 (bestätigter Sanktionstreffer, Ablehnung) sind nicht Teil des Datensatzes; der Screening-Status `bestaetigter_treffer` kommt im Schema nicht vor.

Regelgrüne Fälle mit zusätzlichem Prüfbedarf enthalten unter anderem den Widerspruch zwischen beantragtem Privatkonto und geplanter geschäftlicher Nutzung, Widersprüche zur Mittelherkunft oder zum Vermögensaufbau, unzureichend erklärte Schenkungen, widersprüchliche Arbeitgeberangaben sowie widersprüchliche Steuer- oder Auslandswohnsitzangaben.

Die 500 Fälle `privatkonto_geschaeftlich_geplant` entsprechen dem Motiv von K11: Der Kunde hat sich identifiziert, beantragt ein Privatkonto und erklärt, dass er damit künftig Auftraggeberzahlungen und Kosten für Kundenprojekte abwickeln will. Grundlage ist der Antragstext.

Unauffällige Gegenbeispiele enthalten ausdrücklich private Kontonutzung bei Selbstständigkeit, konsistent erklärte US-Status- und Auslandswohnsitzangaben, belegte Mittelherkunft, erklärte Arbeitgeberwechsel und schlüssig angegebene private Darlehen. Diese Falltypen verhindern, dass die Demo-Richtlinie solche Merkmale pauschal als manuellen Prüfbedarf definiert.

Die 50 Fälle `adresse_reeperbahn_umfeld_pruefbedarf` haben synthetische Wohnadressen an der Reeperbahn oder in ihrem unmittelbaren Umfeld. Alle übrigen Angaben und Nachweise sind konsistent, R1–R3 bleiben grün. Allein die Lage der Adresse führt gemäß der fiktiven Demo-Richtlinie zur manuellen Adressklärung. Die Hausnummernzuordnungen sind erfunden; es handelt sich nicht um Angaben über reale Bewohner.

| Straße | PLZ | Fälle | train | validation | test |
| --- | --- | ---: | ---: | ---: | ---: |
| Reeperbahn | 20359 | 20 | 16 | 2 | 2 |
| Große Freiheit | 22767 | 10 | 8 | 1 | 1 |
| Davidstraße | 20359 | 10 | 8 | 1 | 1 |
| Spielbudenplatz | 20359 | 10 | 8 | 1 | 1 |

Jede der zehn Familien umfasst zwei direkte Reeperbahn-Adressen und je eine Adresse der drei umliegenden Straßen. Die Familien bleiben vollständig in ihrem bisherigen Split. „Nähe“ beschreibt die Lage der Straßen; Hauskoordinaten oder Meterentfernungen wurden nicht berechnet. Die PLZ allein ist kein Prüfgrund.

Die Straßenlage ist anhand von [Hamburg.de: Große Freiheit](https://www.hamburg.de/tourismus/sehenswuerdigkeiten/grosse-freiheit-341258), [Hamburg.de: Davidwache](https://www.hamburg.de/tourismus/sehenswuerdigkeiten/davidwache-hamburg-341256) und [Hamburg.de: Spielbudenplatz](https://www.hamburg.de/oeffentliche-plaetze/4260704/spielbudenplatz.html) geprüft. Die PLZ stützen sich auf [Große Freiheit 36](https://docksfreiheit36.de/grosse-freiheit/), [Davidstraße](https://www.hamburg.de/branchenbuch/hamburg/st-pauli/10247659/n0/) und [Spielbudenplatz](https://www.hamburg.de/freizeit/strassenfeste/spielbudenfestival-338520). Diese Quellen belegen die Straßen und Postleitzahlen, nicht die erfundenen Kundenadressen oder den manuellen Prüfbedarf.

Diese Fälle ersetzen 50 bisherige Varianten mit widersprüchlicher Mittelherkunft. Deren Unterlagen wurden passend zur angegebenen Mittelherkunft neu formuliert. Damit bleiben genau 5.000 Kunden, die vorhandenen Splits und die Verteilung von 2.500 Fällen mit und 2.500 ohne manuellen Prüfbedarf erhalten. Der frühere Prüfgrund wurde durch den alleinigen Adressprüfbedarf ersetzt.

## Geplanter Trainingsablauf mit Laya Multilingual

1. `kunden` laden und die Datensätze über `metadaten.split` auswählen.
2. Für Training nur `train` verwenden. Die Anweisung lautet sinngemäß: „Prüfe anhand dieser KYC-Antragsdaten und der Demo-Richtlinie, ob eine manuelle Prüfung erforderlich ist. Begründe das Ergebnis mit Belegen aus der Eingabe.“
3. `eingabe` kompakt als Kundeninhalt darstellen und die tatsächliche Tokenlänge einschließlich Frage und Optionen prüfen. Für Laya wird `sollbewertung.entscheidung` als Zielklasse über die drei Antwortoptionen verwendet. Begründungen, Belege und offene Fragen bleiben zusätzliche Referenzdaten; Laya erzeugt selbst keine freien Texte. Die Umsetzung berücksichtigt die Kontextgrenze des mehrsprachigen Checkpoints und darf keine relevanten Angaben still abschneiden.
4. Mit `validation` Modell- und Prompt-Einstellungen auswählen. `test` erst für den abschließenden Vergleich nutzen.
5. Dasselbe Modell vor und nach Anpassung vergleichen. Fälschlich automatisch freigegebene Fälle, unnötige manuelle Prüfungen und belegte Begründungen getrennt bewerten; zusätzlich die regelgrüne Teilmenge auswerten.

## Qualität und Grenzen

Die Sollbewertungen wurden aus den konstruierten Sachverhalten und der fiktiven Demo-Richtlinie abgeleitet. Sie stammen nicht aus fachlich geprüften realen Kundenakten. Das Schema bildet keinen vollständigen regulatorischen KYC- oder Steuerprüfprozess ab.

Die Freitexte und Unterlagen sind aus Formulierungsvorlagen erzeugt. Die Profile sind unterschiedlich und die Ausgangsfamilien getrennt, aber dieselben Motive und zum Teil dieselben Formulierungsstrukturen kommen in allen Splits vor. Deshalb zeigt ein gutes Testergebnis zunächst, wie gut das Modell diese konstruierten Fälle lernt. Vor einer Aussage zur Leistung auf echten Kundenfällen wären unabhängig formulierte, fachlich geprüfte Testfälle erforderlich.

Geprüft wurden die gespeicherte JSON-Datei und alle im Schema verwendeten Strukturbedingungen: genau 5.000 Kunden, eindeutige IDs und Eingaben, Pflichtfelder und Datentypen, Erfolgsstatus der Identifizierung, Adressen, Arbeitgeber-Nullwerte, die drei Regeltrigger, Konsistenz von Zielklasse und Boolean, die Belegpfade sowie die vollständige Trennung der Familien zwischen den Splits.

Die JSON-Datei enthält keine zufällig erfundenen Konfidenzwerte. Unsichere Sachverhalte werden durch die Zielentscheidung `unklar` mit manueller Weiterleitung dargestellt.

SHA-256 der Datendatei: `1527a5ead2ec54970e16abaccddd2207791e36184b4be9a70208d384d489ac28`.
