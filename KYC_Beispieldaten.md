# Synthetische KYC-Beispieldaten nach erfolgreicher Identitätsprüfung

Voraussetzung für alle Datensätze: Die Identitätsprüfung des Kunden ist erfolgreich abgeschlossen. Sie findet vor dem betrachteten BPMN-Prozess statt. Alle Namen, Daten und Sachverhalte sind vollständig synthetisch. Alle Fälle werden vor der Kontoanlage geprüft. Es liegen ausschließlich Kundenangaben, Screening-Ergebnisse und gegebenenfalls eingereichte Unterlagen vor. K11 zeigt einen Widerspruch zwischen beantragtem Privatkonto und geplanter geschäftlicher Nutzung.

## Regeln der Demo

- R1: Der Kunde gibt an, selbst nicht wirtschaftlich berechtigt zu sein (Antwort „Nein“).
- R2: PEP-Status bestätigt.
- R3: Möglicher Screening-Treffer noch ungeklärt.
- R4: USA-Bezug (US-Steuerpflicht oder FATCA-US-Person laut Selbstauskunft, US-Staatsangehörigkeit, steuerliche Ansässigkeit USA oder Adresse in den USA). Nachträglich ergänzt; wird nur im Prozess ausgewertet.
- R5: Bestätigter Sanktionstreffer. **Ablehnungsregel**

R1–R4 markieren den Fall für manuelle Klärung. Das Regelergebnis lautet dann „Prüfbedarf“. Auch diese Fälle durchlaufen gemäß BPMN die LLM-Prüfung; das LLM kann den manuellen Prüfbedarf aus den Regeln nicht aufheben. Alle grünen Fälle werden ebenfalls mit dem LLM geprüft.

R5 ist der einzige Ausschlussgrund. Das Regelergebnis lautet dann „Ablehnung“: Der Antrag endet direkt am Endpunkt Ablehnung, ohne LLM-Prüfung und ohne manuelle Prüfung. Keiner der Kunden K01–K11 löst R5 aus; den Ablehnungspfad zeigt K15.

## Elf Datensätze

Bei allen Kunden gilt: Identitätsprüfung = erfolgreich abgeschlossen; Staatsangehörigkeit = DE, bei K06 zusätzlich US. Das Feld „Kunde selbst wirtschaftlich berechtigt“ enthält ausschließlich die Kundenangabe „Ja“ oder „Nein“. Eine dritte Ausprägung ist nicht vorgesehen. „Nein“ löst nach unserer fiktiven Demo-Richtlinie eine manuelle Prüfung aus, keine automatische Ablehnung. Die Mittelherkunft wird getrennt von dieser Kundenangabe betrachtet. Einkommen und geplante Zahlungen werden als Kundenangaben aus dem Antrag erfasst.

| ID | Name | Geburtsdatum | Wohnort | Beruf | Netto pro Monat | Mittelherkunft | Kunde selbst wirtschaftlich berechtigt | PEP | Screening | Regelergebnis |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| K01 | Erika Muster | 12.04.1988 | Hannover, DE | Ingenieurin | 3.200 EUR | Gehalt | Ja | Nein | Kein Treffer | Grün |
| K02 | Thomas Beispiel | 23.09.1976 | Köln, DE | Lehrer | 3.400 EUR | Gehalt, Fahrzeugverkauf | Ja | Nein | Kein Treffer | Grün |
| K03 | Laura Muster | 07.02.1993 | Hamburg, DE | Designerin | 2.800 EUR | Selbstständige Tätigkeit | Ja | Nein | Kein Treffer | Grün |
| K04 | Jan Beispiel | 18.11.1990 | Leipzig, DE | Techniker | 2.700 EUR | Gehalt | Nein | Nein | Kein Treffer | Prüfbedarf: R1; manuell |
| K05 | Claudia Muster | 30.06.1965 | Bremen, DE | Rentnerin | 2.100 EUR | Rente, Erbschaft | Ja | Nein | Kein Treffer | Grün |
| K06 | Felix Beispiel | 09.08.1985 | Stuttgart, DE | Softwareentwickler | 4.600 EUR | Gehalt, Ersparnisse | Ja | Nein | Kein Treffer | Prüfbedarf: R4; manuell |
| K07 | Lea Muster | 14.03.1972 | Berlin, DE | Hochrangige öffentliche Funktion | 7.800 EUR | Bezüge | Ja | Ja | Kein Treffer | Prüfbedarf: R2; manuell |
| K08 | Paul Beispiel | 25.01.1998 | Dresden, DE | Pflegefachkraft | 2.600 EUR | Gehalt | Ja | Nein | Kein Treffer | Grün |
| K09 | Nora Muster | 02.12.1981 | Frankfurt, DE | Projektleiterin | 4.100 EUR | Gehalt | Ja | Nein | Möglicher Treffer, ungeklärt | Prüfbedarf: R3; manuell |
| K10 | David Beispiel | 16.05.1995 | München, DE | Elektriker | 2.900 EUR | Gehalt, Schenkung | Ja | Nein | Kein Treffer | Grün |
| K11 | Simon Muster | 21.07.1987 | Düsseldorf, DE | Selbstständiger IT-Berater | 3.100 EUR | Selbstständige Tätigkeit | Ja | Nein | Kein Treffer | Grün |

