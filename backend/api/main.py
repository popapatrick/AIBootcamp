"""API FastAPI (etapa 7, proprietar C). Implementează contracts/api.openapi.yaml. Date FICTIVE.

Pornire:
    .venv/bin/uvicorn backend.api.main:app --reload --port 8000

Endpoint-uri: /health, POST /rapoarte, GET /retea?data=, GET /evenimente, GET /element/{id}.
Sesiunea 4: POST /element/{id}/verificare, GET /demo/exemple, POST /demo/reset, GET /legenda.
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

from backend.api import pipeline, prezentare, sources

app = FastAPI(title="Grid model API (prototip, date fictive)", version="0.1.0")

# Lovable rulează pe alt domeniu și apelează API-ul prin tunel: CORS deschis (prototip, date fictive).
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

NOTA = "date fictive, rețea demonstrativă"


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


class Raport(BaseModel):
    text: str
    sursa: Literal["mentenanta", "investitii", "racordari", "apel_client"]
    data: _date | None = None
    locatie: Coord | None = None          # clic pe hartă (cerere_racordare, mutare_fire)
    locatie_operator: LocatieOperator | None = None   # cerere_racordare fără coordonate și fără clic


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
                              r.locatie.model_dump() if r.locatie else None,
                              r.locatie_operator.model_dump(exclude_none=True) if r.locatie_operator else None)


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
def retea(data: _date | None = Query(None)) -> dict:
    """GeoJSON FeatureCollection cu starea la `data`; properties = ElementState.

    Sesiunea 4: fiecare feature are `banda`, `verificat_om`, `sursa_locatie`, `t0` (null cât timp motorul nu le dă,
    altfel neatinse) și `eticheta_origine` („GIS” / „Din raport”, din `origine`). `ultima_actualizare`: din motor.
    """
    d = data.isoformat() if data else None
    fc = sources.retea(d)
    fc = pipeline.live_overlay(fc, d)
    for f in fc.get("features", []):
        p = f.setdefault("properties", {})
        for k in ("banda", "verificat_om", "sursa_locatie", "t0"):
            p.setdefault(k, None)
        p["eticheta_origine"] = prezentare.eticheta_origine(p.get("origine"))
    fc["ultima_actualizare"] = sources.ultima_actualizare(d or fc.get("data_instantaneu"))
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
def evenimente() -> list[dict]:
    """Lista pentru timeline, sortată după dată (include rapoartele live din sesiune).

    Sesiunea 4: pe fiecare intrare `text_original`, `echipa` (etichetă), `standardizare`, `focus`, `banda_inainte`,
    `banda_dupa` (null dacă motorul nu le dă încă).
    """
    items = sorted(sources.evenimente() + pipeline.live_evenimente(), key=lambda e: e.get("data", ""))
    return pipeline.imbogateste_evenimente(items)


@app.get("/exemple")
def exemple(sursa: Literal["mentenanta", "investitii", "racordari"]) -> list[dict]:
    """Texte dummy pentru „Generează exemplu" din data/reports/exemple-dummy.json; [] dacă fișierul lipsește."""
    d = sources.raport_json("exemple-dummy.json") or []
    if isinstance(d, dict):   # acceptăm și {sursa: [...]}
        d = d.get(sursa, [])
    return [x for x in d if not isinstance(x, dict) or x.get("sursa", sursa) == sursa]


@app.get("/demo/exemple")
def demo_exemple() -> list[dict]:
    """Cardurile paginii de intro din data/reports/demo-intro.json; [] dacă fișierul lipsește (încă nu e scris)."""
    return sources.raport_json("demo-intro.json") or []


@app.post("/demo/reset")
def demo_reset() -> dict:
    """Modelul revine la starea de start (evenimentele scenariului reluate), rapoartele live se șterg. 501 fără motor."""
    try:
        return {"status": "ok", "evenimente": pipeline.reset()}
    except NotImplementedError as e:
        raise HTTPException(501, str(e))


@app.get("/legenda")
def legenda() -> dict:
    """Benzi de culoare (din weights.culori), stiluri de linie și insigne, cu texte în română."""
    return prezentare.legenda()


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


class Verificare(BaseModel):
    motiv: str | None = None
    data: _date | None = None


@app.post("/element/{element_id}/verificare")
def verificare(element_id: str, v: Verificare | None = None) -> dict:
    """Un om marchează elementul verificat (eveniment `verificare_om`). Întoarce StepTrace.
    404 element necunoscut; 501 cât timp motorul nu are `verificare_om` (V5)."""
    v = v or Verificare()
    try:
        return pipeline.verificare(element_id, v.motiv, v.data.isoformat() if v.data else None)
    except pipeline.ElementLipsa as e:
        raise HTTPException(404, str(e))
    except NotImplementedError as e:
        raise HTTPException(501, str(e))


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
