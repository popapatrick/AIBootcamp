"""Sursele de date ale API-ului (proprietar C). Date FICTIVE.

Ordinea de preferință, aleasă automat la fiecare cerere:
1. motorul real al lui B (`snapshot(data)`, `timeline()`) dacă există în `backend/engine/`;
2. fișierele reale ale lui B: `data/model/snapshots/<data>.geojson`, `data/model/timeline.json`;
3. eșantionul fals `data/model/sample/` (mod „stub").

`mod()` spune ce sursă e folosită, ca UI-ul și /health să arate clar dacă datele sunt stub.
"""
from __future__ import annotations

import importlib
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "data" / "model"
SNAP_DIR = MODEL_DIR / "snapshots"
SAMPLE_DIR = MODEL_DIR / "sample"

# Module din backend/engine în care căutăm funcțiile motorului (B nu a fixat încă numele).
_ENGINE_MODULES = ["backend.engine", "backend.engine.engine", "backend.engine.model",
                   "backend.engine.score", "backend.engine.scor", "backend.engine.decision",
                   "backend.engine.decizie", "backend.engine.timeline", "backend.engine.pipeline"]
_EXTRACT_MODULES = ["backend.extract", "backend.extract.extract", "backend.extract.extractie",
                    "backend.extract.claude"]


def _find(func: str, modules: list[str]):
    """Caută funcția `func` în lista de module; întoarce funcția sau None."""
    for name in modules:
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        f = getattr(mod, func, None)
        if callable(f):
            return f
    return None


def engine_func(name: str):
    """Funcție a motorului lui B (apply_event, snapshot, timeline, match_event) sau None."""
    if name == "match_event":
        return _find(name, ["backend.engine.match"] + _ENGINE_MODULES)
    return _find(name, _ENGINE_MODULES)


def extract_func():
    """`extract_event` al lui A sau None; `API_EXTRACTIE=stub` forțează extracția regex (teste, demo fără cheie)."""
    import os
    if os.environ.get("API_EXTRACTIE") == "stub":
        return None
    return _find("extract_event", _EXTRACT_MODULES)


def cache_hit(text: str, sursa: str, data: str | None) -> bool:
    """True dacă `extract_event` ar răspunde din cache (fără apel API). False dacă nu putem verifica."""
    try:
        from backend.extract import extract as ex
        return (ex.CACHE_DIR / f"{ex.cache_key(text, sursa, data)}.json").exists()
    except Exception:
        return False


def extractie_cod() -> str:
    """Modul curent de extracție: `ai_cli` | `ai_api` | `ai_cache` | `regex` (contracts/interfaces.md, metoda_cod)."""
    import os
    if not extract_func():
        return "regex"
    if os.environ.get("EXTRACT_ALLOW_API") == "1" and _are_cheie():
        return "ai_api"
    try:   # Claude Code headless, din abonament: texte noi standardizate cu AI, fără cheie
        from backend.extract import cli_ai
        if cli_ai.stare()["ok"]:
            return "ai_cli"
    except Exception:
        pass
    return "ai_cache"


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _snapshot_files() -> dict[str, Path]:
    """{data: fișier} din snapshots reale, altfel din eșantion."""
    for d in (SNAP_DIR, SAMPLE_DIR):
        files = {p.stem: p for p in sorted(d.glob("*.geojson"))} if d.is_dir() else {}
        if files:
            return files
    return {}


def _are_cheie() -> bool:
    """Există ANTHROPIC_API_KEY în mediu sau în .env (valoarea nu se citește mai departe)."""
    import os
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True
    env = Path(__file__).resolve().parents[2] / ".env"
    return env.is_file() and any(l.startswith("ANTHROPIC_API_KEY=") and l.strip().split("=", 1)[1]
                                 for l in env.read_text().splitlines())


def mod() -> dict:
    """Ce sursă folosește fiecare parte: motor | fisiere | stub."""
    if engine_func("snapshot"):
        retea = "motor"
    elif SNAP_DIR.is_dir() and any(SNAP_DIR.glob("*.geojson")):
        retea = "fisiere"
    else:
        retea = "stub"
    return {
        "retea": retea,
        "evenimente": "motor" if engine_func("timeline") else
                      ("fisiere" if (MODEL_DIR / "timeline.json").exists() else "stub"),
        "extractie": ("claude" if _are_cheie() else "stub (rezervă: cheie API lipsă)") if extract_func() else "stub",
        "motor": "real" if engine_func("apply_event") else
                 ("partial_match_event" if engine_func("match_event") else "stub"),
    }


def _azi() -> str:
    from datetime import date
    return date.today().isoformat()


def _date_motor() -> list[str]:
    """Datele evenimentelor din motor; fără evenimente încă, doar data de azi."""
    return sorted({e["data"] for e in evenimente()}) or [_azi()]


def date_disponibile() -> list[str]:
    """Datele pentru care avem instantanee (sortate)."""
    if engine_func("snapshot"):
        return _date_motor()
    return sorted(_snapshot_files())


