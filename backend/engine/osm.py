"""Etapa 6: traseul probabil al unui cablu pe stradă, din străzi OpenStreetMap (descărcate o singură dată).

`data/model/osm/streets_raw.json` = răspunsul Overpass (`way[highway]` în zona rețelei, © contribuitorii
OpenStreetMap, licența ODbL). Rutarea e locală, fără internet.

    traseu((lat, lon), (lat, lon)) -> {"puncte": [(lat, lon), ...], "urmeaza_strada": 0-1, ...} | None

`urmeaza_strada` = cât de probabil e ca un cablu între cele două puncte să urmeze strada:
  0,5 × apropierea capetelor de stradă (1 la 0 m, 0 la ≥ 30 m)
  0,5 × cât de scurt e ocolul pe stradă față de linia dreaptă (1 până la 1,3×, 0 la ≥ 2,5×)
Dacă nu avem stradă aproape (> 40 m) sau drum rezonabil, întoarce None și motorul rămâne pe linie dreaptă.
Date FICTIVE pentru rețea; străzile sunt reale.

Refacerea cache-ului (necesită internet): python -m backend.engine.osm --fetch
"""
from __future__ import annotations

import heapq
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

from backend.engine.network import dist_m

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "model" / "osm" / "streets_raw.json"
BBOX = (44.2742, 26.0577, 44.2868, 26.0714)       # sud, vest, nord, est (rețeaua ± ~150 m)
SNAP_MAX_M = 40.0
EXCLUDE = {"footway", "path", "steps", "cycleway", "pedestrian", "track", "trunk", "motorway"}
# trunk/motorway: nu trec cabluri de JT pe carosabilul principal; le excludem din rutare.


def fetch() -> None:
    """Descarcă o dată străzile din Overpass în cache (cu reîncercări)."""
    import subprocess
    import time
    q = f'[out:json][timeout:50];way["highway"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});out geom tags;'
    RAW.parent.mkdir(parents=True, exist_ok=True)
    for url in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"):
        for _ in range(3):
            subprocess.run(["curl", "-s", "-m", "70", "-A", "grid-model-hackathon-prototype",
                            "--data-urlencode", f"data={q}", url, "-o", str(RAW)], check=False)
            if RAW.exists() and RAW.read_text(encoding="utf-8")[:1] == "{":
                return
            time.sleep(8)
    raise RuntimeError("Overpass indisponibil; reîncearcă mai târziu")


def _k(lat: float, lon: float) -> tuple[float, float]:
    return (round(lat, 7), round(lon, 7))


@lru_cache(maxsize=1)
def _graf() -> tuple[dict, dict]:
    """(adiacență, segmente). adiacență[u] = [(v, lungime_m)], segmente = [(u, v)]."""
    d = json.loads(RAW.read_text(encoding="utf-8"))
    adj: dict[tuple, list] = {}
    seg: list[tuple] = []
    for e in d["elements"]:
        if e.get("type") != "way" or e["tags"].get("highway") in EXCLUDE:
            continue
        g = [_k(p["lat"], p["lon"]) for p in e["geometry"]]
        for u, v in zip(g, g[1:]):
            if u == v:
                continue
            L = dist_m(u, v)
            adj.setdefault(u, []).append((v, L))
            adj.setdefault(v, []).append((u, L))
            seg.append((u, v))
    return adj, {"seg": seg}


def disponibil() -> bool:
    return RAW.exists() and RAW.stat().st_size > 1000 and RAW.read_text(encoding="utf-8")[:1] == "{"


def _proiecteaza(p, u, v):
    """Punctul de pe segmentul (u, v) cel mai apropiat de p: (punct, distanță_m)."""
    kx = 111_320 * math.cos(math.radians(p[0]))
    ax, ay = (u[1] - p[1]) * kx, (u[0] - p[0]) * 111_320
    bx, by = (v[1] - p[1]) * kx, (v[0] - p[0]) * 111_320
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L2))
    q = (u[0] + t * (v[0] - u[0]), u[1] + t * (v[1] - u[1]))
    return q, math.hypot(ax + t * dx, ay + t * dy)


def _snap(p, segmente):
    best = None
    for u, v in segmente:
        q, d = _proiecteaza(p, u, v)
        if best is None or d < best[0]:
            best = (d, q, u, v)
    return best


def _lungime(pts) -> float:
    return sum(dist_m(a, b) for a, b in zip(pts, pts[1:]))


