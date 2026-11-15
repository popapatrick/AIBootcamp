"""Smoke test pentru backend/tracking (B1). Rulează: .venv/bin/python -m backend.tracking.smoke_tracking"""
import copy
import math

from backend.engine.config import load_weights
from backend.engine.network import dist_m, incarca_puncte_simulare, load_network
from backend.engine.osm import strazi
from backend.engine.zona import zona_ok
from backend.trace import _dist_strada, gaseste_opriri
from backend.tracking import genereaza_tura

cfg, net, S = load_weights(), load_network(), strazi()
incarca_puncte_simulare(net)
T = cfg["tracking"]
ECHIPE = ["mentenanta", "investitii", "racordari"]
DATA = "2026-09-25"
N = 0


def ok(cond, msg):
    global N
    assert cond, msg
    N += 1


ok(len(S) > 0, "cache OSM disponibil (străzi)")
ways = [[tuple(p) for p in s["puncte"]] for s in S]
noduri = [(v["lat"], v["lon"]) for v in net["noduri"].values()]
ture = {e: genereaza_tura(net, S, cfg, e, "seed-1", DATA) for e in ECHIPE}

# determinism
for e in ECHIPE:
    ok(genereaza_tura(net, S, cfg, e, "seed-1", DATA) == ture[e], f"determinism {e}")
ok(len({t["tura_id"] for t in ture.values()}) == 3, "3 echipe = 3 tura_id diferite")
ok(genereaza_tura(net, S, cfg, "mentenanta", "seed-2", DATA) != ture["mentenanta"], "seed diferit = altă tură")
ok(genereaza_tura(net, S, cfg, "mentenanta", "seed-2", DATA)["tura_id"] != ture["mentenanta"]["tura_id"], "seed diferit = alt tura_id")

# scoruri: stâlpii nu-verzi sunt preferați
scoruri = {nid: (0.9 if i % 2 else 0.5) for i, nid in enumerate(sorted(net["noduri"]))}
ts = genereaza_tura(net, S, cfg, "mentenanta", "seed-s", DATA, scoruri=scoruri)
st = [p["element_id"] for p in ts["plan"] if p["tip_plan"] == "stalp"]
ok(st and all(scoruri[i] < cfg["culori"]["verde"] for i in st), f"stâlpi nu-verzi preferați: {st}")

for e, t in ture.items():
    p = t["plan"]
    stalpi = [x for x in p if x["tip_plan"] == "stalp"]
    ok(T["stalpi_min"] <= len(stalpi) <= T["stalpi_max"], f"{e}: număr stâlpi {len(stalpi)}")
    ok(sum(x["tip_plan"] == "fara_stalp" for x in p) == 1, f"{e}: un loc fără stâlp")
    ok(1 <= sum(x["tip_plan"] == "scurta" for x in p) <= 2 or t["linie_dreapta"], f"{e}: 1-2 opriri scurte")
    ok(len({x["element_id"] for x in stalpi}) == len(stalpi), f"{e}: stâlpi distincți")
    for x in stalpi:
        el = net["noduri"].get(x["element_id"])
        ok(el is not None and not x["element_id"].endswith("-casa"), f"{e}: {x['element_id']} e stâlp existent")
        ok(_dist_strada((el["lat"], el["lon"]), ways) <= 40, f"{e}: stâlp la <= 40 m de stradă")
        d = dist_m((el["lat"], el["lon"]), (x["lat"], x["lon"]))
        ok(3 - 0.5 <= d <= 8 + 0.5, f"{e}: oprire la 3-8 m de stâlp ({d:.1f})")
        ok(6 <= x["durata_min"] <= 10, f"{e}: oprire stâlp 6-10 min")
    fs = next(x for x in p if x["tip_plan"] == "fara_stalp")
    ok(fs["durata_min"] == 15, f"{e}: loc fără stâlp 15 min")
    ok(min(dist_m((fs["lat"], fs["lon"]), q) for q in noduri) >= T["raza_fara_stalp_m"], f"{e}: loc fără stâlp la >= raza_fara_stalp_m de orice nod")
    ok(_dist_strada((fs["lat"], fs["lon"]), ways) <= 1.0, f"{e}: loc fără stâlp pe stradă")
    for x in p:
        if x["tip_plan"] == "scurta":
            ok(x["durata_min"] < T["durata_validare_min"] and 1 <= x["durata_min"] <= 2, f"{e}: oprire scurtă 1-2 min < durata_validare_min")
    # puncte
    pts = t["puncte"]
    ok(len(pts) > 20 and pts == sorted(pts, key=lambda q: q["t"]), f"{e}: puncte cronologice")
    ok(pts[0]["t"] == f"{DATA}T08:00:00", f"{e}: start 08:00")
    ok(all(zona_ok(q["lat"], q["lon"], net, cfg)["ok"] for q in pts), f"{e}: toate punctele în zona de 3 km")
    ok(t["lungime_m"] > 0 and t["durata_min"] > 0, f"{e}: lungime și durată")
    # opririle din plan regăsite de gaseste_opriri
    det = gaseste_opriri(pts, cfg)
    for x in p:
        if x["tip_plan"] == "scurta":
            ok(not any(dist_m((x["lat"], x["lon"]), (o["lat"], o["lon"])) < 15 for o in det), f"{e}: oprirea scurtă nu e detectată ca oprire")
            continue
        gasite = [o for o in det if dist_m((x["lat"], x["lon"]), (o["lat"], o["lon"])) <= 10]
        ok(len(gasite) == 1, f"{e}: oprire {x['tip_plan']} regăsită ({len(gasite)})")
        ok(abs(gasite[0]["durata_min"] - x["durata_min"]) <= 1.0, f"{e}: durata {gasite[0]['durata_min']} ~ {x['durata_min']}")
    ok(len(det) == len([x for x in p if x["tip_plan"] != "scurta"]), f"{e}: nicio oprire în plus detectată ({len(det)})")

# fără zgomot: punctele de mers la <= 20 m de o stradă (cele din opriri sunt chiar în centrul opririi, cu stâlpul la <= 25 m de stradă)
cfg0 = copy.deepcopy(cfg)
cfg0["tracking"]["zgomot_m"] = 0
for e in ECHIPE:
    t0 = genereaza_tura(net, S, cfg0, e, "seed-1", DATA)
    ok(t0["linie_dreapta"] == 0, f"{e}: drumuri pe străzi (linie_dreapta={t0['linie_dreapta']})")
    centre = [(x["lat"], x["lon"]) for x in t0["plan"]]
    mers = [q for q in t0["puncte"] if min(dist_m((q["lat"], q["lon"]), c) for c in centre) > 0.5]
    ok(len(mers) > 5, f"{e}: există puncte de mers")
    ok(all(_dist_strada((q["lat"], q["lon"]), ways) <= 20 for q in mers), f"{e}: puncte de mers la <= 20 m de stradă")
    pas = [dist_m((a["lat"], a["lon"]), (b["lat"], b["lon"])) for a, b in zip(t0["puncte"], t0["puncte"][1:])]
    ok(max(pas) <= T["viteza_m_s"] * T["pas_s"] + 1, f"{e}: pas maxim <= viteza × pas_s")

# mai multe seed-uri: nu cade, rămân în zonă
for i in range(10):
    t = genereaza_tura(net, S, cfg, ECHIPE[i % 3], f"s{i}", DATA)
    ok(all(zona_ok(q["lat"], q["lon"], net, cfg)["ok"] for q in t["puncte"]), f"seed s{i} în zonă")

print(f"OK: {N} verificări")
