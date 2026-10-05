"""Ergänzt den KYC-Datensatz um 1.000 Varianten, die Scheinzusammenhänge auflösen.

Befund (KYC_Trainingsergebnisse.md): Alle 50 Reeperbahn-Fälle waren Selbstständige mit
Rücklagenbestätigung, und kein anderer Fall hatte dieses Dokument. Das Modell lernte deshalb den
Dokumenttyp statt der Wohnadresse. Zusätzlich fehlte der Widerspruch „selbstständig, aber Gehalt
und Arbeitgeberbestätigung“.

Jede neue Variante wird aus einem bestehenden Fall abgeleitet und bleibt in dessen Familie und
Split; die Trennung der Familien zwischen den Splits bleibt erhalten. Das Original
KYC_Trainingsdaten_5000.json bleibt unverändert.

    python augment_dataset.py   # schreibt KYC_Trainingsdaten_6000.json und die Validierung
"""
import copy
import hashlib
import json
import random
from collections import Counter, defaultdict

import jsonschema

import kyc_data as K

SOURCE_FILE = K.PROJECT_DIR / "KYC_Trainingsdaten_5000.json"
TARGET_FILE = K.PROJECT_DIR / "KYC_Trainingsdaten_6000.json"
VALIDATION_FILE = K.PROJECT_DIR / "KYC_Trainingsdaten_6000_Validierung.json"
SCHEMA_FILE = K.PROJECT_DIR / "KYC_Trainingsdaten.schema.json"
SEED = 20261004
MAX_VARIANTS = 20

TRIGGER_STREETS = [("Reeperbahn", "20359", 4), ("Große Freiheit", "22767", 2),
                   ("Davidstraße", "20359", 2), ("Spielbudenplatz", "20359", 2)]
# Unauffällige Adressen; Budapester Straße zeigt, dass die PLZ 20359 allein kein Auslöser ist.
NEUTRAL_ADDRESSES = [("Budapester Straße", "20359", "Hamburg"), ("Testallee", "20095", "Hamburg"),
                     ("Musterweg", "30159", "Hannover"), ("Beispielstraße", "50667", "Köln"),
                     ("Musterstraße", "04109", "Leipzig"), ("Musterplatz", "80331", "München"),
                     ("Beispielgasse", "01067", "Dresden"), ("Musterallee", "10115", "Berlin")]
GREEN_OK_SCENARIOS = ["gehalt_konsistent", "ruhestand_konsistent", "erbschaft_belegt", "fahrzeugverkauf_belegt",
                      "schenkung_belegt", "vermoegensaufbau_belegt", "darlehen_erklaert", "selbststaendig_private_nutzung",
                      "auslandswohnsitz_konsistent", "arbeitgeberwechsel_erklaert", "us_status_konsistent"]


def house_number(rng):
    return str(rng.randint(1, 160)) + rng.choice(["", "", "", "a", "b"])


def trigger_address(rng):
    street, postcode, _ = rng.choices(TRIGGER_STREETS, weights=[w for *_, w in TRIGGER_STREETS])[0]
    return {"plz": postcode, "strasse": street, "hausnummer": house_number(rng), "ort": "Hamburg", "land": "DE"}


def neutral_address(rng):
    street, postcode, city = rng.choice(NEUTRAL_ADDRESSES)
    return {"plz": postcode, "strasse": street, "hausnummer": house_number(rng), "ort": city, "land": "DE"}


def full_name(application):
    return f"{application['kunde']['vorname']} {application['kunde']['nachname']}"


def euro(amount):
    return f"{amount:,}".replace(",", ".") + " EUR"


def manual(reason, evidence, question):
    return {"manuelle_pruefung_erforderlich": True, "entscheidung": "manuelle_pruefung",
            "begruendung": reason, "belege": evidence, "offene_fragen": [question]}