Genau vier der elf Kunden werden durch diese Regeln herausgefiltert: K04 (R1), K06 (R4), K07 (R2) und K09 (R3). Abgelehnt wird keiner von ihnen. Die sieben grünen Kunden gehen ebenfalls zur LLM-Prüfung. Regelgrün allein ist keine Freigabe.

## Erweiterte Kundenfelder

Die folgenden Tabellen ergänzen dieselben elf Kunden. Die ID verbindet die Angaben mit der Haupttabelle. Alle Anschriften und Arbeitgebernamen sind fiktiv. Die Kundentexte zur Entstehung des Gesamtvermögens sind synthetische Selbstauskünfte; die fachlichen Sollbewertungen stehen getrennt davon.

### Wohnadresse

PLZ und Hausnummer werden als Text gespeichert. So bleiben führende Nullen wie in „04109“ und Zusätze wie in „23a“ erhalten. Ort und Land ergänzen die Anschrift.

| ID | PLZ | Straße | Hausnummer | Ort | Land |
| --- | --- | --- | --- | --- | --- |
| K01 | 30159 | Musterweg | 12 | Hannover | DE |
| K02 | 50667 | Beispielstraße | 8 | Köln | DE |
| K03 | 20095 | Testallee | 23a | Hamburg | DE |
| K04 | 04109 | Musterstraße | 4 | Leipzig | DE |
| K05 | 28195 | Beispielweg | 9 | Bremen | DE |
| K06 | 70173 | Teststraße | 18 | Stuttgart | DE |
| K07 | 10115 | Musterallee | 15 | Berlin | DE |
| K08 | 01067 | Beispielgasse | 5 | Dresden | DE |
| K09 | 60311 | Testweg | 20 | Frankfurt | DE |
| K10 | 80331 | Musterplatz | 6 | München | DE |
| K11 | 40213 | Beispielstraße | 12 | Düsseldorf | DE |

### Arbeitgeber

Bei Selbstständigen und im Ruhestand ist kein aktueller Arbeitgeber vorhanden. Der Arbeitgeber und seine Adressfelder sind dann fachlich nicht anwendbar; „—“ steht in der Tabelle für diese leeren Werte und nicht für eine erfundene Anschrift. Ein eigenes Unternehmen kann später als eigenes Datenobjekt ergänzt werden.

| ID | Beschäftigungsstatus | Arbeitgebername | Straße | Hausnummer | PLZ | Ort | Land |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K01 | Angestellt | Beispielmaschinenbau GmbH | Werkstraße | 50 | 30179 | Hannover | DE |
| K02 | Angestellt | Beispielschule West gGmbH | Schulstraße | 3 | 50931 | Köln | DE |
| K03 | Selbstständig | Kein Arbeitgeber | — | — | — | — | — |
| K04 | Angestellt | Beispieltechnik Mitte GmbH | Werkstattstraße | 10 | 04129 | Leipzig | DE |
| K05 | Ruhestand | Kein aktueller Arbeitgeber | — | — | — | — | — |
| K06 | Angestellt | Beispielsoftware Süd GmbH | Technologieallee | 7 | 70563 | Stuttgart | DE |
| K07 | Öffentliche Funktion | Beispielverwaltung Bund | Verwaltungsstraße | 1 | 10117 | Berlin | DE |
| K08 | Angestellt | Beispielpflege Elbe gGmbH | Klinikstraße | 22 | 01307 | Dresden | DE |
| K09 | Angestellt | Beispielprojekt Main GmbH | Projektstraße | 14 | 60327 | Frankfurt | DE |
| K10 | Angestellt | Beispielelektro Isar GmbH | Werkstattweg | 19 | 81331 | München | DE |
| K11 | Selbstständig | Kein Arbeitgeber | — | — | — | — | — |

