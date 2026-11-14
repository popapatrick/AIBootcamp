"""Smoke prezice_lant: .venv/bin/python -m backend.racordare.smoke_racordare"""
import json
from statistics import median

from backend.engine.config import ROOT, load_weights
from backend.engine.network import dist_m
from backend.racordare import _elemente, _lungime, prezice_lant

net = json.loads((ROOT / "data/model/network.geojson").read_text(encoding="utf-8"))
cfg = load_weights()
noduri, tr = _elemente(net)
span = median(_lungime(t) for t in tr)
nid, (la, lo) = max(noduri, key=lambda x: x[1][1])  # nodul cel mai estic: casa spre est îi e sigur cea mai apropiată
n = 0


def ok(c, m):
    global n
    assert c, m
    n += 1


# stradă sintetică est-vest, la ~5 m de nodul de start; casa la ~4 spanuri spre est
lon_pas = 1 / (111_320 * 0.7155)  # ~1 m în lon la lat ~44.28
strada = [{"nume": "Test", "puncte": [[la + 5e-5, lo + k * 10 * lon_pas] for k in range(-1, 15)]}]
casa = {"lat": la + 5e-5, "lon": lo + 4 * span * lon_pas}
r = prezice_lant(casa, net, strada, cfg)
ok(r["status"] == "lant" and r["urmeaza_strada"] == 1.0 and r["nod_start"] == nid, r)
ok(len(r["stalpi"]) >= 2 and len(r["cabluri"]) == len(r["stalpi"]) + 1, r)
pts = [(s["lat"], s["lon"]) for s in r["stalpi"]]
ok(len(pts) >= 2 and all(abs(dist_m(a, b) - span) < 0.1 * span + 1 for a, b in zip(pts, pts[1:])), "spațiere ~mediană")
ok(r["cabluri"][-1]["la"] == "casa", r)

r = prezice_lant(casa, net, [], cfg)
ok(r["status"] == "linie_dreapta" and r["urmeaza_strada"] is None, r)

r = prezice_lant({"lat": la + 0.1, "lon": lo}, net, strada, cfg)
ok(r["status"] == "fara_nod" and r["stalpi"] == [], r)

cfg2 = {**cfg, "racordare": {**cfg["racordare"], "max_stalpi_prezisi": 1}}
r = prezice_lant(casa, net, strada, cfg2)
ok(len(r["stalpi"]) == 1 and r["ambiguu"] and r["motiv"], r)
print(f"OK: {n} verificări")