def no_review(reason, evidence):
    return {"manuelle_pruefung_erforderlich": False, "entscheidung": "keine_manuelle_pruefung",
            "begruendung": reason, "belege": evidence, "offene_fragen": []}


def address_evidence(application):
    address = application["kunde"]["adresse"]
    return [{"feld": f"kunde.adresse.{f}", "wert": address[f]} for f in ("strasse", "plz", "ort")]


# ---------- Varianten ----------

def address_trigger_variant(source, rng):
    """A: Wohnadresse im Reeperbahn-Umfeld, alles andere wie im unauffälligen Ausgangsfall."""
    app = copy.deepcopy(source["eingabe"])
    app["kunde"]["adresse"] = trigger_address(rng)
    a = app["kunde"]["adresse"]
    label = manual(
        f"Die Wohnadresse liegt in der Straße {a['strasse']}, {a['plz']} Hamburg, an der Reeperbahn oder in ihrem "
        "unmittelbaren Umfeld. Die übrigen Angaben und Nachweise sind konsistent und die Regeln R1–R3 bleiben grün. "
        "Allein die Lage der Wohnadresse erfordert gemäß der fiktiven Demo-Richtlinie eine manuelle Adressklärung.",
        address_evidence(app),
        "Kann die Wohnadresse im Rahmen der nach der Demo-Richtlinie vorgesehenen manuellen Adressklärung bestätigt werden?")
    return "adresse_reeperbahn_umfeld_divers", app, label


def reserves_neutral_address_variant(source, rng):
    """B: Bisheriger Adressfall (Selbstständig, Rücklagenbestätigung) an unauffälliger Wohnadresse."""
    app = copy.deepcopy(source["eingabe"])
    app["kunde"]["adresse"] = neutral_address(rng)
    a = app["kunde"]["adresse"]
    label = no_review(
        f"Die Rücklagen aus selbstständiger Tätigkeit sind durch die Rücklagenbestätigung belegt und passen zur "
        f"geplanten Ersteinzahlung. Die Wohnadresse ({a['strasse']}, {a['plz']} {a['ort']}) löst nach der Demo-Richtlinie "
        "keine Adressklärung aus; die PLZ allein ist kein Auslöser.",
        [{"feld": "mittelherkunft.beschreibung_freitext", "wert": app["mittelherkunft"]["beschreibung_freitext"]},
         {"feld": "eingereichte_unterlagen.0.textauszug", "wert": app["eingereichte_unterlagen"][0]["textauszug"]},
         *address_evidence(app)])
    return "ruecklagen_belegt_adresse_unauffaellig", app, label


def reserves_documented_variant(source, rng):
    """C: Selbstständig mit privater Nutzung, Rücklagen jetzt zusätzlich durch Bestätigung belegt."""
    app = copy.deepcopy(source["eingabe"])
    amount = app["mittelherkunft"]["geplante_ersteinzahlung_eur"]
    text = (f"Synthetische Rücklagenbestätigung für {full_name(app)}: Die für die Ersteinzahlung vorgesehenen {euro(amount)} "
            "stammen aus eigenen Überschüssen der selbstständigen Tätigkeit nach Abzug von Steuern und betrieblichen Kosten. "
            "Der Betrag steht als persönliche Rücklage zur Verfügung.")
    app["eingereichte_unterlagen"] = [{"dokument_id": "DOC-01", "typ": "Ruecklagenbestaetigung", "textauszug": text}]
    label = no_review(
        "Die selbstständige Tätigkeit und die privaten Rücklagen sind erklärt und durch die Rücklagenbestätigung "
        "belegt; Betrag und Herkunft stimmen überein. Die geplante Nutzung ist ausdrücklich privat.",
        [{"feld": "mittelherkunft.beschreibung_freitext", "wert": app["mittelherkunft"]["beschreibung_freitext"]},
         {"feld": "eingereichte_unterlagen.0.textauszug", "wert": text}])
    return "ruecklagen_belegt_selbststaendig", app, label


