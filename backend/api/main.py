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
Scenariu = Literal["extrem"] | None


def _sc(f):
    """Rulează f(); scenariul lipsă devine 404 clar."""
    try:
        return f()
    except sources.ScenariuLipsa as e:
        raise HTTPException(404, str(e))


class Coord(BaseModel):
    lat: float
    lon: float


class LocatieOperator(BaseModel):
    """Poziția SIMULATĂ a operatorului (de la GET /locatie-operator-demo). `simulata` nu poate fi false."""
    lat: float
    lon: float
    precizie_m: float | None = None
    simulata: Literal[True] = True
    zona: str | None = None


class TraceParams(BaseModel):
    """Parametri de generare a traseului simulat (contracts: detalii.trace_params); suprascriu weights.trace_generat."""
    puncte: float | None = None
    zgomot_m: float | None = None
    durata_oprire_min: float | None = None
    acoperire: float | None = None
    decalaj_m: float | None = None
    dezactivat: bool | None = None       # fără traseu generat pentru acest raport (motorul îl respectă)


class Raport(BaseModel):
    text: str
    sursa: Literal["mentenanta", "investitii", "racordari", "apel_client"]
    data: _date | None = None
    locatie: Coord | None = None          # clic pe hartă (cerere_racordare, mutare_fire)
    trace: list[dict] | None = None       # traseul tabletei: [{t, lat, lon}]
    locatie_operator: LocatieOperator | None = None   # cerere_racordare fără coordonate și fără clic
    trace_params: TraceParams | None = None           # reglaje traseu simulat; intră în detalii.trace_params


class Decizie(BaseModel):
    decizie: Literal["accepta", "respinge"]
    motiv: str | None = None
    data: _date | None = None


@app.get("/health")
def health() -> dict:
    """{"status": "ok", "mod": {...}} — `mod` arată dacă fiecare parte e stub sau reală."""
    out = {"status": "ok", "mod": sources.mod(), "nota": NOTA, "extractie_cod": sources.extractie_cod()}
    f = sources.engine_func("sursa_evenimente")
    if f:
        out["sursa_evenimente"] = f()
    out["ultima_actualizare"] = sources.ultima_actualizare(None)   # null până o dă motorul (B3)
    return out


@app.post("/rapoarte")
def rapoarte(r: Raport) -> dict:
    """Procesează un raport nou; întoarce StepTrace (extracție, potrivire, predicție, scor)."""
    if not r.text.strip():
        raise HTTPException(422, "text gol")
    return pipeline.proceseaza(r.text, r.sursa, r.data.isoformat() if r.data else None,
                              r.locatie.model_dump() if r.locatie else None, r.trace,
                              r.locatie_operator.model_dump(exclude_none=True) if r.locatie_operator else None,
                              r.trace_params.model_dump(exclude_none=True) if r.trace_params else None)


@app.get("/locatie-operator-demo")
def locatie_operator_demo(text: str | None = Query(None, description="descrierea operatorului (strada, colț, cartier)"),
                          adresa: str | None = Query(None, description="alias pentru `text`"),
                          lat: float | None = Query(None), lon: float | None = Query(None)) -> dict:
    """Poziție GPS DUMMY a operatorului, din textul lui, în zona descrisă (determinist). `simulata` e mereu true.
    Întoarce {lat, lon, precizie_m, simulata, strada, motiv, indicii: [{tip, valoare, gasit}], zona}.
    422 dacă lipsește textul sau niciun indiciu nu se găsește în datele locale (`detail` = {mesaj, indicii})."""
    t = (text or adresa or "").strip()
    if not t:
        raise HTTPException(422, {"mesaj": "lipsește `text` (descrierea operatorului)", "indicii": []})
    try:
        return pipeline.locatie_operator(t, lat, lon)
    except pipeline.LocalizareEroare as e:
        raise HTTPException(422, {"mesaj": str(e), "indicii": e.indicii})


@app.get("/retea")
def retea(data: _date | None = Query(None), scenariu: Scenariu = Query(None)) -> dict:
    """GeoJSON FeatureCollection cu starea la `data`; properties = ElementState.

    `?scenariu=extrem`: scenariul din data/events/events.extreme.json (404 dacă lipsește).
    `ultima_actualizare`: din motor (null până îl dă B).
    """
    d = data.isoformat() if data else None
    fc = _sc(lambda: sources.retea(d, scenariu))
    if not scenariu:
        fc = pipeline.live_overlay(fc, d)
    fc["ultima_actualizare"] = _sc(lambda: sources.ultima_actualizare(d or fc.get("data_instantaneu"), scenariu))
    fc["nota"] = NOTA
    z = sources.zona()
    if z:
        fc["zona"] = z   # safeguard prototip: {centru:{lat,lon}, raza_m}
    return fc


@app.get("/geocodeaza")
def geocodeaza(adresa: str = Query(..., description="adresă text, ex. „Strada Liviu Rebreanu 12”")) -> dict:
    """Depanare: geocodarea motorului (backend.geo, A1/B2) pe o adresă. 501 dacă funcția nu există încă;
    întoarce {status, lat, lon, precizie_m, metoda, acuratete, motiv} cum o dă funcția."""
    f = sources.geocodeaza_func()
    if f is None:
        raise HTTPException(501, "geocodarea nu e încă în motor (B2/A1)")
    from backend.engine import osm
    return f({"adresa": adresa, "adresa_structurata": None}, osm.strazi(), pipeline._weights())


@app.get("/reguli")
def reguli() -> dict:
    """Read-only: conținutul contracts/weights.yaml (ponderi, praguri, zona, geocodare etc.) ca JSON."""
    return pipeline._weights()


@app.get("/evenimente")
def evenimente(scenariu: Scenariu = Query(None)) -> list[dict]:
    """Lista pentru timeline, sortată după dată (include rapoartele live din sesiune).

    `?scenariu=extrem`: scenariul extrem (fără rapoarte live); 404 dacă fișierul lipsește.
    """
    live = [] if scenariu else pipeline.live_evenimente()
    return sorted(_sc(lambda: sources.evenimente(scenariu)) + live, key=lambda e: e.get("data", ""))


@app.get("/exemple")
def exemple(sursa: Literal["mentenanta", "investitii", "racordari", "apel_client"]) -> list[dict]:
    """Texte dummy pentru „Generează exemplu" din data/reports/exemple-dummy.json; [] dacă fișierul lipsește."""
    d = sources.raport_json("exemple-dummy.json") or []
    if isinstance(d, dict):   # acceptăm și {sursa: [...]}
        d = d.get(sursa, [])
    return [x for x in d if not isinstance(x, dict) or x.get("sursa", sursa) == sursa]


@app.get("/trasee-demo")
def trasee_demo() -> list[dict]:
    """Trasee GPS dummy din data/reports/trasee-dummy.json; [] dacă fișierul lipsește."""
    return sources.raport_json("trasee-dummy.json") or []


@app.post("/predictii/{pred_id}/decizie")
def decizie(pred_id: str, d: Decizie) -> dict:
    """Decizia omului (accepta/respinge) asupra unei predicții, prin `apply_event` (B4). Întoarce StepTrace.
    404 necunoscută; 409 deja decisă; 400 decizie invalidă; 501 fără motor real."""
    try:
        return pipeline.decizie(pred_id, d.decizie, d.motiv, d.data.isoformat() if d.data else None)
    except NotImplementedError as e:
        raise HTTPException(501, str(e))
    except pipeline.DecizieEroare as e:
        raise HTTPException({"necunoscut": 404, "deja_decis": 409}.get(e.cod, 400), f"{e.cod}: {e}")


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
