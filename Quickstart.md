# Quickstart: KYC-Demo starten

`start_demo.sh` startet den Laya-Dienst und den Kogito-Prozessdienst, spielt die Demo-Fälle K01–K15 ein und öffnet das Dashboard. Die Dienste laufen weiter, bis du sie mit Strg+C beendest.

## Voraussetzungen

- Python-Umgebung `.venv/` im Projektordner (enthält Laya, PyTorch und uvicorn)
- Java 21; Maven nur, wenn neu gebaut werden muss
- Modell `modelle/laya-multilingual-kyc-v2/`
- Ports 8000 (Laya) und 8080 (Kogito) frei

## Starten

```bash
cd "/Users/mp/Documents/VSC-Projekte/Vorträge/Vertical AI"
./start_demo.sh
```

Ablauf:

1. Fehlt der Build des Prozessdienstes, baut das Skript ihn zuerst (`mvn package` mit Tests, ca. 1 Minute).
2. Laya lädt das Modell. Das dauert etwa 40 Sekunden, das Skript zeigt so lange Punkte an.
3. Kogito ist nach wenigen Sekunden bereit.
4. Die Fälle K01–K15 werden gestartet, je eine Zeile pro Fall.
5. Der Browser öffnet das Dashboard unter http://localhost:8080/#dashboard.
6. Das Terminal wartet. **Offen lassen**, solange die Demo läuft.

Varianten:

| Aufruf | Wirkung |
| --- | --- |
| `./start_demo.sh` | Dienste starten, Demo-Fälle einspielen, offene Prüfungen bleiben stehen |
| `NO_CASES=1 ./start_demo.sh` | Nur Dienste starten, keine Fälle einspielen; Fälle dann live in der Oberfläche starten |
| `./start_demo.sh --decide approve` | Nach dem Einspielen alle offenen manuellen Prüfungen freigeben (`--decide reject` lehnt sie ab) |
| `BUILD=1 ./start_demo.sh` | Vorher neu bauen, z. B. nach Änderungen an DMN, BPMN oder Weboberfläche |

Für einen Vortrag ist `NO_CASES=1` meist besser: Das Dashboard ist dann leer, und jeder Fall erscheint, wenn du ihn vorführst.

## Ausgabe der Demo-Fälle lesen

```
K06  Regeln review R4     Laya keine_manuelle_pruefung  p(keine)=1.00  ->  manuelle Prüfung (offen)   ✓
K15  Regeln reject R5     Laya -                        p(keine)=0.00  ->  Ablehnung (Regeln)         ✓
14/15 Fälle mit erwartetem Endpfad
```

- **Regeln**: `green` (keine Regel), `review` (R1–R4, manuelle Prüfung) oder `reject` (R5, Ablehnung)
- **Laya**: Entscheidung des Modells; bei K15 `-`, weil R5 vor Laya ablehnt (der Wert `p(keine)` ist dort bedeutungslos)
- **Pfad**: Freigabe (automatisch), manuelle Prüfung (offen) oder Ablehnung (Regeln)
- **✓/✗**: Vergleich mit dem erwarteten Pfad. Erwartet sind 14 von 15: K10 wird bekannterweise fälschlich freigegeben (siehe KYC_Trainingsergebnisse.md).

## Mit der Weboberfläche arbeiten

http://localhost:8080 hat drei Bereiche:

**Antrag prüfen**: Vorlage K01–K15 wählen, Felder im Formular oder als JSON ändern, „Prüfung starten“. Das Ergebnis zeigt die DMN-Regeltabelle mit Treffern, die Laya-Wahrscheinlichkeiten und den Pfad. Gut zum Vorführen: einen Wert ändern und erneut prüfen, z. B. bei K01 das Sanktionsscreening auf `bestaetigter_treffer` setzen.

**Manuelle Prüfung**: Offene Aufgaben der Gruppe `kyc-reviewers` mit Antrag, Regeln und Laya-Ergebnis. Kommentar eintragen, dann „Freigeben“ oder „Ablehnen“.

**Dashboard**: Kennzahlen, Instanzliste (aktualisiert alle 2 Sekunden) und BPMN-Diagramm der gewählten Instanz: durchlaufene Schritte grün, wartender Schritt orange, Badges mit DMN- und Laya-Ergebnis, Zeitleiste. „Leeren“ löscht die Liste.

## Vorschlag für die Live-Demo

Reihenfolge wie auf der Folie „Live-Demo“:

| Fall | Was man sieht |
| --- | --- |
| K01 | Regeln grün, Laya ok → automatische Freigabe |
| K11 | Privatkonto mit geplanter Geschäftsnutzung; Laya schickt in die manuelle Prüfung |
| K06 | Laya sagt ok, Regel R4 (USA-Bezug) erzwingt trotzdem die manuelle Prüfung |
| K15 | Bestätigter Sanktionstreffer; R5 lehnt sofort ab, Laya wird nicht gefragt |
| K13 / K14 | Wohnadresse Reeperbahn → manuell; nur Arbeitgeber dort → Freigabe |
| – | Offene Fälle im Bereich „Manuelle Prüfung“ entscheiden, Ablauf im Dashboard zeigen |

## Beenden

Strg+C im Terminal von `start_demo.sh`. Das Skript beendet beide Dienste. Der Browser-Tab bleibt offen, lädt aber nichts mehr. Alle Instanzen liegen nur im Arbeitsspeicher und sind nach einem Neustart weg.

## Wenn etwas nicht klappt

| Meldung | Lösung |
| --- | --- |
| `Port 8000 ist schon belegt` (oder 8080) | Alte Instanz läuft noch: `lsof -ti tcp:8000 \| xargs kill` (bzw. 8080) |
| `Warte auf Laya … ✗ abgebrochen` | `logs/laya.log` ansehen; meist fehlt `.venv/` oder das Modellverzeichnis |
| `Warte auf Kogito … ✗` | `logs/kogito.log` ansehen; Java-Version prüfen (`java -version`, nötig ist 21) |
| Laya-Ergebnis `fehler` in der Oberfläche | Laya-Dienst nicht erreichbar; der Fall geht korrekt in die manuelle Prüfung |
| Änderungen an DMN/BPMN/Oberfläche nicht sichtbar | `BUILD=1 ./start_demo.sh` |

Weitere Details: `kyc-prozess/README.md` (Prozessdienst, REST-API), KYC_Demo_Planung.md (Fälle und Regeln), KYC_Trainingsergebnisse.md (Modell).
