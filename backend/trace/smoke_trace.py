"""Smoke test pentru backend/trace. Rulează: .venv/bin/python -m backend.trace.smoke_trace"""
import json
from pathlib import Path

from backend.engine.config import load_weights
from backend.engine.network import load_network
from backend.engine.osm import strazi
from backend.engine.network import dist_m
from backend.trace import gaseste_opriri, genereaza_traseu, localizeaza

cfg, net, S = load_weights(), load_network(), strazi()
N = 0


def ok(cond, msg):
    global N
    assert cond, msg
    N += 1


def tr(*grupuri):  # (lat, lon, minute) -> puncte la 30 s
    out, s = [], 0
    for la, lo, m in grupuri:
        for _ in range(int(m * 2) + 1):
            out.append({"t": f"2026-10-28T09:{s // 60:02d}:{s % 60:02d}", "lat": la, "lon": lo})
            s += 30
        s += 120  # deplasare
    return out


# opriri: 5 min + 2 min (prea scurtă) la 200 m distanță
op = gaseste_opriri(tr((44.2810, 26.0600, 5), (44.2828, 26.0600, 2)), cfg)
ok(len(op) == 1 and op[0]["durata_min"] >= 5, "oprire scurtă ignorată")
ok(gaseste_opriri([], cfg) == [], "fără puncte")

# fără opriri
r = localizeaza(tr((44.2810, 26.0600, 0)), "Strada X", net, S, cfg)
ok(r["status"] == "fara_opriri" and r["alegere"] is None, "fara_opriri")

# trasee din fișier: status așteptat
T = json.loads((Path(__file__).parents[2] / "data/reports/trasee-dummy.json").read_text(encoding="utf-8"))
R = {t["id"]: localizeaza(t["puncte"], t["adresa"], net, S, cfg) for t in T}
a = R["trace-1"]  # stradă + oprire lungă fără stâlp, 3 stâlpi vizitați
ok(a["status"] == "gasit" and a["strada"]["nume"] == "Strada Liviu Rebreanu", "stradă potrivită")
ok(a["alegere"]["element_id"] is None and a["alegere"]["durata_min"] >= 20, "oprire lungă fără stâlp")
ok(len(a["vizitate"]) >= 3, "stâlpi vizitați")
b = R["trace-2"]
ok(b["status"] == "ambiguu" and b["ambiguitate"] and b["calitate"] < 0.9, "ambiguitate")
c = R["trace-3"]
ok(c["status"] == "gasit" and c["strada"] is None and abs(c["calitate"] - 0.9 * cfg["trace"]["factor_fara_strada"]) < 1e-6, "fallback fără stradă")
ok(R["trace-4"]["status"] == "fara_opriri", "traseu doar mers")
ok(localizeaza(T[0]["puncte"], "STRADA LIVIU REBREANU nr. 3", net, S, cfg)["strada"] is not None, "normalizare")

# traseu generat: punct pe o stradă numită din cache
st = next(x for x in S if x["nume"] and len(x["puncte"]) > 3)
mid = st["puncte"][len(st["puncte"]) // 2]
P = {"lat": mid[0], "lon": mid[1]}
G = cfg["trace_generat"]
g1 = genereaza_traseu(P, S, G, "r1")
ok(g1 == genereaza_traseu(P, S, G, "r1"), "determinist pe seed")
ok(g1 != genereaza_traseu(P, S, G, "r2"), "seed diferit, traseu diferit")
ok(40 <= len(g1) <= 60 and g1[0]["t"] < g1[-1]["t"], "număr puncte și ordine")
r = localizeaza(g1, st["nume"], net, S, cfg)
ok(r["status"] == "gasit" and dist_m((r["alegere"]["lat"], r["alegere"]["lon"]), mid) < 10, "oprirea generată redescoperită")
ok(r["alegere"]["durata_min"] >= G["durata_oprire_min"] - 3, "durata oprire")
# decalaj: oprirea se mută cu ~decalaj
r = localizeaza(genereaza_traseu(P, S, {**G, "decalaj_m": 50}, "r1"), st["nume"], net, S, cfg)
d = dist_m((r["alegere"]["lat"], r["alegere"]["lon"]), mid)
ok(r["status"] != "fara_opriri" and 40 < d < 60, f"decalaj 50 m (d={d:.0f})")
# oprire scurtă (sub durata_min_min) și zgomot mare: nu se mai găsește oprirea
ok(localizeaza(genereaza_traseu(P, S, {**G, "durata_oprire_min": 2}, "r1"), st["nume"], net, S, cfg)["status"] == "fara_opriri", "oprire scurtă")
ok(localizeaza(genereaza_traseu(P, S, {**G, "zgomot_m": 40}, "r1"), st["nume"], net, S, cfg)["status"] == "fara_opriri", "zgomot mare")
# zgomot moderat: încă găsită, dar mai puțin precis decât la zgomot mic
e = lambda z: dist_m(*[(lambda a: (a["lat"], a["lon"]))(localizeaza(genereaza_traseu(P, S, {**G, "zgomot_m": z}, "r3"), st["nume"], net, S, cfg)["alegere"]), mid])
ok(e(1) < 3, "zgomot 1 m precis")
# acoperire mică: oprirea poate pierde puncte, durata scade
ok(len(genereaza_traseu(P, S, {**G, "acoperire": 0.3}, "r1")) < len(g1), "acoperire mică, mai puține puncte")
ok(len(genereaza_traseu(P, [], G, "r1")) > 30, "fără străzi")
# în afara zonei: oprire la ~5 km de centroid (> raza_max_m)
from backend.engine.zona import centru_retea
c0 = centru_retea(net)
far = localizeaza(tr((c0[0] + 0.045, c0[1], 5)), "Strada X", net, S, cfg)
ok(far["status"] == "in_afara_zonei" and far["alegere"] and "peste limita" in far["motiv"], far)
print(f"OK: {N} verificări")
