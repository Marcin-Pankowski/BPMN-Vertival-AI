# Planung: KYC mit Regeln, LLM und manueller Prüfung

Stand: 3. Oktober 2026, aktualisiert am 5. Oktober 2026 (Regel R5, Prüffälle K12–K15). Ziel: 30 Minuten Vortrag und Demo, anschließend 15 Minuten Fragerunde.

Die Implementierung wurde freigegeben; Training, Auswertung und Demo-Skripte liegen in `laya_kyc/`, die Ergebnisse in KYC_Trainingsergebnisse.md. Der Prozess läuft als Kogito-10.2.0-Microservice in `kyc-prozess/` (Regeln als DMN, Laya als REST-Dienst, manuelle Prüfung als User Task). Die BPMN-Datei ist ein fachlicher Prozessentwurf. Die nachfolgenden Regeln und Fallbewertungen beschreiben eine fiktive Bankrichtlinie für die Demo; sie sind keine vollständige Abbildung regulatorischer Anforderungen.

## 1. Umfang und Prozess

Ausgangspunkt sind synthetische Privatkunden beim Onboarding einer deutschen Bank nach abgeschlossener, erfolgreicher Identitätsprüfung. Nur Daten solcher Kunden werden für Demo, Training und Evaluation verwendet. Die Identitätsprüfung findet vor dem BPMN-Start statt und ist keine Entscheidungsregel dieses Prozesses. Firmenkunden und Beteiligungsstrukturen bleiben eine mögliche Erweiterung.

Alle Fälle werden unmittelbar nach erfolgreicher Identitätsprüfung und vor der Kontoanlage bewertet. Grundlage sind Kundenangaben aus dem Antrag, Screening-Ergebnisse und gegebenenfalls bereits eingereichte Unterlagen. „Freigabe“ bedeutet Freigabe der beantragten Kontoanlage. K11 zeigt einen Widerspruch zwischen beantragtem Privatkonto und einem Kundenfreitext zur geplanten geschäftlichen Nutzung.

1. Der Prozess beginnt mit KYC-Daten eines bereits erfolgreich identifizierten Kunden; anschließend erfolgt die Prüfung nach Regeln.
2. Eindeutige regelbasierte Ablehnung führt zum Endpunkt Ablehnung.
3. Ein grünes Regelergebnis oder ein Regelergebnis mit Prüfbedarf führt zur Prüfung mit LLM. Auch grüne Fälle werden durch das LLM geprüft.
4. Das LLM bewertet anhand der Angaben und Nachweise, ob eine manuelle Prüfung erforderlich ist.
5. Eine automatische Freigabe setzt ein grünes Regelergebnis und ein eindeutiges LLM-Ergebnis „keine manuelle Prüfung erforderlich“ voraus.
6. Bei manuellem Klärungsbedarf oder einem unklaren LLM-Ergebnis folgt eine manuelle Prüfung. Ein durch Regeln festgestellter Prüfbedarf bleibt ebenfalls manuell zu bearbeiten.
7. Die manuelle Prüfung endet nach der Klärung mit Freigabe oder Ablehnung.

Technische Fehler und ungültige Modellausgaben führen zur manuellen Prüfung. Im BPMN-Entwurf im Projektwurzelverzeichnis sind diese Fehlerpfade nicht eigens modelliert; der Kogito-Dienst setzt sie um (`decision = fehler` → manuelle Prüfung, siehe `kyc-prozess/README.md`).

## 2. Vorgeschlagene Regeln der Demo