### Entstehung des Gesamtvermögens als Freitext

Die Entstehung des Gesamtvermögens beschreibt, wie der Kunde sein Vermögen über die Zeit aufgebaut hat. Die Mittelherkunft in der Haupttabelle beschreibt dagegen die Herkunft der für das Konto vorgesehenen Mittel. Beide Angaben werden separat erfasst.

| ID | Entstehung des Gesamtvermögens – Kundenfreitext |
| --- | --- |
| K01 | Mein Vermögen entstand aus regelmäßigen Ersparnissen aus meinem Gehalt als Ingenieurin. Einen Teil lege ich seit 2015 in Fonds an. |
| K02 | Ich habe über viele Jahre einen Teil meines Lehrergehalts gespart. Der Erlös aus dem Verkauf meines privaten Fahrzeugs kommt jetzt hinzu. |
| K03 | Meine Ersparnisse stammen aus Designaufträgen seit 2018. Ich lege einen Teil meiner Einnahmen nach Steuern und Ausgaben zurück. |
| K04 | Ich habe mein Vermögen durch Ersparnisse aus meinem Technikergehalt aufgebaut. Größere Erbschaften oder Schenkungen habe ich nicht erhalten. |
| K05 | Mein Vermögen entstand aus früheren Gehaltsersparnissen und einer Erbschaft meiner Eltern. Heute erhalte ich außerdem eine Rente. |
| K06 | Ich spare seit Beginn meiner Tätigkeit als Softwareentwickler einen Teil meines Gehalts. Mein Vermögen besteht überwiegend aus diesen Ersparnissen und Fondsanlagen. |
| K07 | Mein Vermögen stammt aus früherer Berufstätigkeit, laufenden Bezügen und einer geerbten Wohnung. Es wurde über mehrere Jahre aufgebaut. |
| K08 | Meine Rücklagen stammen aus meinem Gehalt als Pflegefachkraft. Ich habe monatlich kleine Beträge gespart. |
| K09 | Ich habe mein Vermögen aus meinem Gehalt als Projektleiterin und Erträgen langfristiger Anlagen aufgebaut. |
| K10 | Mein Vermögen besteht aus Ersparnissen aus meinem Elektrikergehalt und einer Schenkung meiner Eltern. Zur Schenkung habe ich bisher keine Unterlagen eingereicht. |
| K11 | Mein Vermögen wurde aus Überschüssen meiner selbstständigen IT-Beratung aufgebaut. Ich habe nach Abzug der Kosten und Steuern regelmäßig Geld zurückgelegt. |

### US-Steuerangaben FATCA und Auslandswohnsitz

