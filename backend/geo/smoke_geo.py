"""Smoke test pentru backend/geo. Rulează: .venv/bin/python -m backend.geo.smoke_geo (fără apel CLI real)."""
import os

os.environ["EXTRACT_CLI"] = "0"
from unittest import mock

from backend.engine.config import load_weights
from backend.engine.network import load_network
from backend.engine.osm import strazi
from backend.extract import cli_ai
from backend.geo import geocodeaza, _AI_CACHE

cfg, S = load_weights(), strazi()
A = cfg["geocodare"]["acuratete"]
N = 0


def ok(c, m):
    global N
    assert c, m
    N += 1


def g(**ad):
    return geocodeaza({"adresa_structurata": ad}, S, cfg)


r = g(strada="Strada Liviu Rebreanu", numar="12")
ok(r["status"] == "gasit" and r["metoda"] == "osm_cache" and r["acuratete"] == A["strada_numar"], r)
ok(r["precizie_m"] == cfg["geocodare"]["precizie_numar_m"] and r["lat"], r)
r2 = g(strada="str. liviu rebreanu", numar="12")  # diacritice/prefix/majuscule
ok((r2["lat"], r2["lon"]) == (r["lat"], r["lon"]), r2)
ok(g(strada="Strada Liviu Rebreanu", numar="90")["lat"] != r["lat"], "interpolare")
s = g(strada="Strada Liviu Rebreanu")
ok(s["acuratete"] == A["strada"] and 25 <= s["precizie_m"] <= 150, s)
t = geocodeaza({"adresa": "Strada Liviu Rebreanu nr. 12, Pașcani"}, S, cfg)  # text liber
ok((t["lat"], t["lon"]) == (r["lat"], r["lon"]), t)
x = g(strada="Strada Bălții colț cu Strada Orizont")
ok(x["status"] == "gasit" and x["acuratete"] == A["intersectie"] and "intersecția" in x["motiv"], x)
ok(g(strada="Strada Inexistenta Zzz")["status"] == "necunoscut", "necunoscut (CLI oprit)")
ok(g(reper="lângă școală")["status"] == "necunoscut", "reper fără stradă")
rp = g(reper="vizavi de Strada Fagului")
ok(rp["status"] == "gasit" and rp["acuratete"] == A["reper"] and rp["precizie_m"] == cfg["geocodare"]["precizie_reper_m"], rp)

# calea AI: alege din listă (acceptat) sau în afara listei (respins)
for ales, status in (("Strada Liviu Rebreanu", "gasit"), ("Strada Inventata", "necunoscut")):
    _AI_CACHE.clear()
    with mock.patch.object(cli_ai, "call_cli", return_value={"strada": ales}) as m:
        a = g(strada="str liviu rebrianu")
    ok(m.called and a["status"] == status, a)
    if status == "gasit":
        ok(a["metoda"] == "ai_estimare" and a["acuratete"] == round(A["strada"] * cfg["geocodare"]["factor_ai_fuzzy"], 3), a)
ok(geocodeaza({}, S, cfg)["status"] == "necunoscut" and geocodeaza({"adresa": "x"}, [], cfg)["status"] == "necunoscut", "gol")
# în afara zonei: stradă din cache, dar cu raza_max_m mică (centroid fix -> punctul e „departe”)
ofz = geocodeaza({"adresa_structurata": {"strada": "Strada Liviu Rebreanu"}}, S, {**cfg, "zona": {"raza_max_m": 1}}, net=load_network())
ok(ofz["status"] == "in_afara_zonei" and ofz["metoda"] == "in_afara_zonei" and ofz["lat"] and "peste limita" in ofz["motiv"], ofz)
ok(r["status"] == "gasit", "în zonă rămâne gasit")

# fals pozitiv: „București” e orașul, nu strada; „Calea” nu potrivește „Strada”
for ad in ({"adresa": "Calea Victoriei 10 Bucuresti"}, {"adresa_structurata": {"strada": "Calea Victoriei", "numar": "10", "localitate": "București"}}):
    _AI_CACHE.clear()
    rv = geocodeaza(ad, S, cfg)
    ok(rv["status"] == "necunoscut", rv)
ok(g(strada="Strada București")["status"] == "gasit", "stradă reală București rămâne potrivită")

# toate cazurile din data/reports/geo-test.json (referinta din adresa_structurata_asteptata; cazurile cu AI: fără CLI = necunoscut, apoi CLI simulat)
import json
from pathlib import Path

from backend.engine.network import dist_m

TAB = []
for c in json.loads((Path(__file__).resolve().parents[2] / "data/reports/geo-test.json").read_text(encoding="utf-8"))["adrese"]:
    ref, a = {"adresa_structurata": c["adresa_structurata_asteptata"]}, c["asteptat"]

    def rul():
        _AI_CACHE.clear()
        return geocodeaza(ref, S, cfg)

    if c["ai_strada"]:
        ok(rul()["status"] == "necunoscut", (c["id"], "fără CLI = necunoscut"))
        with mock.patch.object(cli_ai, "call_cli", return_value={"strada": c["ai_strada"]}):
            res = rul()
        ok(res["metoda"] == "ai_estimare", (c["id"], res))
    else:
        res = rul()
    d = dist_m((res["lat"], res["lon"]), (a["lat"], a["lon"])) if res["lat"] and a["lat"] and c["geo_apelat"] else None
    ok(res["status"] == a["status_geo"], (c["id"], res))
    ok(d is None or d <= a["toleranta_m"], (c["id"], d, a["toleranta_m"]))
    if res["status"] == "gasit":  # acuratețea = cheia din tabel x factor_ai_fuzzy dacă a ales AI
        ok(res["acuratete"] == round(A[a["acuratete_tinta"]] * (cfg["geocodare"]["factor_ai_fuzzy"] if c["ai_strada"] else 1), 3), (c["id"], res))
    TAB.append((c["id"], res["status"], res["metoda"], None if d is None else round(d)))
for t in TAB:
    print(*t)
print(f"OK: {N} verificări")