| ID | Prüfung | Ergebnis bei Regeltrigger |
| --- | --- | --- |
| R1 | Gibt der Kunde an, selbst nicht wirtschaftlich berechtigt zu sein (Antwort „Nein“)? | Prüfbedarf; manuelle Fachprüfung |
| R2 | Ist der PEP-Status bestätigt? | Prüfbedarf; manuelle Fachprüfung erforderlich |
| R3 | Liegt ein möglicher, noch ungeklärter Screening-Treffer vor? | Prüfbedarf; möglichen Treffer manuell prüfen |
| R4 | Besteht ein USA-Bezug (US-Steuerpflicht oder FATCA-US-Person laut Selbstauskunft, US-Staatsangehörigkeit, steuerliche Ansässigkeit USA oder Wohn-/Auslandsadresse in den USA)? | Prüfbedarf; manuelle Prüfung des US-Bezugs |
| R5 | Liegt ein bestätigter Sanktionstreffer vor? | Ablehnung; keine LLM-Prüfung |

Das Feld „Kunde selbst wirtschaftlich berechtigt“ enthält die Kundenangabe „Ja“ oder „Nein“. Eine dritte Ausprägung ist nicht vorgesehen. „Nein“ löst nach unserer fiktiven Demo-Richtlinie R1 aus; das ist keine automatische Ablehnung.

„Grün“ bedeutet: Keine Demo-Regel verlangt eine manuelle Prüfung. „Prüfbedarf“ bedeutet: Mindestens eine Demo-Regel verlangt eine manuelle Prüfung. „Ablehnung“ bedeutet: Ein bestätigter Ausschlussgrund liegt vor.

R4 wurde nach dem Training ergänzt und wird nur im Prozess (DMN) ausgewertet. Laya kennt aus dem Training nur R1–R3 und erhält im Regelergebnis weiterhin nur diese; die Trainingsdaten behandeln einen konsistent angegebenen US-Status noch als unauffällig. Da jeder Regeltrigger die manuelle Prüfung erzwingt, ändert das Modellurteil daran nichts.

R1–R4 markieren ausschließlich manuellen Prüfbedarf. Einziger Ausschlussgrund ist R5, ein bestätigter Sanktionstreffer: Der Antrag endet direkt in der Ablehnung, Laya wird nicht aufgerufen. Laya kennt diesen Screening-Status aus dem Training nicht; das ist unkritisch, weil der Fall das Modell nie erreicht. Ein bestätigter PEP-Status ist hier ein Trigger für Fachprüfung, keine automatische Ablehnung. Den Ablehnungspfad zeigt der zusätzliche Prüffall K15 (siehe unten).

Einkommensgrenzen oder feste Betragsgrenzen legen wir zunächst nicht fest. Der interessante LLM-Anteil ist die inhaltliche Übereinstimmung von Kundenerklärung, wirtschaftlichem Profil und Nachweisen sowie zwischen angegebenem Kontozweck und erklärter geplanter Nutzung.

## 3. Aufgabe des LLM

Das LLM erhält den strukturierten KYC-Fall, das Regelergebnis einschließlich offener Befunde sowie Textauszüge aus synthetischen Nachweisen. Bei K11 erhält es den beantragten Kontotyp, den ausgewählten privaten Kontozweck und einen Freitext zur geplanten Nutzung. Es soll beantworten:

> Sind die Angaben und Nachweise ausreichend konsistent und nachvollziehbar, oder muss ein Mensch den Fall prüfen?

Die Antwort enthält:

- Entscheidung: manuelle Prüfung erforderlich / nicht erforderlich / unklar.
- Kurze Begründung anhand des konkreten Falls.
- Verweise auf die verwendeten Datenfelder und Dokumentstellen.
- Offene Fragen oder fehlende Nachweise.

Das Modell entscheidet nicht selbst über eine Ablehnung. Es darf offene Regelbefunde nicht durch eine plausible Erklärung als erledigt behandeln. Eine selbst angegebene numerische Modellkonfidenz verwenden wir zunächst nicht als Entscheidungsgrundlage.

## 4. Synthetische Testfälle

Alle Beträge und Sachverhalte sind fiktive Beispiele. Die Sollwerte beruhen auf der für die Demo festgelegten Richtlinie. Bei allen elf Kunden ist die Identitätsprüfung bereits erfolgreich abgeschlossen. Die Kundenkennungen entsprechen der Tabelle in KYC_Beispieldaten.md.

