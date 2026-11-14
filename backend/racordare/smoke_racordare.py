"""Smoke prezice_lant: .venv/bin/python -m backend.racordare.smoke_racordare"""
import json
from statistics import median

from backend.engine.config import ROOT, load_weights
from backend.engine.network import dist_m
from backend.racordare import LocalizareEroare, _elemente, _lungime, locatie_operator_demo, prezice_lant

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
ok(r["treapta"] == 1 and r["status"] == "lant" and r["urmeaza_strada"] == 1.0 and r["nod_start"] == nid, r)
ok(len(r["stalpi"]) >= 2 and len(r["cabluri"]) == len(r["stalpi"]) + 1, r)
pts = [(s["lat"], s["lon"]) for s in r["stalpi"]]
ok(len(pts) >= 2 and all(abs(dist_m(a, b) - span) < 0.1 * span + 1 for a, b in zip(pts, pts[1:])), "spațiere ~mediană")
ok(r["cabluri"][-1]["la"] == "casa", r)

r = prezice_lant(casa, net, [], cfg)
ok(r["status"] == "linie_dreapta" and r["urmeaza_strada"] is None, r)

# treptele 2-4: casa spre est, la distanță mare de orice nod (nodul cel mai estic e cel mai apropiat)
rz = cfg["racordare"]
la_m = lambda m: {"lat": la, "lon": lo + m * lon_pas}
r = prezice_lant(la_m(rz["raza_nod_m"] - 20), net, [], cfg)
ok(r["treapta"] == 1 and r["status"] == "linie_dreapta" and r["motiv"] is None, r)
r = prezice_lant(la_m(rz["raza_nod_m"] + 20), net, strada, cfg)
ok(r["treapta"] == 2 and r["nod_start"] == nid and r["stalpi"] and "extinsă" in r["motiv"], r)
r = prezice_lant(la_m(rz["raza_extinsa_m"] + 20), net, strada, cfg)  # strada există, dar treapta 3 e linie dreaptă
ok(r["treapta"] == 3 and r["status"] == "linie_dreapta" and r["urmeaza_strada"] is None and r["nod_start"] == nid, r)
ok(r["cabluri"] and r["cabluri"][-1]["la"] == "casa" and r["motiv"], r)
r = prezice_lant({"lat": la + 0.1, "lon": lo}, net, strada, cfg)
ok(r["treapta"] == 3 and r["ambiguu"] and len(r["stalpi"]) == rz["max_stalpi_prezisi"], r)
r = prezice_lant(casa, {"type": "FeatureCollection", "features": []}, strada, cfg)
ok(r["treapta"] == 4 and r["status"] == "fara_nod" and r["nod_start"] is None and r["stalpi"] == [] and r["cabluri"] == [] and r["motiv"], r)

cfg2 = {**cfg, "racordare": {**cfg["racordare"], "max_stalpi_prezisi": 1}}
r = prezice_lant(casa, net, strada, cfg2)
ok(len(r["stalpi"]) == 1 and r["ambiguu"] and r["motiv"], r)

# --- locatie_operator_demo (poziția simulată din textul operatorului), pe străzi OSM reale din cache
from backend.engine import osm

S = osm.strazi()
rs = [s for s in S if s["nume"] == "Strada Liviu Rebreanu"]
op = lambda t, **k: locatie_operator_demo(t, net, S, cfg, **k)
r = op("Cerere racordare: client nou, casă pe Strada Liviu Rebreanu")
ok(r["simulata"] is True and r["strada"] == "Strada Liviu Rebreanu" and r["precizie_m"] > 0, r)
ok(min(dist_m((r["lat"], r["lon"]), tuple(p)) for s in rs for p in s["puncte"]) <= r["precizie_m"] + 6, "pe stradă (±precizie)")
ok(r["indicii"] == [{"tip": "strada", "valoare": "Strada Liviu Rebreanu", "gasit": True}], r["indicii"])
ok(op("str. LIVIU rebreanu!") == op("Strada Liviu  Rebreanu"), "determinist, tolerant la prescurtări/majuscule")
ok(prezice_lant(r, net, S, cfg)["status"] in ("lant", "linie_dreapta"), "punctul pornește un lanț")
ri = op("casa e pe strada Liviu Rebreanu colț cu strada Ion Luca Caragiale")
ok(any(i["tip"] == "intersectie" and i["gasit"] for i in ri["indicii"]) and ri["precizie_m"] < r["precizie_m"], ri["indicii"])
cs = [q for s in S if s["nume"] in ("Strada Liviu Rebreanu", "Strada Ion Luca Caragiale") for q in s["puncte"]]
ok(min(dist_m((ri["lat"], ri["lon"]), tuple(q)) for q in cs) <= 12, "lângă intersecție")
rc = op("cartierul 1 Decembrie")
ok(rc["strada"] is None and rc["precizie_m"] > r["precizie_m"] and rc["indicii"][0]["tip"] == "cartier", rc)
rk = op("Strada Viilor din cartierul 1 Decembrie")
ok([i["tip"] for i in rk["indicii"]] == ["strada", "cartier"] and all(i["gasit"] for i in rk["indicii"]), rk["indicii"])
rn = op("strada Liviu Rebreanu, cartierul Berceni, lângă școala veche")
ok([(i["tip"], i["gasit"]) for i in rn["indicii"]] == [("strada", True), ("cartier", False), ("reper", False)]
   and rn["strada"] == "Strada Liviu Rebreanu" and "negăsiți" in rn["motiv"], rn["indicii"])
for txt in ("casă undeva", "strada Foo Bar nr 3", "cartierul Berceni"):
    try:
        op(txt)
        ok(False, f"trebuia LocalizareEroare: {txt}")
    except LocalizareEroare as e:
        ok(e.indicii == [] or all(not i["gasit"] for i in e.indicii), e.indicii)
print(f"OK: {n} verificări")
