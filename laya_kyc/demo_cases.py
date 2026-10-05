"""Die Demo-Kunden K01–K11 aus KYC_Beispieldaten.md, die Prüffälle K12–K14 und der Ablehnungsfall K15 im
Eingabeschema der Trainingsdaten.

Stammdaten, Adressen, Arbeitgeber, Vermögensfreitexte, Steuerangaben und der K11-Freitext
stammen aus KYC_Beispieldaten.md. Beträge, Kontozwecke und Unterlagenauszüge, die dort
nicht festgelegt sind, wurden für die Demo synthetisch ergänzt (für K03 und K10 gemäß
Abschnitt „Geplante wirtschaftliche Nachweise“). Der erwartete Pfad stammt aus
KYC_Demo_Planung.md, Abschnitt 4. Er wird dem Modell nicht übergeben.
"""
import json
from pathlib import Path

PRIVATE_PURPOSE = "Private Lebenshaltung, Miete und Einkäufe."
PRIVATE_USAGE = "Ich möchte mit dem Konto meine Miete und Einkäufe bezahlen und private Rücklagen bilden."
NO_PEP = ("Nein", "Kein PEP-Befund im synthetischen Screening.")
NO_HIT = ("kein_treffer", "Kein Treffer im synthetischen Screening.")
TAX_DE_ONLY = {
    "us_steuerpflicht_laut_selbstauskunft": "Nein",
    "fatca_us_person_laut_selbstauskunft": "Nein",
    "steuerliche_ansaessigkeit_laut_selbstauskunft": ["DE"],
    "erlaeuterung_freitext": "Ich gebe Deutschland als steuerliche Ansässigkeit an.",
    "selbstauskunft_vorhanden": True,
}


def address(postcode, street, house_number, city, country="DE"):
    return {"plz": postcode, "strasse": street, "hausnummer": house_number, "ort": city, "land": country}


def make_case(case_id, first_name, last_name, birth_date, home_address, status, occupation, net_income,
              employer, wealth_text, funds_category, funds_text, amount, expected_path, *,
              beneficial_owner="Ja", nationalities=("DE",), foreign_addresses=(), tax=TAX_DE_ONLY,
              pep=NO_PEP, screening=NO_HIT, purpose=PRIVATE_PURPOSE, usage=PRIVATE_USAGE, documents=()):
    # Nur R1–R3: So hat Laya das Regelergebnis im Training gesehen. R4 (USA-Bezug) wertet der Prozess aus.
    rules = [rule for rule, triggered in (("R1", beneficial_owner == "Nein"), ("R2", pep[0] == "Ja"),
                                          ("R3", screening[0] == "moeglicher_treffer_ungeklaert")) if triggered]
    return {
        "kunden_id": case_id,
        "expected_path": expected_path,
        "eingabe": {
            "prozessphase": "nach_identifizierung_vor_kontoanlage",
            "identitaetspruefung": {"status": "erfolgreich_abgeschlossen", "datum": "2026-10-01",
                                    "verfahren": "VideoIdent"},
            "kunde": {
                "vorname": first_name, "nachname": last_name, "geburtsdatum": birth_date,
                "staatsangehoerigkeiten": list(nationalities), "adresse": home_address,
                "ist_selbst_wirtschaftlich_berechtigt": beneficial_owner,
                "auslandswohnsitz": "Ja" if foreign_addresses else "Nein",
                "auslandsadressen": list(foreign_addresses),
            },
            "beschaeftigung": {"status": status, "beruf": occupation,
                               "nettoeinkommen_monat_eur_laut_kunde": net_income, "arbeitgeber": employer},
            "entstehung_gesamtvermoegen_freitext": wealth_text,
            "mittelherkunft": {"kategorie": funds_category, "beschreibung_freitext": funds_text,
                               "geplante_ersteinzahlung_eur": amount},
            "steuerangaben": tax,
            "screening": {"pep": pep[0], "pep_erlaeuterung": pep[1],
                          "sanktionsscreening_status": screening[0], "screening_erlaeuterung": screening[1]},
            "kontoantrag": {"kontotyp": "Privatkonto", "kontozweck": purpose, "geplante_nutzung_freitext": usage},
            "eingereichte_unterlagen": [
                {"dokument_id": f"DOC-{i + 1:02d}", "typ": doc_type, "textauszug": text}
                for i, (doc_type, text) in enumerate(documents)
            ],
            "regelpruefung": {"ergebnis": "Pruefbedarf" if rules else "Gruen", "ausgeloeste_regeln": rules},
        },
    }


