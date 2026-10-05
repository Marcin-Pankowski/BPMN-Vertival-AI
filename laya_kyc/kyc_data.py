"""KYC-Datenaufbereitung für Laya Multilingual.

Gemeinsame Grundlage für Training, Evaluation, Demo und Laya-Dienst:
- kompakte, deterministische Darstellung von `eingabe` als `pfad: wert`-Zeilen
  (Pfade entsprechen den Belegpfaden in `sollbewertung.belege`),
- die fiktive Demo-Richtlinie als fester Textvorspann,
- die Laya-Frage mit den drei Antwortoptionen.

Nur `eingabe` geht in den Modellinput. Metadaten, Szenario und Sollbewertung bleiben draußen.
Die Feldnamen des Datensatzes (deutsch) sind Teil des Modelleingabetexts und bleiben unverändert.
"""
import json
from pathlib import Path

import torch

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "KYC_Trainingsdaten_5000.json"
BASE_MODEL = PROJECT_DIR / "modelle" / "laya-multilingual-base"

# Reihenfolge = Klassenindex der Zielverteilung. Die Werte sind die trainierten Modellklassen.
OPTIONS = ["keine_manuelle_pruefung", "manuelle_pruefung", "unklar"]

QUESTION = {
    "t": "choice",
    "ins": (
        "Prüfe den KYC-Antrag nach der Demo-Richtlinie: Ist eine manuelle Prüfung "
        "vor der Kontoanlage erforderlich?"
    ),
    "crit": {
        "keine_manuelle_pruefung": "kein Regeltrigger, Angaben und Nachweise konsistent",
        "manuelle_pruefung": "Regeltrigger R1-R3 oder konkreter Widerspruch bzw. Klärungsbedarf",
        "unklar": "entscheidungsrelevante Angaben oder Nachweise fehlen",
    },
}

# Dieselbe Frage im Format der öffentlichen Laya-API (`Agent.predict_batch`).
QUESTION_API = {"type": "choice", "instructions": QUESTION["ins"], "criteria": QUESTION["crit"]}

# Konstante Prozessangaben: Voraussetzung für die Aufnahme, kein Lernmerkmal.
EXCLUDED_FIELDS = {"prozessphase", "identitaetspruefung"}

POLICY_TEXT = (
    "Demo-Richtlinie (fiktiv). Regeln mit manueller Prüfung: R1 Kunde nicht selbst "
    "wirtschaftlich berechtigt; R2 PEP Ja; R3 möglicher Screening-Treffer ungeklärt. "
    "Auch bei grünen Regeln manuell: Privatkonto mit geplanter Geschäftsnutzung; "
    "Widerspruch zwischen Mittelherkunft und Unterlage; Widerspruch zum Vermögensaufbau; "
    "unzureichend erläuterte Schenkung; widersprüchliche Arbeitgeber-, US-/FATCA- oder "
    "Auslandswohnsitzangaben; Wohnadresse an Reeperbahn, Große Freiheit, Davidstraße oder "
    "Spielbudenplatz in Hamburg (PLZ allein kein Auslöser). Kein Auslöser: Selbstständigkeit "
    "mit privater Nutzung, hohe Einzahlung mit konsistenter Herkunft, konsistenter US-Status "
    "oder Auslandswohnsitz, kein Arbeitgeber bei Selbstständigkeit oder Ruhestand. Fehlen "
    "entscheidungsrelevante Angaben: unklar."
)

# Feste Feldreihenfolge je Objektpfad, wie in allen Trainingsdaten. Das Modell reagiert stark auf
# die Reihenfolge der Zeilen; JSON-Objekte aus anderen Systemen (z. B. Kogito) dürfen ihre Felder
# daher nicht in eigener Reihenfolge durchreichen. Unbekannte Felder folgen alphabetisch.
FIELD_ORDER = {
    "": ["prozessphase", "identitaetspruefung", "kunde", "beschaeftigung",
         "entstehung_gesamtvermoegen_freitext", "mittelherkunft", "steuerangaben", "screening",
         "kontoantrag", "eingereichte_unterlagen", "regelpruefung"],
    "identitaetspruefung": ["status", "datum", "verfahren"],
    "kunde": ["vorname", "nachname", "geburtsdatum", "staatsangehoerigkeiten", "adresse",
              "ist_selbst_wirtschaftlich_berechtigt", "auslandswohnsitz", "auslandsadressen"],
    "kunde.adresse": ["plz", "strasse", "hausnummer", "ort", "land"],
    "kunde.auslandsadressen[]": ["plz", "strasse", "hausnummer", "ort", "land"],
    "beschaeftigung": ["status", "beruf", "nettoeinkommen_monat_eur_laut_kunde", "arbeitgeber"],
    "beschaeftigung.arbeitgeber": ["name", "plz", "strasse", "hausnummer", "ort", "land"],
    "mittelherkunft": ["kategorie", "beschreibung_freitext", "geplante_ersteinzahlung_eur"],
    "steuerangaben": ["us_steuerpflicht_laut_selbstauskunft", "fatca_us_person_laut_selbstauskunft",
                      "steuerliche_ansaessigkeit_laut_selbstauskunft", "erlaeuterung_freitext",
                      "selbstauskunft_vorhanden"],
    "screening": ["pep", "pep_erlaeuterung", "sanktionsscreening_status", "screening_erlaeuterung"],
    "kontoantrag": ["kontotyp", "kontozweck", "geplante_nutzung_freitext"],
    "eingereichte_unterlagen[]": ["dokument_id", "typ", "textauszug"],
    "regelpruefung": ["ergebnis", "ausgeloeste_regeln"],
}


