"""Interfața publică a motorului (contracts/interfaces.md). Folosită de API (C).

    from backend.engine.engine import apply_event, snapshot, timeline, statistici, reset

Un singur model în memorie. La prima folosire reia evenimentele din `data/events/events.json`
(altfel `events.stub.json`, dacă există), în ordinea datelor. Date FICTIVE.
"""
from __future__ import annotations

import json
from pathlib import Path

from backend.engine import osm
from backend.engine.model import GridModel, ROOT

EVENTS = ROOT / "data" / "events"
_model: GridModel | None = None


FALLBACK = ROOT / "data" / "model" / "events.fallback.json"
_sursa = ["niciuna"]


def _incarca_evenimente() -> list[dict]:
    """events.json (A), apoi events.stub.json (A), apoi rezerva lui B (sintetică, doar cât lipsesc ale lui A)."""
    for cale, nume in ((EVENTS / "events.json", "events.json"), (EVENTS / "events.stub.json", "events.stub.json"),
                       (FALLBACK, "rezerva_B")):
        if cale.exists():
            ev = json.loads(cale.read_text(encoding="utf-8"))
            if ev:
                _sursa[0] = nume
                return sorted(ev, key=lambda e: (e["data"], e["event_id"]))
    return []


def sursa_evenimente() -> str:
    """De unde vin evenimentele reluate: events.json | events.stub.json | rezerva_B | niciuna."""
    get_model()
    return _sursa[0]


def get_model() -> GridModel:
    global _model
    if _model is None:
        _model = GridModel()
        _model.traseu_fn = osm.traseu_fn()      # None dacă lipsește cache-ul de străzi: linii drepte
        for ev in _incarca_evenimente():
            _model.apply_event(ev)
    return _model


def reset() -> None:
    """Șterge modelul din memorie; următorul apel îl reconstruiește din evenimente."""
    global _model
    _model = None


def apply_event(event: dict) -> dict:
    """Aplică un Event pe model, întoarce StepTrace."""
    return get_model().apply_event(event)


def snapshot(data: str) -> dict:
    return get_model().snapshot(data)


def timeline() -> list[dict]:
    return get_model().timeline()


def statistici(data: str) -> dict:
    return get_model().statistici(data)


def aplica_decizie(event: dict) -> dict:
    """Decizia omului asupra unei predicții (B4). `event` = Event `verificare` cu `echipa_sursa: om_teren` și
    `detalii.decizie {tinta_id, decizie}`. Întoarce StepTrace; ridică KeyError (predicție necunoscută),
    ValueError (deja decisă sau decizie invalidă), cum așteaptă `backend/api/pipeline.py`."""
    trace = get_model().apply_event(event)
    err = trace.get("eroare")
    if err:
        if err["cod"] == "necunoscut":
            raise KeyError(err["mesaj"])
        raise ValueError(err["mesaj"])
    return trace


def jurnal() -> list[dict]:
    return get_model().jurnal
