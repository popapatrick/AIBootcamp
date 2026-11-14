"""Interfața publică a motorului (contracts/interfaces.md). Folosită de API (C).

    from backend.engine.engine import apply_event, snapshot, timeline, statistici, reset

Un singur model în memorie. La prima folosire reia evenimentele din `data/events/events.json`
(altfel `events.stub.json`, dacă există), în ordinea datelor. Date FICTIVE.
"""
from __future__ import annotations

import json
from pathlib import Path

from backend.engine.model import GridModel, ROOT

EVENTS = ROOT / "data" / "events"
_model: GridModel | None = None


def _incarca_evenimente() -> list[dict]:
    for nume in ("events.json", "events.stub.json"):
        p = EVENTS / nume
        if p.exists():
            return sorted(json.loads(p.read_text(encoding="utf-8")), key=lambda e: (e["data"], e["event_id"]))
    return []


def get_model() -> GridModel:
    global _model
    if _model is None:
        _model = GridModel()
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


def jurnal() -> list[dict]:
    return get_model().jurnal