| Fall | Sachverhalt | Regelergebnis | Erwarteter Pfad |
| --- | --- | --- | --- |
| K01 | Gehaltskonto; Angaben, Gehaltsnachweis und erwartete Eingänge stimmen überein | Grün | LLM → Freigabe |
| K02 | Vorgesehene Ersteinzahlung von 18.000 EUR aus Fahrzeugverkauf; Erklärung, Vertrag und Betrag passen zusammen | Grün | LLM → Freigabe |
| K03 | Kundin erklärt Einkommen aus selbstständiger Tätigkeit; vorgelegtes Dokument beschreibt ein Darlehen eines Dritten | Grün | LLM → manuelle Prüfung |
| K04 | Identität erfolgreich geprüft; Kunde gibt an, selbst nicht wirtschaftlich berechtigt zu sein (Antwort „Nein“) | Prüfbedarf (R1) | LLM → manuelle Prüfung; keine automatische Freigabe |
| K05 | Erbschaft erklärt eine vorgesehene hohe Ersteinzahlung; synthetischer Nachweis passt zu Person und Betrag | Grün | LLM → Freigabe |
| K06 | Gehalt und Ersparnisse; Angaben und Nachweise passen zusammen; deutsche und US-Staatsangehörigkeit, US-Status angegeben | Prüfbedarf (R4) | LLM → manuelle Prüfung |
| K07 | PEP-Status bestätigt; Identität erfolgreich geprüft | Prüfbedarf (R2) | LLM → manuelle Prüfung |
| K08 | Gehaltskonto einer Pflegefachkraft mit konsistenten Angaben | Grün | LLM → Freigabe |
| K09 | Screening liefert einen möglichen Namensgleichklang, dessen Zuordnung noch offen ist | Prüfbedarf (R3) | LLM → manuelle Prüfung |
| K10 | Gehalt und Schenkung; Regeln grün, aber wirtschaftliche Dokumentauszüge reichen zur Bewertung nicht aus | Grün | LLM unklar → manuelle Prüfung |
| K11 | Privatkonto beantragt; Kunde plant laut Freitext Auftraggeberhonorare und Kosten für Kundenprojekte über dieses Konto abzuwickeln | Grün | LLM → manuelle Prüfung |

Die Regeln filtern genau K04, K06, K07 und K09 zur manuellen Prüfung heraus. Die sieben grünen Kunden werden ebenfalls mit dem LLM geprüft. K03, K10 und K11 demonstrieren zusätzlichen Klärungsbedarf, den die Regeln nicht abdecken.

K11 führt zur Prüfung der Abweichung zwischen angegebenem privatem Kontozweck und geplanter geschäftlicher Nutzung. Die Entscheidung über die beantragte Kontoanlage und eine passende Kontovariante trifft nach der Klärung die manuelle Prüfung.

Zusätzliche Prüffälle in `laya_kyc/demo_cases.json` (Details in KYC_Beispieldaten.md):

| Fall | Sachverhalt | Regelergebnis | Erwarteter Pfad |
| --- | --- | --- | --- |
| K12 | Variante von K01: Wohnadresse Reeperbahn; selbstständig, aber Gehaltsersparnisse und Arbeitgeberbestätigung | Grün | LLM → manuelle Prüfung |
| K13 | Variante von K01: Wohnadresse Reeperbahn, sonst konsistent | Grün | LLM → manuelle Prüfung |
| K14 | Variante von K01: nur der Arbeitgeber sitzt an der Reeperbahn | Grün | LLM → Freigabe |
| K15 | Angestellter Ingenieur mit konsistenten Angaben, aber bestätigtem Sanktionstreffer | Ablehnung (R5) | Ablehnung durch Regeln, ohne LLM |