„USA-Abhängigkeit“ wird entsprechend der gewählten Bedeutung als US-Steuerangabe bzw. FATCA-Selbstauskunft erfasst. US-Steuerpflicht und FATCA-US-Person-Status bleiben getrennte Felder; in diesen synthetischen Beispielen stimmen die Angaben überein. Die Bankbewertung ist von der Selbstauskunft zu unterscheiden. Zur Ermittlung der steuerlichen Ansässigkeit dient eine Selbstauskunft; siehe [BZSt FATCA](https://online.portal.bzst.de/SharedDocs/Leistungsbeschreibung/DE/meldung_nach_FATCA-Abkommen.html).

K06 gibt neben der deutschen auch die US-Staatsangehörigkeit an; sein US-Status ist nicht allein aus einem Auslandswohnsitz abgeleitet. K02 zeigt einen Auslandswohnsitz in der Schweiz ohne angegebenen US-Status. Die Tabelle enthält zusätzliche Wohnsitze zur jeweiligen deutschen Anschrift. Ein Auslandswohnsitz ist als Ja/Nein-Feld mit einer optionalen Liste von Anschriften modelliert; die Beispiele haben höchstens einen zusätzlichen Wohnsitz. Steuerliche Ansässigkeit wird separat als Kundenangabe erfasst.

| ID | US-steuerpflichtig laut Selbstauskunft | FATCA-US-Person laut Selbstauskunft | Steuerliche Ansässigkeit laut Selbstauskunft | Auslandswohnsitz | Land | PLZ | Straße | Hausnummer | Ort |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K01 | Nein | Nein | DE | Nein | — | — | — | — | — |
| K02 | Nein | Nein | DE, CH | Ja | CH | 8001 | Musterstrasse | 14 | Zürich |
| K03 | Nein | Nein | DE | Nein | — | — | — | — | — |
| K04 | Nein | Nein | DE | Nein | — | — | — | — | — |
| K05 | Nein | Nein | DE | Nein | — | — | — | — | — |
| K06 | Ja | Ja | DE, US | Ja | US | 98101 | Example Street | 100 | Seattle |
| K07 | Nein | Nein | DE | Nein | — | — | — | — | — |
| K08 | Nein | Nein | DE | Nein | — | — | — | — | — |
| K09 | Nein | Nein | DE | Nein | — | — | — | — | — |
| K10 | Nein | Nein | DE | Nein | — | — | — | — | — |
| K11 | Nein | Nein | DE | Nein | — | — | — | — | — |

Seit Einführung von R4 löst ein USA-Bezug die manuelle Prüfung aus; K06 ist davon betroffen. Ein Auslandswohnsitz außerhalb der USA (K02, Schweiz) löst für sich genommen weiterhin keine manuelle KYC-Prüfung aus. Die zusätzlichen Daten dienen der Bewertung der Konsistenz des Kundenprofils; ein vollständiger steuerlicher Prüfprozess ist nicht Teil der Demo-Regeln.

## K11 Beantragtes Privatkonto mit geplanter geschäftlicher Nutzung

Die Identitätsprüfung ist erfolgreich abgeschlossen. Das Konto ist noch nicht angelegt. Der Kunde beantragt ein Privatkonto und nennt im strukturierten Feld „Kontozweck“ den Wert „private Lebenshaltung, Miete und Einkäufe“. Er gibt an, selbst wirtschaftlich berechtigt zu sein. PEP- und Screening-Prüfung liefern keinen Trigger.

In einem Freitext zur geplanten Kontonutzung erklärt der Kunde: „Auf dieses Konto sollen meine Auftraggeber die Honorare für IT-Projekte überweisen. Ich möchte damit auch die Hostingkosten für meine Kundenprojekte bezahlen. Ich habe ein Privatkonto ausgewählt, weil ich als Einzelunternehmer unter meinem eigenen Namen arbeite.“

Diese Erklärung ist ein synthetischer Kundenfreitext aus dem Kontoantrag. Sie beschreibt die beabsichtigte künftige Nutzung. Für diesen Fall sind die Angaben im Antrag ausreichend, um den Widerspruch zu demonstrieren; zusätzliche Unterlagen sind dafür nicht nötig.

Die Modelleingabe enthält den beantragten Kontotyp „Privatkonto“, den angegebenen privaten Kontozweck, den Beruf und den Freitext zur geplanten Nutzung. Eine vorweggenommene Bewertung „geschäftliche Nutzung“ oder die Sollentscheidung wird dem Modell nicht als Eingabefeld mitgegeben.

**Sollbewertung:** Manuelle Prüfung erforderlich. Der ausgewählte private Kontozweck widerspricht der geplanten Abwicklung von Auftraggeberhonoraren und Kosten für Kundenprojekte. Die Regeln R1–R5 bleiben grün; das LLM soll die Abweichung anhand der Antragsfelder und des Kundenfreitexts erkennen und begründen.

**Erwarteter Prozesspfad:** Regeln grün → LLM-Prüfung → manuelle Prüfung → Freigabe oder Ablehnung der beantragten Kontoanlage nach Klärung. Welche Kontovariante und welches Kundenprofil passend sind, entscheidet die manuelle Prüfung. Selbstständigkeit allein ist in diesem Beispiel kein Auslöser; entscheidend ist der Widerspruch zwischen ausgewähltem Kontotyp und erklärter geplanter Nutzung.

## Geplante wirtschaftliche Nachweise für die LLM-Demo

Für K03 soll ein synthetischer Dokumentauszug der angegebenen Mittelherkunft widersprechen: Die Kundin nennt Einnahmen aus selbstständiger Tätigkeit, der Nachweis beschreibt jedoch ein Darlehen eines Dritten. Für K10 sollen die Nachweise zur angegebenen Schenkung für eine eindeutige Bewertung nicht ausreichen. Dadurch kann das LLM bei zunächst grünen Fällen zusätzlichen manuellen Klärungsbedarf erkennen. Umgesetzt in `laya_kyc/demo_cases.py`: K03 hat eine Finanzierungsvereinbarung über ein zurückzuzahlendes Darlehen eines Dritten als Unterlage; K10 hat keine Unterlage zur Schenkung. Für K11 ist der synthetische Kundenfreitext aus dem Antrag oben ausgearbeitet.

## Zusätzliche Prüffälle K12–K15

K12–K14 wurden im Workshop als Varianten von K01 eingegeben und zeigten Schwächen des ersten Modells (siehe KYC_Trainingsergebnisse.md, Version 2). K15 zeigt die Ablehnung durch Regel R5. Vollständige Antragsdaten stehen in `laya_kyc/demo_cases.py`; Identitätsprüfung erfolgreich, Staatsangehörigkeit DE, Kunde selbst wirtschaftlich berechtigt „Ja“, PEP „Nein“, kein USA-Bezug.

| ID | Name | Geburtsdatum | Wohnadresse | Beschäftigung | Netto pro Monat | Mittelherkunft | Screening | Regelergebnis | Erwarteter Pfad |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| K12 | Tim Uphaus | 12.04.1988 | Reeperbahn 12, 20359 Hamburg | Selbstständig, Beruf „Ingenieurin“, kein Arbeitgeber | 3.200 EUR | Gehaltsersparnisse | Kein Treffer | Grün | LLM → manuelle Prüfung |
| K13 | Karl Jones | 12.04.1988 | Reeperbahn 12, 20359 Hamburg | Angestellt, Beispielmaschinenbau GmbH, Reeperbahn 50 | 3.200 EUR | Gehaltsersparnisse | Kein Treffer | Grün | LLM → manuelle Prüfung |
| K14 | Marcin Pankowski | 12.04.1988 | Musterweg 12, 30159 Hannover | Angestellt, Beispielmaschinenbau GmbH, Reeperbahn 50 | 3.200 EUR | Gehaltsersparnisse | Kein Treffer | Grün | LLM → Freigabe |
| K15 | Viktor Beispiel | 03.10.1979 | Musterweg 14, 30159 Hannover | Angestellt (Ingenieur), Beispielmaschinenbau GmbH, Werkstraße 50, Hannover | 3.300 EUR | Gehaltsersparnisse | **Bestätigter Treffer** | **Ablehnung: R5** | Ablehnung durch Regeln, ohne LLM |

- K12: Wohnadresse an der Reeperbahn; außerdem widersprüchlich: selbstständig, aber Gehaltsersparnisse und Arbeitgeberbestätigung.
- K13: Wohnadresse an der Reeperbahn, sonst konsistent. Allein die Adresse führt nach der Demo-Richtlinie zur manuellen Prüfung.
- K14: Nur der Arbeitgeber sitzt an der Reeperbahn; die Wohnadresse ist unauffällig. Kein Prüfgrund.
- K15: Angaben, Gehalt und Arbeitgeberbestätigung sind konsistent. Das synthetische Sanktionsscreening meldet einen bestätigten Treffer (Referenz SAN-SYN-K15). R5 lehnt ab, bevor Laya aufgerufen wird. Der Screening-Status „bestätigter Treffer“ kommt in den Trainingsdaten nicht vor.

Die Tabellen sind ein kompaktes Demonstrationsschema; vollständige Kundenakten werden im nächsten Planungsschritt ausgearbeitet.