K01_WEALTH = ("Mein Vermögen entstand aus regelmäßigen Ersparnissen aus meinem Gehalt als Ingenieurin. "
              "Einen Teil lege ich seit 2015 in Fonds an.")
K01_FUNDS = "Die vorgesehene Ersteinzahlung von 3.000 EUR stammt aus meinen Gehaltsersparnissen."
K01_EMPLOYER_CONFIRMATION = ("Arbeitgeberbestaetigung", "Arbeitgeber: Beispielmaschinenbau GmbH. Beschäftigungsverhältnis "
                             "besteht. Das vom Kunden angegebene Nettoeinkommen beträgt 3.200 EUR monatlich.")
SALARY_USAGE = "Auf das Konto soll mein Gehalt eingehen; davon bezahle ich Miete, Einkäufe und Versicherungen."


CASES = [
    make_case("K01", "Erika", "Muster", "1988-04-12", address("30159", "Musterweg", "12", "Hannover"),
         "angestellt", "Ingenieurin", 3200,
         {"name": "Beispielmaschinenbau GmbH", **address("30179", "Werkstraße", "50", "Hannover")},
         "Mein Vermögen entstand aus regelmäßigen Ersparnissen aus meinem Gehalt als Ingenieurin. "
         "Einen Teil lege ich seit 2015 in Fonds an.",
         "Gehaltsersparnisse", "Die vorgesehene Ersteinzahlung von 3.000 EUR stammt aus meinen Gehaltsersparnissen.",
         3000, "LLM → Freigabe",
         usage="Auf das Konto soll mein Gehalt eingehen; davon bezahle ich Miete, Einkäufe und Versicherungen.",
         documents=[("Arbeitgeberbestaetigung", "Arbeitgeber: Beispielmaschinenbau GmbH. Beschäftigungsverhältnis "
                      "besteht. Das vom Kunden angegebene Nettoeinkommen beträgt 3.200 EUR monatlich.")]),
    make_case("K02", "Thomas", "Beispiel", "1976-09-23", address("50667", "Beispielstraße", "8", "Köln"),
         "angestellt", "Lehrer", 3400,
         {"name": "Beispielschule West gGmbH", **address("50931", "Schulstraße", "3", "Köln")},
         "Ich habe über viele Jahre einen Teil meines Lehrergehalts gespart. Der Erlös aus dem Verkauf "
         "meines privaten Fahrzeugs kommt jetzt hinzu.",
         "Fahrzeugverkauf", "Die vorgesehene Ersteinzahlung von 18.000 EUR stammt aus dem Verkauf meines privaten Fahrzeugs.",
         18000, "LLM → Freigabe",
         foreign_addresses=[address("8001", "Musterstrasse", "14", "Zürich", "CH")],
         tax={**TAX_DE_ONLY, "steuerliche_ansaessigkeit_laut_selbstauskunft": ["DE", "CH"],
                 "erlaeuterung_freitext": "Ich habe neben meiner deutschen Anschrift einen weiteren Wohnsitz in "
                                          "Zürich, CH. In der steuerlichen Selbstauskunft gebe ich DE und CH an."},
         documents=[("Kaufvertrag", "Verkäufer/in: Thomas Beispiel. Gegenstand: privates Fahrzeug. Kaufpreis: "
                      "18.000 EUR. Der Auszug beschreibt den vereinbarten Verkauf; er enthält keinen Nachweis "
                      "eines Kontovorgangs.")]),
    make_case("K03", "Laura", "Muster", "1993-02-07", address("20095", "Testallee", "23a", "Hamburg"),
         "selbststaendig", "Designerin", 2800, None,
         "Meine Ersparnisse stammen aus Designaufträgen seit 2018. Ich lege einen Teil meiner Einnahmen "
         "nach Steuern und Ausgaben zurück.",
         "Ruecklagen_aus_Selbststaendigkeit", "Die geplanten 6.000 EUR sind persönliche Rücklagen nach Steuern "
         "und betrieblichen Kosten aus meiner selbstständigen Tätigkeit.",
         6000, "LLM → manuelle Prüfung",
         usage="Über das Konto sollen meine persönlichen Ausgaben laufen; Geld für meinen Betrieb bleibt "
                 "auf dem Geschäftskonto.",
         documents=[("Finanzierungsvereinbarung", "Vereinbarung für Laura Muster: Darlehen von einer dritten "
                      "Person über 6.000 EUR. Vorgesehene Verwendung: Ersteinzahlung auf das beantragte Konto. "
                      "Der Betrag ist zurückzuzahlen.")]),
    make_case("K04", "Jan", "Beispiel", "1990-11-18", address("04109", "Musterstraße", "4", "Leipzig"),
         "angestellt", "Techniker", 2700,
         {"name": "Beispieltechnik Mitte GmbH", **address("04129", "Werkstattstraße", "10", "Leipzig")},
         "Ich habe mein Vermögen durch Ersparnisse aus meinem Technikergehalt aufgebaut. Größere "
         "Erbschaften oder Schenkungen habe ich nicht erhalten.",
         "Gehaltsersparnisse", "Die vorgesehene Ersteinzahlung von 2.000 EUR stammt aus meinen Gehaltsersparnissen.",
         2000, "Prüfbedarf (R1) → LLM → manuelle Prüfung", beneficial_owner="Nein"),
    make_case("K05", "Claudia", "Muster", "1965-06-30", address("28195", "Beispielweg", "9", "Bremen"),
         "ruhestand", "Rentnerin", 2100, None,
         "Mein Vermögen entstand aus früheren Gehaltsersparnissen und einer Erbschaft meiner Eltern. "
         "Heute erhalte ich außerdem eine Rente.",
         "Erbschaft", "Ich möchte 60.000 EUR aus einer Erbschaft auf das neue Konto einbringen.",
         60000, "LLM → Freigabe",
         documents=[("Nachlassunterlage", "Begünstigte Person: Claudia Muster. In der synthetischen "
                      "Nachlassunterlage ausgewiesener Geldanteil: 60.000 EUR.")]),
    make_case("K06", "Felix", "Beispiel", "1985-08-09", address("70173", "Teststraße", "18", "Stuttgart"),
         "angestellt", "Softwareentwickler", 4600,
         {"name": "Beispielsoftware Süd GmbH", **address("70563", "Technologieallee", "7", "Stuttgart")},
         "Ich spare seit Beginn meiner Tätigkeit als Softwareentwickler einen Teil meines Gehalts. Mein "
         "Vermögen besteht überwiegend aus diesen Ersparnissen und Fondsanlagen.",
         "Gehaltsersparnisse", "Die vorgesehene Ersteinzahlung von 10.000 EUR stammt aus meinen Gehaltsersparnissen.",
         10000, "Prüfbedarf (R4) → LLM → manuelle Prüfung", nationalities=("DE", "US"),
         foreign_addresses=[address("98101", "Example Street", "100", "Seattle", "US")],
         tax={"us_steuerpflicht_laut_selbstauskunft": "Ja", "fatca_us_person_laut_selbstauskunft": "Ja",
                 "steuerliche_ansaessigkeit_laut_selbstauskunft": ["DE", "US"],
                 "erlaeuterung_freitext": "Ich habe die deutsche und die US-Staatsangehörigkeit, einen weiteren "
                                          "Wohnsitz in Seattle und gebe meinen US-Status in der Selbstauskunft an.",
                 "selbstauskunft_vorhanden": True},
         documents=[("Arbeitgeberbestaetigung", "Arbeitgeber: Beispielsoftware Süd GmbH. Beschäftigungsverhältnis "
                      "besteht. Das vom Kunden angegebene Nettoeinkommen beträgt 4.600 EUR monatlich.")]),
    make_case("K07", "Lea", "Muster", "1972-03-14", address("10115", "Musterallee", "15", "Berlin"),
         "oeffentliche_funktion", "Hochrangige öffentliche Funktion", 7800,
         {"name": "Beispielverwaltung Bund", **address("10117", "Verwaltungsstraße", "1", "Berlin")},
         "Mein Vermögen stammt aus früherer Berufstätigkeit, laufenden Bezügen und einer geerbten Wohnung. "
         "Es wurde über mehrere Jahre aufgebaut.",
         "Gehaltsersparnisse", "Die vorgesehene Ersteinzahlung von 5.000 EUR stammt aus meinen Ersparnissen aus Bezügen.",
         5000, "Prüfbedarf (R2) → LLM → manuelle Prüfung",
         pep=("Ja", "Bestätigter PEP-Befund im vollständig synthetischen Screening: hochrangige öffentliche "
                    "Funktion, Referenz PEP-SYN-K07.")),
    make_case("K08", "Paul", "Beispiel", "1998-01-25", address("01067", "Beispielgasse", "5", "Dresden"),
         "angestellt", "Pflegefachkraft", 2600,
         {"name": "Beispielpflege Elbe gGmbH", **address("01307", "Klinikstraße", "22", "Dresden")},
         "Meine Rücklagen stammen aus meinem Gehalt als Pflegefachkraft. Ich habe monatlich kleine Beträge gespart.",
         "Gehaltsersparnisse", "Die vorgesehene Ersteinzahlung von 1.500 EUR stammt aus meinen Gehaltsersparnissen.",
         1500, "LLM → Freigabe",
         usage="Auf das Konto soll mein Gehalt eingehen; davon bezahle ich Miete, Einkäufe und Versicherungen."),
    make_case("K09", "Nora", "Muster", "1981-12-02", address("60311", "Testweg", "20", "Frankfurt"),
         "angestellt", "Projektleiterin", 4100,
         {"name": "Beispielprojekt Main GmbH", **address("60327", "Projektstraße", "14", "Frankfurt")},
         "Ich habe mein Vermögen aus meinem Gehalt als Projektleiterin und Erträgen langfristiger Anlagen aufgebaut.",
         "Gehaltsersparnisse", "Die vorgesehene Ersteinzahlung von 4.000 EUR stammt aus meinen Gehaltsersparnissen.",
         4000, "Prüfbedarf (R3) → LLM → manuelle Prüfung",
         screening=("moeglicher_treffer_ungeklaert", "Möglicher Namensgleichklang mit einem vollständig "
                    "synthetischen Screening-Referenzdatensatz SCR-SYN-K09. Die Zuordnung ist offen.")),
    make_case("K10", "David", "Beispiel", "1995-05-16", address("80331", "Musterplatz", "6", "München"),
         "angestellt", "Elektriker", 2900,
         {"name": "Beispielelektro Isar GmbH", **address("81331", "Werkstattweg", "19", "München")},
         "Mein Vermögen besteht aus Ersparnissen aus meinem Elektrikergehalt und einer Schenkung meiner "
         "Eltern. Zur Schenkung habe ich bisher keine Unterlagen eingereicht.",
         "Schenkung", "Ich plane 15.000 EUR aus einer Schenkung einzubringen. Einen Nachweis habe ich nicht beigefügt.",
         15000, "LLM unklar → manuelle Prüfung"),
    make_case("K11", "Simon", "Muster", "1987-07-21", address("40213", "Beispielstraße", "12", "Düsseldorf"),
         "selbststaendig", "Selbstständiger IT-Berater", 3100, None,
         "Mein Vermögen wurde aus Überschüssen meiner selbstständigen IT-Beratung aufgebaut. Ich habe nach "
         "Abzug der Kosten und Steuern regelmäßig Geld zurückgelegt.",
         "Ruecklagen_aus_Selbststaendigkeit", "Die geplanten 5.000 EUR sind persönliche Rücklagen nach Steuern "
         "und betrieblichen Kosten aus meiner selbstständigen Tätigkeit.",
         5000, "LLM → manuelle Prüfung",
         purpose="private Lebenshaltung, Miete und Einkäufe",
         usage="Auf dieses Konto sollen meine Auftraggeber die Honorare für IT-Projekte überweisen. Ich möchte "
                 "damit auch die Hostingkosten für meine Kundenprojekte bezahlen. Ich habe ein Privatkonto "
                 "ausgewählt, weil ich als Einzelunternehmer unter meinem eigenen Namen arbeite."),
    # K12–K14: im Workshop eingegebene Prüffälle (Varianten von K01), die Schwächen des ersten Modells zeigten.
    make_case("K12", "Tim", "Uphaus", "1988-04-12", address("20359", "Reeperbahn", "12", "Hamburg"),
         "selbststaendig", "Ingenieurin", 3200, None,
         K01_WEALTH, "Gehaltsersparnisse", K01_FUNDS, 3000,
         "LLM → manuelle Prüfung (Wohnadresse Reeperbahn; selbstständig, aber Gehalt und Arbeitgeberbestätigung)",
         usage=SALARY_USAGE, documents=[K01_EMPLOYER_CONFIRMATION]),
    make_case("K13", "Karl", "Jones", "1988-04-12", address("20359", "Reeperbahn", "12", "Hamburg"),
         "angestellt", "Ingenieurin", 3200,
         {"name": "Beispielmaschinenbau GmbH", **address("20359", "Reeperbahn", "50", "Hamburg")},
         K01_WEALTH, "Gehaltsersparnisse", K01_FUNDS, 3000, "LLM → manuelle Prüfung (Wohnadresse Reeperbahn)",
         usage=SALARY_USAGE, documents=[K01_EMPLOYER_CONFIRMATION]),
    make_case("K14", "Marcin", "Pankowski", "1988-04-12", address("30159", "Musterweg", "12", "Hannover"),
         "angestellt", "Ingenieurin", 3200,
         {"name": "Beispielmaschinenbau GmbH", **address("20359", "Reeperbahn", "50", "Hamburg")},
         K01_WEALTH, "Gehaltsersparnisse", K01_FUNDS, 3000,
         "LLM → Freigabe (nur der Arbeitgeber sitzt an der Reeperbahn)",
         usage=SALARY_USAGE, documents=[K01_EMPLOYER_CONFIRMATION]),
    # K15: Ausschlussgrund R5. Der Status bestaetigter_treffer liegt außerhalb der Trainingsdaten; der Prozess
    # lehnt ab, bevor Laya aufgerufen wird.
    make_case("K15", "Viktor", "Beispiel", "1979-10-03", address("30159", "Musterweg", "14", "Hannover"),
         "angestellt", "Ingenieur", 3300,
         {"name": "Beispielmaschinenbau GmbH", **address("30179", "Werkstraße", "50", "Hannover")},
         "Mein Vermögen entstand aus regelmäßigen Ersparnissen aus meinem Gehalt als Ingenieur.",
         "Gehaltsersparnisse", "Die vorgesehene Ersteinzahlung von 3.000 EUR stammt aus meinen Gehaltsersparnissen.",
         3000, "Ablehnung durch Regeln (R5), ohne LLM",
         usage=SALARY_USAGE,
         screening=("bestaetigter_treffer", "Bestätigter Treffer im vollständig synthetischen Sanktionsscreening: "
                    "Identität und Geburtsdatum stimmen mit Referenz SAN-SYN-K15 überein."),
         documents=[("Arbeitgeberbestaetigung", "Arbeitgeber: Beispielmaschinenbau GmbH. Beschäftigungsverhältnis "
                      "besteht. Das vom Kunden angegebene Nettoeinkommen beträgt 3.300 EUR monatlich.")]),
]


if __name__ == "__main__":
    target = Path(__file__).with_name("demo_cases.json")
    target.write_text(json.dumps({"kunden": CASES}, ensure_ascii=False, indent=2))
    print(f"{len(CASES)} Fälle geschrieben: {target}")