K12–K14 wurden im Workshop eingegeben und zeigten die Adress-Abkürzung des ersten Modells. K15 ist der einzige Fall, der durch Regeln abgelehnt wird.

Eine Weiterleitung zur manuellen Prüfung ist kein Geldwäscheverdacht und keine Ablehnung. Die endgültige manuelle Entscheidung hängt von der anschließenden Klärung ab.

## 5. Daten für Training und Evaluation

Ein Fall besteht aus Kundenprofil, Kontotyp, angegebenem Kontozweck, erwarteter Kontonutzung, Mittelherkunft, Nachweisen und Regelergebnis. Die geplante Nutzung wird als Kundenfreitext vor der Kontoanlage erhoben. Voraussetzung für die Aufnahme eines Falls ist eine abgeschlossene, erfolgreiche Identitätsprüfung. Ihr Status wird als Metadatum der Datenherkunft dokumentiert; er ist in diesem Datensatz konstant und kein Lernmerkmal zur Entscheidung über manuelle Prüfung. Die getrennte Sollbewertung enthält den Bedarf einer manuellen Prüfung, eine fachliche Begründung und Belegstellen. Diese Sollbewertung gehört nicht in die Modelleingabe.

### Zusätzliche Datenfelder

Für alle elf Fälle werden ergänzt:

| Feld | Datentyp | Inhalt |
| --- | --- | --- |
| Entstehung des Gesamtvermögens | Freitext | Synthetische Kundenangabe zum Vermögensaufbau über die Zeit; getrennt von der Mittelherkunft |
| Kundenadresse | Objekt | PLZ, Straße und Hausnummer jeweils als Text; ergänzt um Ort und Land |
| Beschäftigungsstatus | Auswahlwert | Angestellt, selbstständig, Ruhestand oder öffentliche Funktion |
| Arbeitgeber | Optionales Objekt | Name, Straße, PLZ und Hausnummer jeweils als Text; ergänzt um Ort und Land |
| US-Steuerpflicht laut Selbstauskunft | Ja/Nein | Kundenangabe; getrennt von der fachlichen Bewertung durch die Bank |
| FATCA-US-Person laut Selbstauskunft | Ja/Nein | Kundenangabe zum US-Person-Status |
| Steuerliche Ansässigkeit | Liste von Ländercodes | Kundenangabe; separat von Wohnadressen |
| Auslandswohnsitz | Ja/Nein | Kundenangabe über einen oder mehrere Wohnsitze außerhalb Deutschlands |
| Auslandswohnsitze | Optionale Liste von Adressobjekten | Land, Ort, PLZ, Straße und Hausnummer |
| Geplante Kontonutzung | Freitext | Kundenangabe aus dem Antrag, zum Beispiel private Ausgaben oder Auftraggeberhonorare |

