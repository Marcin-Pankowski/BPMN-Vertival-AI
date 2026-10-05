"""REST-Dienst für die LLM-Prüfung im KYC-Prozess (BPMN-Task „Prüfung mit LLM“).

Lädt das angepasste Laya-Modell einmal beim Start und bewertet je Aufruf einen Antrag.
`application` ist `eingabe` im Schema der Trainingsdaten, einschließlich des vom Prozess
berechneten `regelpruefung`-Ergebnisses.

Start:
    cd laya_kyc && ../.venv/bin/uvicorn laya_service:app --port 8000

Umgebungsvariablen: LAYA_MODEL (Pfad), LAYA_DEVICE (mps, cpu; Standard: mps falls verfügbar).
"""
import os
import time
import warnings
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import laya

import kyc_data as K

MODEL_PATH = os.environ.get("LAYA_MODEL", str(K.PROJECT_DIR / "modelle" / "laya-multilingual-kyc-v2"))
DEVICE = os.environ.get("LAYA_DEVICE")
# Trainiert mit 1.024 Tokens; längere Anträge werden nicht abgeschnitten (siehe kyc_demo.py).
MAX_LEN = 2048
REQUIRED_FIELDS = ("kunde", "beschaeftigung", "mittelherkunft", "steuerangaben", "screening",
                   "kontoantrag", "eingereichte_unterlagen", "regelpruefung")

state = {}


@asynccontextmanager
async def lifespan(_app):
    warnings.filterwarnings("ignore")
    state["agent"] = laya.load(MODEL_PATH, device=DEVICE)
    yield
    state.clear()


app = FastAPI(title="Laya KYC-Bewertung", version="1.1.0", lifespan=lifespan)


class AssessmentRequest(BaseModel):
    application: Dict[str, Any]


class Assessment(BaseModel):
    decision: str
    manual_review_recommended: bool
    probabilities: Dict[str, float]
    model: str
    tokens: int
    duration_ms: int


@app.get("/health")
def health():
    agent = state.get("agent")
    return {"status": "ok" if agent else "loading", "model": MODEL_PATH,
            "device": str(agent.device) if agent else None}


@app.post("/assessment", response_model=Assessment)
def assessment(request: AssessmentRequest):
    missing = [f for f in REQUIRED_FIELDS if f not in request.application]
    if missing:
        raise HTTPException(422, f"Pflichtfelder fehlen im Antrag: {', '.join(missing)}")
    start = time.perf_counter()
    result = state["agent"].predict_batch([K.model_state(request.application)],
                                          {"entscheidung": K.QUESTION_API}, max_len=MAX_LEN)[0]
    if result["usage"]["truncated"]:
        # Nicht still abschneiden: Der Prozess behandelt den Fehler als manuellen Prüfbedarf.
        raise HTTPException(413, "Antrag passt nicht vollständig in das Eingabelimit")
    answer = result["answers"]["entscheidung"]
    return Assessment(
        decision=answer["choice"],
        manual_review_recommended=answer["choice"] != "keine_manuelle_pruefung",
        probabilities=answer["probabilities"],
        model=os.path.basename(MODEL_PATH),
        tokens=result["usage"]["input_tokens"],
        duration_ms=round((time.perf_counter() - start) * 1000),
    )