def employer_at_trigger_street_variant(source, rng):
    """D: Nur der Arbeitgeber sitzt im Reeperbahn-Umfeld; die Wohnadresse ist unauffällig."""
    app = copy.deepcopy(source["eingabe"])
    app["beschaeftigung"]["arbeitgeber"].update(trigger_address(rng))
    employer = app["beschaeftigung"]["arbeitgeber"]
    label = no_review(
        f"Der Arbeitgeber hat seinen Sitz in der Straße {employer['strasse']}, {employer['plz']} Hamburg. Die "
        "Demo-Richtlinie verlangt eine Adressklärung nur für die Wohnadresse; Arbeitgeber, Gehalt und Nachweis passen "
        "zusammen.",
        [{"feld": "beschaeftigung.arbeitgeber.strasse", "wert": employer["strasse"]},
         {"feld": "kunde.adresse.strasse", "wert": app["kunde"]["adresse"]["strasse"]}])
    return "arbeitgeber_im_reeperbahn_umfeld", app, label


def self_employed_salary_variant(source, rng):
    """E: Status selbstständig, aber Gehaltsersparnisse und Arbeitgeberbestätigung."""
    app = copy.deepcopy(source["eingabe"])
    app["beschaeftigung"]["status"] = "selbststaendig"
    if rng.random() < 0.5:
        app["beschaeftigung"]["arbeitgeber"] = None
    evidence = [{"feld": "beschaeftigung.status", "wert": "selbststaendig"},
                {"feld": "mittelherkunft.kategorie", "wert": app["mittelherkunft"]["kategorie"]},
                {"feld": "eingereichte_unterlagen.0.textauszug", "wert": app["eingereichte_unterlagen"][0]["textauszug"]}]
    label = manual(
        "Der Kunde gibt an, selbstständig zu sein, erklärt die Mittel aber als Gehaltsersparnisse und reicht eine "
        "Arbeitgeberbestätigung über ein bestehendes Beschäftigungsverhältnis ein. Beschäftigungsstatus und "
        "Arbeitgeberangaben widersprechen sich und sind manuell zu klären.",
        evidence,
        "Ist der Kunde angestellt oder selbstständig, und von wem stammt das Einkommen?")
    return "selbststaendig_gehalt_widerspruch", app, label