Bei Selbstständigen und im Ruhestand ist das Arbeitgeberobjekt nicht anwendbar. PLZ sind Textwerte, damit führende Nullen erhalten bleiben. Hausnummern können Buchstaben enthalten. Diese Angaben werden in KYC_Beispieldaten.md für jede Kundenkennung ergänzt. US-Steuerpflicht und FATCA-Status werden als Selbstauskunft getrennt erfasst; Auslandswohnsitz und steuerliche Ansässigkeit sind ebenfalls getrennte Felder. K06 ist ein synthetischer Kunde mit deutscher und US-Staatsangehörigkeit, angegebenem US-Status und zusätzlichem US-Wohnsitz. K02 hat einen zusätzlichen Schweizer Wohnsitz ohne angegebenen US-Status. Diese Felder ändern die Trainingsregeln R1–R3 nicht; der USA-Bezug wird seit R4 nur im Prozess ausgewertet. Grundlage zum Selbstauskunftsbegriff: [BZSt FATCA](https://online.portal.bzst.de/SharedDocs/Leistungsbeschreibung/DE/meldung_nach_FATCA-Abkommen.html).

Die elf Beispielkunden dienen der fachlichen Planung. Die Datei KYC_Trainingsdaten_5000.json (später auf KYC_Trainingsdaten_6000.json erweitert) ergänzt sie um 5.000 synthetische Kundenfälle mit getrennten Eingaben und Sollbewertungen: 4.000 Training, 500 Validierung und 500 Test. Je 2.500 Fälle benötigen laut Demo-Richtlinie manuelle Prüfung bzw. keine manuelle Prüfung. Von den 4.000 regelgrünen Fällen haben 1.500 zusätzlichen manuellen Prüfbedarf. Die 1.000 Ausgangsfamilien bleiben zwischen den Splits getrennt. Die Texte sind vorlagenbasiert; gleiche Motive kommen in allen Splits vor. Verwendung und Grenzen stehen in KYC_Trainingsdaten_README.md. Die Sollbewertungen sind konstruiert und noch nicht anhand echter Kundenakten fachlich validiert.

Für den Vortrag vergleichen wir zunächst dasselbe Modell ohne Anpassung mit einer angepassten Variante. So lässt sich zeigen, ob Training bei unserer Aufgabe tatsächlich hilft. Als Entscheidungsmodell wählen wir Laya Multilingual unter Apache-2.0. Das lokale Training lief auf einem Mac M1 Max mit 64 GB RAM über PyTorch MPS. Ohne Anpassung schickt das Modell 246 von 250 unauffälligen Testfällen unnötig zur manuellen Prüfung; nach Anpassung ist der synthetische Testsplit fehlerfrei, bei den Demo-Fällen wird jedoch K10 fälschlich freigegeben. Das aktive Modell v2 behebt die Adress-Abkürzung aus K12/K13; K10 bleibt falsch (siehe KYC_Trainingsergebnisse.md). Laya liefert Entscheidungen und Wahrscheinlichkeiten; für freie Begründungen und Feldbelege benötigt die Demo eine zusätzliche Komponente. Die Auswahl und die Bewertungsgrenzen stehen in KYC_Modellauswahl.md.

Wichtige Bewertungsgrößen:

- Wie viele tatsächlich zu prüfende Fälle werden fälschlich automatisch freigegeben?
- Wie viele unauffällige Fälle werden unnötig zur manuellen Prüfung geschickt?
- Sind die Begründungen durch die angegebenen Daten und Dokumentstellen gedeckt?
- Wie oft enthält sich das Modell oder liefert eine ungültige Antwort?

Mit synthetischen Daten demonstrieren wir das Verfahren. Eine Aussage über die Qualität bei realen Bankkunden erfordert gesonderte, fachlich geprüfte Daten.

## 6. Vorgeschlagene Aufteilung des Vortrags

| Zeit | Inhalt |
| --- | --- |
| 0–4 Minuten | Problem und KYC-Beispiel |
| 4–9 Minuten | BPMN: Regeln, LLM und manuelle Prüfung |
| 9–14 Minuten | Daten, Nachweise und Fallbewertungen |
| 14–19 Minuten | Modellanpassung und Vergleich ohne Anpassung |
| 19–27 Minuten | Live-Demo: K01 automatische Freigabe, K11 geschäftliche Nutzung, K06 USA-Bezug (R4), K15 Ablehnung durch Regel (R5), K13/K14 Wohnadresse vs. Arbeitgeber, Postkorb und Dashboard |
| 27–30 Minuten | Ergebnisse und Grenzen |
| Anschließend 15 Minuten | Fragerunde |

Nächste Schritte: Stichproben aus den 5.000 synthetischen Fällen fachlich prüfen, einen unabhängig formulierten Testdatensatz erstellen, die Trainingsdaten so variieren, dass Formulierung und Nachweislage nicht mehr gekoppelt sind (Befund K10), und eine Komponente für Begründungen und Feldbelege ergänzen.