def load_customers(path=DATA_FILE):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["kunden"]


def _format_value(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _ordered_keys(obj, schema_path):
    known = FIELD_ORDER.get(schema_path, [])
    rank = {key: i for i, key in enumerate(known)}
    return sorted(obj, key=lambda key: (rank.get(key, len(known)), key))


def _flatten(obj, prefix, schema_path, lines):
    if isinstance(obj, dict):
        for key in _ordered_keys(obj, schema_path):
            _flatten(obj[key], f"{prefix}.{key}" if prefix else key,
                     f"{schema_path}.{key}" if schema_path else key, lines)
    elif isinstance(obj, list):
        if not obj:
            lines.append(f"{prefix}: []")
        elif all(not isinstance(x, (dict, list)) for x in obj):
            lines.append(f"{prefix}: " + ", ".join(_format_value(x) for x in obj))
        else:
            for i, x in enumerate(obj):
                _flatten(x, f"{prefix}.{i}", schema_path + "[]", lines)
    else:
        lines.append(f"{prefix}: {_format_value(obj)}")


def case_text(application):
    """Kompakte Darstellung des Falls ohne Richtlinie, unabhängig von der JSON-Feldreihenfolge."""
    lines = []
    for key in _ordered_keys(application, ""):
        if key not in EXCLUDED_FIELDS:
            _flatten(application[key], key, key, lines)
    return "\n".join(lines)


def model_state(application):
    """Vollständiger Modellzustand: Richtlinie + Fall."""
    return POLICY_TEXT + "\n\nAntrag:\n" + case_text(application)


def target_index(customer):
    return OPTIONS.index(customer["sollbewertung"]["entscheidung"])


def has_rule_trigger(application):
    return application["regelpruefung"]["ergebnis"] != "Gruen"


def has_us_nexus(application):
    """Regel R4 (nach dem Training eingeführt, nur im Prozess): USA-Bezug erzwingt manuelle Prüfung.

    Spiegelt die DMN-Tabelle KYC_RuleCheck. `regelpruefung` im Modellinput enthält weiterhin nur R1–R3.
    """
    person = application.get("kunde") or {}
    tax = application.get("steuerangaben") or {}
    return (tax.get("us_steuerpflicht_laut_selbstauskunft") == "Ja"
            or tax.get("fatca_us_person_laut_selbstauskunft") == "Ja"
            or "US" in (person.get("staatsangehoerigkeiten") or [])
            or "US" in (tax.get("steuerliche_ansaessigkeit_laut_selbstauskunft") or [])
            or (person.get("adresse") or {}).get("land") == "US"
            or any(a.get("land") == "US" for a in person.get("auslandsadressen") or []))


def build_items(tokenizer, customers, max_len=1024, head_max_len=256):
    """Tokenisierte Laya-Items. Bricht ab, falls ein Fall abgeschnitten würde."""
    from laya.common import QTYPES, build_sequence

    items = []
    for customer in customers:
        ids, markers, truncation = build_sequence(
            tokenizer, model_state(customer["eingabe"]), QUESTION, max_len, head_max_len,
            return_truncation_stats=True,
        )
        if truncation["truncated"] or len(markers) != len(OPTIONS):
            raise ValueError(f"{customer['kunden_id']}: Eingabe passt nicht vollständig ins Limit ({truncation})")
        target = target_index(customer)
        items.append({
            "ids": ids,
            "markers": markers,
            "qtype": QTYPES["choice"],
            "target": [1.0 if i == target else 0.0 for i in range(len(OPTIONS))],
            "label": target,
            "customer_id": customer["kunden_id"],
        })
    return items


def collate(items, pad_id):
    n, length = len(items), max(len(it["ids"]) for it in items)
    ids = torch.full((n, length), pad_id, dtype=torch.long)
    attention = torch.zeros((n, length), dtype=torch.long)
    for i, it in enumerate(items):
        ids[i, : len(it["ids"])] = torch.tensor(it["ids"], dtype=torch.long)
        attention[i, : len(it["ids"])] = 1
    return {
        "input_ids": ids,
        "attention_mask": attention,
        "marker_pos": torch.tensor([it["markers"] for it in items]),
        "marker_mask": torch.ones((n, len(OPTIONS)), dtype=torch.bool),
        "qtype": torch.tensor([it["qtype"] for it in items]),
        "target": torch.tensor([it["target"] for it in items]),
    }


@torch.no_grad()
def option_logits(model, items, pad_id, device, batch_size=8):
    """Rohe Optionslogits (ohne Temperatur), Reihenfolge wie `OPTIONS`."""
    model.eval()
    out = []
    for start in range(0, len(items), batch_size):
        batch = collate(items[start:start + batch_size], pad_id)
        logits, _ = model(batch["input_ids"].to(device), batch["attention_mask"].to(device),
                          batch["marker_pos"].to(device), batch["marker_mask"].to(device),
                          batch["qtype"].to(device))
        out.append(logits.float().cpu())
    return torch.cat(out)
