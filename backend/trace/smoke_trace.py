"""Smoke test pentru backend/trace. Rulează: .venv/bin/python -m backend.trace.smoke_trace"""
import json
from pathlib import Path

from backend.engine.config import load_weights
from backend.engine.network import load_network
from backend.engine.osm import strazi
from backend.trace import gaseste_opriri, localizeaza

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
print(f"OK: {N} verificări")