def retea(data: str | None, scenariu: str | None = None) -> dict:
    """GeoJSON cu starea la `data` (sau cea mai recentă). Alege instantaneul cu data <= `data`."""
    if scenariu:
        m = model_extrem()
        data = data or max((j["data"] for j in m.jurnal), default=_azi())
        fc = m.snapshot(data)
        fc["data_instantaneu"] = data
        return fc
    snap = engine_func("snapshot")
    if snap:
        if data is None:
            data = _date_motor()[-1]
        fc = snap(data)
        fc["data_instantaneu"] = data
        return fc
    files = _snapshot_files()
    if not files:
        return {"type": "FeatureCollection", "features": []}
    dates = sorted(files)
    alese = [d for d in dates if data is None or d <= data] or [dates[0]]
    fc = _load(files[alese[-1]])
    fc["data_instantaneu"] = alese[-1]
    return fc


def evenimente(scenariu: str | None = None) -> list[dict]:
    """Lista pentru timeline: [{data, event_id, rezumat, elemente_atinse}], sortată după dată."""
    if scenariu:
        return sorted(model_extrem().timeline(), key=lambda e: e.get("data", ""))
    tl = engine_func("timeline")
    if tl:
        items = tl()
    else:
        p = MODEL_DIR / "timeline.json"
        items = _load(p) if p.exists() else (_load(SAMPLE_DIR / "timeline.json")
                                             if (SAMPLE_DIR / "timeline.json").exists() else [])
    return sorted(items, key=lambda e: e.get("data", ""))


def _id(props: dict) -> str | None:
    return props.get("element_id") or props.get("id")


def element(element_id: str) -> dict | None:
    """Starea curentă + istoricul elementului, din toate instantaneele, în ordine cronologică."""
    if engine_func("snapshot"):
        dates = _date_motor()
        snaps = [(d, engine_func("snapshot")(d)) for d in dates]
    else:
        snaps = [(d, _load(p)) for d, p in sorted(_snapshot_files().items())]
    istoric, curent, geom = [], None, None
    for d, fc in snaps:
        for f in fc.get("features", []):
            pr = f.get("properties", {})
            if _id(pr) == element_id:
                curent, geom = pr, f.get("geometry")
                istoric.append({"data": d, "nivel": pr.get("nivel"), "scor": pr.get("scor"),
                                "motive": pr.get("motive", [])})
                break
    if curent is None:
        return None
    return {**curent, "geometry": geom, "istoric": istoric}


@lru_cache(maxsize=1)
def model_net() -> dict | None:
    """Modelul curent al lui B (cu defecte), pentru match_event în modul parțial."""
    try:
        from backend.engine import defects
        return defects.build()["model"]
    except Exception:
        return None


# ---------------------------------------------------------------- scenariul extrem (sesiunea 2)
class ScenariuLipsa(Exception):
    """Fișierul scenariului nu există (se traduce în 404)."""


def model_extrem():
    """GridModel al scenariului extrem, din `engine.model_scenariu("extrem")` (B). Ridică ScenariuLipsa dacă fișierul lipsește."""
    from backend.engine import engine as eng
    try:
        return eng.model_scenariu("extrem")
    except FileNotFoundError as e:
        raise ScenariuLipsa(f"scenariul extrem nu există încă: {e}")


def ultima_actualizare(data: str | None, scenariu: str | None = None) -> str | None:
    """`ultima_actualizare` din statistici(data) al motorului; None dacă motorul nu o dă încă."""
    try:
        if scenariu:
            st = model_extrem().statistici(data or _azi())
        else:
            f = engine_func("statistici")
            st = f(data or _date_motor()[-1]) if f else {}
        return st.get("ultima_actualizare")
    except ScenariuLipsa:
        raise
    except Exception:
        return None


def raport_json(nume: str):
    """Conținutul `data/reports/<nume>` sau None dacă lipsește."""
    p = ROOT / "data" / "reports" / nume
    return _load(p) if p.is_file() else None


def geocodeaza_func():
    """`geocodeaza(referinta, strazi, cfg)` din backend.geo / motor (contracts/interfaces.md, sesiunea 3) sau None."""
    return _find("geocodeaza", ["backend.geo", "backend.geo.geocodare", "backend.geo.geocodeaza"] + _ENGINE_MODULES)


def zona() -> dict | None:
    """Zona prototipului {centru: {lat, lon}, raza_m}: din `engine.zona.zona_ok` dacă există (B1), altfel centroidul
    nodurilor rețelei de start + `zona.raza_max_m` din weights.yaml. None dacă lipsește modelul sau configurația."""
    import yaml
    net = model_net()
    cfg = yaml.safe_load((ROOT / "contracts" / "weights.yaml").read_text(encoding="utf-8"))
    if not net or "zona" not in cfg:
        return None
    n = list(net["noduri"].values())
    f = _find("zona_ok", ["backend.engine.zona"])
    if f and n:
        try:
            r = f(n[0]["lat"], n[0]["lon"], net, cfg)
            return {"centru": r["centru"], "raza_m": r["raza_m"]}
        except Exception:
            pass
    if not n:
        return None
    return {"centru": {"lat": round(sum(x["lat"] for x in n) / len(n), 7),
                       "lon": round(sum(x["lon"] for x in n) / len(n), 7)},
            "raza_m": cfg["zona"]["raza_max_m"]}