def traseu(a: tuple[float, float], b: tuple[float, float]) -> dict | None:
    """Traseul pe stradă între a și b (lat, lon) sau None dacă nu există unul credibil."""
    if not disponibil():
        return None
    adj, meta = _graf()
    segs = meta["seg"]
    sa, sb = _snap(a, segs), _snap(b, segs)
    if not sa or not sb or max(sa[0], sb[0]) > SNAP_MAX_M:
        return None
    dreapta = dist_m(a, b)
    if dreapta < 1:
        return None
    # graf temporar: punctele proiectate devin noduri legate de capetele segmentului
    PA, PB = ("P", "a"), ("P", "b")
    extra: dict = {PA: [], PB: []}
    for P, (_, q, u, v) in ((PA, sa), (PB, sb)):
        extra[P] += [(u, dist_m(q, u)), (v, dist_m(q, v))]
    if (sa[2], sa[3]) == (sb[2], sb[3]) or (sa[2], sa[3]) == (sb[3], sb[2]):
        extra[PA].append((PB, dist_m(sa[1], sb[1])))      # același segment: drum direct

    def vecini(n):
        if n in extra:
            return extra[n]
        out = list(adj.get(n, []))
        for P, (_, q, u, v) in ((PA, sa), (PB, sb)):
            if n in (u, v):
                out.append((P, dist_m(q, n)))
        return out

    dist, prev, pq = {PA: 0.0}, {}, [(0.0, 0, PA)]
    i = 0
    while pq:
        d, _, n = heapq.heappop(pq)
        if n == PB:
            break
        if d > dist.get(n, 1e18):
            continue
        for m, L in vecini(n):
            nd = d + L
            if nd < dist.get(m, 1e18):
                dist[m], prev[m] = nd, n
                i += 1
                heapq.heappush(pq, (nd, i, m))
    if PB not in dist:
        return None
    cale, n = [], PB
    while n != PA:
        cale.append(sa[1] if n == PA else sb[1] if n == PB else n)
        n = prev[n]
    cale.append(sa[1])
    cale.reverse()
    # primul/ultimul punct real: a și b (cu un scurt tronson până la stradă)
    puncte = [a] + cale + [b]
    # scoate duplicatele consecutive
    puncte = [p for i, p in enumerate(puncte) if i == 0 or p != puncte[i - 1]]
    lung = _lungime(puncte)
    detur = lung / dreapta
    snap_mediu = (sa[0] + sb[0]) / 2
    s_snap = 1 - min(1.0, snap_mediu / 30.0)
    s_detur = 1.0 if detur <= 1.3 else max(0.0, 1 - (detur - 1.3) / 1.2)
    urm = round(0.5 * s_snap + 0.5 * s_detur, 3)
    if detur > 3.0:
        return None
    # cât s-ar abate linia dreaptă a→b de traseul pe stradă (justifică alegerea traseului în loc de dreaptă)
    abatere = 0.0
    for k in range(1, 10):
        f = k / 10
        q = (a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1]))
        abatere = max(abatere, min(_proiecteaza(q, u, v)[1] for u, v in zip(puncte, puncte[1:])))
    return {"puncte": puncte, "urmeaza_strada": urm, "abatere_dreapta_m": round(abatere, 1),
            "lungime_m": round(lung, 1),
            "lungime_dreapta_m": round(dreapta, 1), "detur": round(detur, 2), "snap_mediu_m": round(snap_mediu, 1)}


def strazi() -> list[dict]:
    """Străzile din cache pentru modulele lui A (trace, racordare): [{"nume": str|None, "puncte": [[lat, lon], ...]}].
    Doar drumurile folosite și la rutare (fără EXCLUDE). Listă goală dacă lipsește cache-ul."""
    if not disponibil():
        return []
    d = json.loads(RAW.read_text(encoding="utf-8"))
    out = []
    for e in d["elements"]:
        if e.get("type") != "way" or e["tags"].get("highway") in EXCLUDE:
            continue
        out.append({"nume": e["tags"].get("name"),
                    "puncte": [[p["lat"], p["lon"]] for p in e["geometry"]]})
    return out


def traseu_fn():
    """Funcția de pus în `GridModel.traseu_fn` (None dacă lipsește cache-ul de străzi)."""
    return traseu if disponibil() else None


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch()
        print("descărcat:", RAW)
    else:
        print("cache disponibil:", disponibil())
