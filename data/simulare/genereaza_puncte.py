"""A4: stâlpi (serie 5) și case (serie 7) SIMULATE pe străzile OSM, generate o dată și hardcodate în puncte-simulare.json.

Format (cerut de B, `network.py` le încarcă cu origine retea_start):
  {"noduri": [{"id": "SIM-001", "lat", "lon", "serie": "serie 5"|"serie 7"}],
   "tronsoane": [{"id": "SIM-L1", "capete": [id, id], "puncte": [[lat, lon], ...], "categorie": "aerian"}]}
Stâlpii formează lanțuri pe străzi (tronson = porțiunea de stradă dintre doi stâlpi consecutivi); primul stâlp al
lanțului se leagă de nodul existent cel mai apropiat dacă e la <= LEGARE_M. Fiecare casă se leagă de un stâlp.

Rulare (din rădăcina repo-ului): .venv/bin/python data/simulare/genereaza_puncte.py
`data/` nu e pachet Python, deci rulăm ca script (adaugă singur rădăcina în sys.path). Nu face parte din demo.
Date FICTIVE: punctele nu există în realitate.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.engine import osm  # noqa: E402
from backend.engine.network import dist_m  # noqa: E402

SEED = 20260811
N_STALPI, N_CASE = 40, 15
MIN_M = 2.5                    # = potrivire.distanta_max_element_nou_m (regula nodului nou)
PAS_M = (35.0, 50.0)           # distanța dintre stâlpi pe stradă
LANT_MAX = 8                   # stâlpi per lanț
LEGARE_M = 80.0                # legare de un nod existent
OFFSET_CASA_M = (8.0, 14.0)    # casa e lateral față de stradă
RAZA_MAX_M = 3000              # = zona.raza_max_m
OUT = Path(__file__).with_name("puncte-simulare.json")


def retea() -> tuple[tuple[float, float], list[tuple[str, float, float]]]:
    """(centroid, noduri existente [(id, lat, lon)]) din network.geojson; centroidul = media nodurilor (Point)."""
    d = json.loads((ROOT / "data/model/network.geojson").read_text(encoding="utf-8"))
    n = [(f["properties"]["id"], f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0])
         for f in d["features"] if f["geometry"]["type"] == "Point"]
    return (sum(x[1] for x in n) / len(n), sum(x[2] for x in n) / len(n)), n


def _la(pct, cum, s):
    """(punct, indexul segmentului) la distanța s de-a lungul poliliniei."""
    for i in range(len(pct) - 1):
        if cum[i + 1] >= s:
            f = (s - cum[i]) / ((cum[i + 1] - cum[i]) or 1)
            a, b = pct[i], pct[i + 1]
            return (a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])), i
    return pct[-1], len(pct) - 2


def _lateral(a, b, p, m):
    kx = 111_320 * math.cos(math.radians(p[0]))
    dx, dy = (b[1] - a[1]) * kx, (b[0] - a[0]) * 111_320
    L = math.hypot(dx, dy) or 1.0
    return (p[0] + (dx / L) * m / 111_320, p[1] + (-dy / L) * m / kx)


def genereaza() -> dict:
    centru, existente = retea()
    rnd = random.Random(SEED)
    cai = sorted(([tuple(p) for p in s["puncte"]] for s in osm.strazi() if s["nume"] and len(s["puncte"]) >= 2),
                 key=lambda p: (p[0], len(p)))  # doar străzi cu nume; ordine stabilă
    cum_cai = []
    for p in cai:
        c = [0.0]
        for a, b in zip(p, p[1:]):
            c.append(c[-1] + dist_m(a, b))
        cum_cai.append(c)
    cai = [(p, c) for p, c in zip(cai, cum_cai) if c[-1] >= 100]
    ocupate = [(lat, lon) for _, lat, lon in existente]
    noduri, tronsoane, info = [], [], {}  # info[id] = (segment a, b) pentru case

    def liber(p):
        return dist_m(p, centru) <= RAZA_MAX_M and all(dist_m(p, q) >= MIN_M for q in ocupate)

    def nod(p, serie):
        i = f"SIM-{len(noduri) + 1:03d}"
        noduri.append({"id": i, "lat": round(p[0], 7), "lon": round(p[1], 7), "serie": serie})
        ocupate.append((round(p[0], 7), round(p[1], 7)))
        return i

    def tronson(a, b, puncte):
        tronsoane.append({"id": f"SIM-L{len(tronsoane) + 1}", "capete": [a, b],
                          "puncte": [[round(x, 7), round(y, 7)] for x, y in puncte], "categorie": "aerian"})

    tries = 0
    while len(noduri) < N_STALPI:
        tries += 1
        assert tries < 5000, "nu încap stâlpii"
        pct, cum = rnd.choice(cai)
        s, prev, n = rnd.uniform(0, cum[-1] * 0.3), None, 0  # prev = (id, s, punct)
        while s <= cum[-1] and n < LANT_MAX and len(noduri) < N_STALPI:
            p, seg = _la(pct, cum, s)
            if liber(p):
                i = nod(p, "serie 5")
                info[i] = (pct[seg], pct[seg + 1])
                p = (noduri[-1]["lat"], noduri[-1]["lon"])
                if prev:
                    pi, ps, pp = prev
                    mij = [pct[k] for k in range(len(pct)) if ps < cum[k] < s]
                    tronson(pi, i, [pp] + mij + [p])
                else:
                    e = min(existente, key=lambda x: dist_m(p, (x[1], x[2])))
                    if dist_m(p, (e[1], e[2])) <= LEGARE_M:
                        tronson(e[0], i, [(e[1], e[2]), p])
                prev, n = (i, s, p), n + 1
            s += rnd.uniform(*PAS_M)

    stalpi = [n["id"] for n in noduri]
    for st in rnd.sample(stalpi, N_CASE):
        s0 = next(n for n in noduri if n["id"] == st)
        a, b = info[st]
        for _ in range(200):
            p = _lateral(a, b, (s0["lat"], s0["lon"]), rnd.choice((-1, 1)) * rnd.uniform(*OFFSET_CASA_M))
            if liber(p):
                break
        else:
            raise AssertionError("nu încape casa")
        h = nod(p, "serie 7")
        tronson(st, h, [(s0["lat"], s0["lon"]), (noduri[-1]["lat"], noduri[-1]["lon"])])
    return {"noduri": noduri, "tronsoane": tronsoane}


def verifica(d: dict) -> None:
    centru, existente = retea()
    N = {n["id"]: (n["lat"], n["lon"]) for n in d["noduri"]}
    ex = {e[0]: (e[1], e[2]) for e in existente}
    assert sum(n["serie"] == "serie 5" for n in d["noduri"]) == N_STALPI
    assert sum(n["serie"] == "serie 7" for n in d["noduri"]) == N_CASE
    assert len(N) == len(d["noduri"]) and not set(N) & set(ex)
    P = list(N.values())
    for i, (k, p) in enumerate(N.items()):
        assert dist_m(p, centru) <= RAZA_MAX_M, k
        assert min(dist_m(p, e) for e in ex.values()) >= MIN_M, k
        assert all(dist_m(p, q) >= MIN_M for q in P[:i]), k
    assert len({t["id"] for t in d["tronsoane"]}) == len(d["tronsoane"])
    for t in d["tronsoane"]:
        assert t["categorie"] == "aerian" and len(t["capete"]) == 2 and len(t["puncte"]) >= 2, t
        assert all(c in N or c in ex for c in t["capete"]), t
        assert any(c in N for c in t["capete"]), t
    legate = {c for t in d["tronsoane"] for c in t["capete"]}
    assert all(k in legate for k in N), "nod izolat"


if __name__ == "__main__":
    d = genereaza()
    verifica(d)
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"ok: {len(d['noduri'])} noduri, {len(d['tronsoane'])} tronsoane -> {OUT.relative_to(ROOT)}")