def main():
    rng = random.Random(SEED)
    data = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
    customers = data["kunden"]
    by_scenario = defaultdict(list)
    for c in customers:
        by_scenario[c["metadaten"]["szenario"]].append(c)
    next_variant = defaultdict(int)
    for c in customers:
        fam = c["metadaten"]["familie_id"]
        next_variant[fam] = max(next_variant[fam], c["metadaten"]["variante"] + 1)

    salary = rng.sample(by_scenario["gehalt_konsistent"], len(by_scenario["gehalt_konsistent"]))
    green_ok = [c for s in GREEN_OK_SCENARIOS for c in by_scenario[s]]
    plan = [
        (address_trigger_variant, rng.sample(green_ok, 400)),
        (reserves_neutral_address_variant, [c for c in by_scenario["adresse_reeperbahn_umfeld_pruefbedarf"] for _ in range(3)]),
        (reserves_documented_variant, rng.sample(by_scenario["selbststaendig_private_nutzung"], 150)),
        (employer_at_trigger_street_variant, salary[:100]),
        (self_employed_salary_variant, salary[100:300]),
    ]

    added = []
    skipped = 0
    for make, sources in plan:
        for source in sources:
            fam = source["metadaten"]["familie_id"]
            if next_variant[fam] > MAX_VARIANTS:
                skipped += 1
                continue
            scenario, application, label = make(source, rng)
            added.append({
                "kunden_id": f"SYN-KYC-{len(customers) + len(added) + 1:06d}",
                "metadaten": {"split": source["metadaten"]["split"], "familie_id": fam, "szenario": scenario,
                              "variante": next_variant[fam], "synthetisch": True},
                "eingabe": application,
                "sollbewertung": label,
            })
            next_variant[fam] += 1
    assert skipped == 0, f"{skipped} Varianten übersprungen (Familienlimit)"

    all_customers = customers + added
    data["kunden"] = all_customers
    meta = data["metadaten"]
    meta["name"] = meta["name"] + " (ergänzt um entkoppelte Varianten)"
    meta["schema_version"] = "1.1.0"
    meta["aktualisiert_am"] = "2026-10-03"
    meta["ergaenzung"] = ("1.000 abgeleitete Varianten (laya_kyc/augment_dataset.py): Wohnadresse im Reeperbahn-Umfeld bei "
                          "sonst unauffälligen Fällen aller Art, Rücklagenbestätigungen ohne Adressbezug, Arbeitgeber im "
                          "Reeperbahn-Umfeld sowie Widerspruch 'selbstständig, aber Gehalt und Arbeitgeberbestätigung'. "
                          "Varianten bleiben in Familie und Split der Vorlage.")
    meta["aufteilung"] = "Familien vollständig in einem Split; Varianten ab 6 sind abgeleitet."
    meta["statistik"] = statistics(all_customers)

    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    jsonschema.validate(data, schema)
    checks = validate(all_customers)

    TARGET_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    digest = hashlib.sha256(TARGET_FILE.read_bytes()).hexdigest()
    report = {"datei": TARGET_FILE.name, "sha256": digest, "groesse_bytes": TARGET_FILE.stat().st_size,
              "schema_valide": True, **checks, "statistik": meta["statistik"]}
    VALIDATION_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("sha256", "anzahl_kunden", "familien_in_mehreren_splits")}, ensure_ascii=False))
    print(json.dumps(meta["statistik"]["neue_szenarien"], ensure_ascii=False))
    print(json.dumps(meta["statistik"]["splits"], ensure_ascii=False))


def statistics(customers):
    splits = defaultdict(Counter)
    for c in customers:
        splits[c["metadaten"]["split"]][c["sollbewertung"]["entscheidung"]] += 1
    new = Counter(c["metadaten"]["szenario"] for c in customers if c["metadaten"]["variante"] > 5)
    return {
        "anzahl_kunden": len(customers),
        "splits": {s: dict(v) for s, v in sorted(splits.items())},
        "manuelle_pruefung": dict(Counter("Ja" if c["sollbewertung"]["manuelle_pruefung_erforderlich"] else "Nein" for c in customers)),
        "szenarien": dict(Counter(c["metadaten"]["szenario"] for c in customers)),
        "neue_szenarien": dict(new),
    }


def validate(customers):
    ids = [c["kunden_id"] for c in customers]
    assert len(ids) == len(set(ids)), "doppelte Kunden-IDs"
    texts = [K.case_text(c["eingabe"]) for c in customers]
    assert len(texts) == len(set(texts)), "doppelte Eingaben"
    family_splits = defaultdict(set)
    for c in customers:
        family_splits[c["metadaten"]["familie_id"]].add(c["metadaten"]["split"])
        label = c["sollbewertung"]
        assert label["manuelle_pruefung_erforderlich"] == (label["entscheidung"] != "keine_manuelle_pruefung")
        for evidence in label["belege"]:   # Belegpfade zeigen auf die tatsächlichen Werte der Eingabe
            value = c["eingabe"]
            for part in evidence["feld"].split("."):
                value = value[int(part)] if isinstance(value, list) else value[part]
            assert value == evidence["wert"], (c["kunden_id"], evidence["feld"])
    mixed = sum(len(s) > 1 for s in family_splits.values())
    assert mixed == 0, "Familie in mehreren Splits"
    return {"anzahl_kunden": len(customers), "eindeutige_ids": True, "eindeutige_eingaben": True,
            "belegpfade_geprueft": True, "familien_in_mehreren_splits": mixed}


if __name__ == "__main__":
    main()
