"""API FastAPI (etapa 7, proprietar C). Implementează contracts/api.openapi.yaml. Date FICTIVE.

Pornire:
    .venv/bin/uvicorn backend.api.main:app --reload --port 8000

Endpoint-uri: /health, POST /rapoarte, GET /retea?data=, GET /evenimente, GET /element/{id}.
În plus: /ui = UI plan B (Leaflet), /date = datele instantaneelor disponibile.
"""
from __future__ import annotations

from datetime import date as _date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.api import pipeline, sources

app = FastAPI(title="Grid model API (prototip, date fictive)", version="0.1.0")

# Lovable rulează pe alt domeniu și apelează API-ul prin tunel: CORS deschis (prototip, date fictive).
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

NOTA = "date fictive, rețea demonstrativă"


class Raport(BaseModel):
    text: str
    sursa: Literal["mentenanta", "investitii", "racordari", "apel_client"]
    data: _date | None = None


@app.get("/health")
def health() -> dict:
    """{"status": "ok", "mod": {...}} — `mod` arată dacă fiecare parte e stub sau reală."""
    out = {"status": "ok", "mod": sources.mod(), "nota": NOTA}
    f = sources.engine_func("sursa_evenimente")
    if f:
        out["sursa_evenimente"] = f()
    return out


@app.post("/rapoarte")
def rapoarte(r: Raport) -> dict:
    """Procesează un raport nou; întoarce StepTrace (extracție, potrivire, predicție, scor)."""
    if not r.text.strip():
        raise HTTPException(422, "text gol")
    return pipeline.proceseaza(r.text, r.sursa, r.data.isoformat() if r.data else None)


@app.get("/retea")
def retea(data: _date | None = Query(None)) -> dict:
    """GeoJSON FeatureCollection cu starea la `data`; properties = ElementState."""
    d = data.isoformat() if data else None
    fc = sources.retea(d)
    fc = pipeline.live_overlay(fc, d)
    fc["nota"] = NOTA
    return fc


@app.get("/evenimente")
def evenimente() -> list[dict]:
    """Lista pentru timeline, sortată după dată (include rapoartele live din sesiune)."""
    return sorted(sources.evenimente() + pipeline.live_evenimente(), key=lambda e: e.get("data", ""))


@app.get("/date")
def date_disponibile() -> list[str]:
    """Datele instantaneelor disponibile (ajută timeline-ul)."""
    return sources.date_disponibile()


@app.get("/element/{element_id}")
def element(element_id: str) -> dict:
    """ElementState curent + `istoric` [{data, nivel, scor, motive}] + geometrie."""
    el = pipeline.live_element(element_id) or sources.element(element_id)
    if el is None:
        raise HTTPException(404, f"element necunoscut: {element_id}")
    return el


_UI = Path(__file__).resolve().parents[2] / "frontend" / "plan-b"
if _UI.is_dir():
    app.mount("/ui", StaticFiles(directory=_UI, html=True), name="ui")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/ui/" if _UI.is_dir() else "/docs")
