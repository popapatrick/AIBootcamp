"""Smoke test pentru backend/geo. Rulează: .venv/bin/python -m backend.geo.smoke_geo (fără apel CLI real)."""
import os

os.environ["EXTRACT_CLI"] = "0"
from unittest import mock

from backend.engine.config import load_weights
from backend.engine.network import load_network
from backend.engine.osm import strazi
from backend.extract import cli_ai
import tempfile
from pathlib import Path

import backend.geo as geo
from backend.geo import geocodeaza, _AI_CACHE, cerere_ai, scrie_ai

geo._AI_FILE = Path(tempfile.mkdtemp()) / "geo_ai.json"  # izolat de cache-ul commit-uit

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
FC = cfg["cautare_strada"]["factor_numere_conventie"]
ok(r["status"] == "gasit" and r["metoda"] == "osm_cache" and r["acuratete"] == round(A["strada_numar"] * FC, 3), r)  # V6: convenția, fără ancore
ok(r["precizie_m"] == cfg["cautare_strada"]["precizie_conventie_m"] and r["lat"] and r["fereastra"]["metoda"] == "conventie", r)
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
    geo._AI_FILE = Path(tempfile.mkdtemp()) / "geo_ai.json"
    with mock.patch.object(cli_ai, "call_cli", return_value={"strada": ales}) as m:
        a = g(strada="str liviu rebrianu")
    ok(m.called and a["status"] == status, a)
    if status == "gasit":
        ok(a["metoda"] == "ai_estimare" and a["acuratete"] == round(A["strada"] * cfg["geocodare"]["factor_ai_fuzzy"], 3), a)
# cache persistent: fără CLI, intrare validă -> ai_estimare; nume în afara listei -> ignorat; scrie_ai validează
_AI_CACHE.clear()
ci = cerere_ai("str liviu rebrianu", S)
ok(ci["cheie"] == "liviu rebrianu" and "Strada Liviu Rebreanu" in ci["candidati"] and len(ci["candidati"]) <= 5, ci)
ok(g(strada="str liviu rebrianu")["status"] == "necunoscut", "fără cache și fără CLI")
scrie_ai(ci["cheie"], "Strada Liviu Rebreanu")
c1 = g(strada="str liviu rebrianu")
ok(c1["status"] == "gasit" and c1["metoda"] == "ai_estimare", c1)
try:
    scrie_ai("x", "Strada Inventata")
    ok(False, "trebuia ValueError")
except ValueError:
    ok(True, "")
geo._AI_FILE.write_text('{"liviu rebrianu": "Strada Inventata"}', encoding="utf-8")
ok(g(strada="str liviu rebrianu")["status"] == "necunoscut", "nume invalid în cache ignorat")
geo._AI_FILE = Path(tempfile.mkdtemp()) / "geo_ai.json"
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

# ---- V6: fereastra pe stradă (fereastra_strada); EXTRACT_CLI=0, determinist, fără AI
import math

from backend.engine.network import dist_m
from backend.geo import fereastra as fer
from backend.geo import fereastra_strada, _grupe, _SOSEA
from backend.engine.zona import centru_retea, zona_ok

NET = load_network()
GR = _grupe(S)
CS = cfg["cautare_strada"]


def fs(ref, anc=None):
    return fereastra_strada(ref, S, cfg, anc, NET)


def ad(**k):
    return {"adresa_structurata": k}


def cale_(cheie):  # calea orientată a unei străzi, ca în modul
    return fer.orienteaza(GR[cheie]["pct"], GR[_SOSEA]["cai"] if cheie != _SOSEA else None, centru_retea(NET), cheie == _SOSEA)[0]


def dd(p, q):
    return dist_m((p["lat"], p["lon"]), (q["lat"], q["lon"]))


V = "Strada Viilor"
# convenția: nr 2 aproape de start, nr 40 mai departe; par/impar pe părți opuse la 2*decalaj
w2, w40 = fs(ad(strada=V, numar="2")), fs(ad(strada=V, numar="40"))
ok(w2["status"] == w40["status"] == "gasit" and w2["metoda"] == "conventie", (w2, w40))
ok(w2["de_la_m"] == 0.0 and w2["pana_la_m"] == CS["precizie_conventie_m"] + 12, w2)  # nr 2 = 12 m de start, fereastră ±100 m, tăiată la 0
ok(w40["de_la_m"] == 240 - CS["precizie_conventie_m"] and w40["precizie_m"] == CS["precizie_conventie_m"], w40)
ok(w40["acuratete"] == round(A["strada_numar"] * CS["factor_numere_conventie"], 3), w40)
ok(dist_m(cale_("viilor").p[0], (w2["punct"]["lat"], w2["punct"]["lon"])) < dist_m(cale_("viilor").p[0], (w40["punct"]["lat"], w40["punct"]["lon"])), "nr 2 mai aproape de start")
w14, w15 = fs(ad(strada=V, numar="14")), fs(ad(strada=V, numar="15"))
ok(w14["latura"] == "par" and w15["latura"] == "impar", (w14, w15))
ok(abs(dd(w14["punct"], w15["punct"]) - 2 * CS["decalaj_paritate_m"]) < 1.0, dd(w14["punct"], w15["punct"]))  # ~16 m între cele două părți
ok(w14["indiciu"]["tip"] == "numar" and w14["indiciu"]["sursa"] == "regex", w14["indiciu"])
ok(fs(ad(strada=V, numar="9999"))["pana_la_m"] <= round(cale_("viilor").L, 1), "plafonat la lungimea străzii")
for w in (w2, w14, w15, w40):
    ok(w["linie"] and w["linie"][0] and w["motiv"] and w["ancore_folosite"] == [], w)
# capătul de start: Strada Viilor se leagă de Șoseaua Principală, aceasta de centrul rețelei
ok(dist_m(cale_("viilor").p[0], GR["principala"]["pct"][0]) > 0 and min(dist_m(cale_("viilor").p[0], q) for q in GR["principala"]["pct"]) < 300, "start Viilor la Șoseaua Principală")
# ancore: 2 pe Strada Viilor (nr 5 la 40 m, nr 45 la 200 m)
cv = cale_("viilor")
A1, A2 = cv.la(40), cv.la(200)
ANC = [{"strada": V, "numar": 5, "lat": A1[0], "lon": A1[1]}, {"strada": "Str. Viilor", "numar": 45, "lat": A2[0], "lon": A2[1]},
       {"strada": "Strada Teiului", "numar": 9, "lat": A1[0], "lon": A1[1]}]  # ultima = altă stradă, ignorată
wa = fs({"adresa_structurata": {"strada": V, "numar": "15", "indiciu": {"tip": "langa", "numar": "15"}}}, ANC)
ok(wa["metoda"] == "ancore" and wa["precizie_m"] == CS["precizie_ancore_m"] and wa["acuratete"] == A["strada_numar"], wa)
ok(wa["de_la_m"] == 40.0 and wa["pana_la_m"] == 120.0 and len(wa["ancore_folosite"]) == 2, wa)  # nr 15 = 40 + 10/40*160 = 80 m
ok(wa["indiciu"]["sursa"] == "extractie" and wa["indiciu"]["tip"] == "langa", wa["indiciu"])
sa, _ = cv.proiecteaza((wa["punct"]["lat"], wa["punct"]["lon"]))
ok(40 < sa < 200, sa)  # cade între ancore
ok(fs(ad(strada=V, numar="25"), ANC)["de_la_m"] == 80.0, "nr 25 = 40 + 20/40*160 = 120 m, fereastră ±40")
ok(fs(ad(strada=V, numar="45"), ANC)["de_la_m"] == 160.0, "număr egal cu o ancoră")
we = fs(ad(strada=V, numar="55"), ANC)  # extrapolare de la ultima ancoră: 200 + 10*6 = 260 m
ok(we["metoda"] == "ancore" and we["de_la_m"] == 220.0 and len(we["ancore_folosite"]) == 1, we)
# indicii relative
wi = fs(ad(strada="Strada Bălții", indiciu={"tip": "intre", "numar": "10", "numar_2": "20"}))
ok(wi["metoda"] == "conventie" and wi["latura"] is None and wi["precizie_m"] == 30.0 and (wi["de_la_m"], wi["pana_la_m"]) == (60.0, 120.0), wi)
wi2 = fs(ad(strada="Strada Bălții", indiciu={"tip": "intre", "numar": "10", "numar_2": "12"}))
ok(wi2["precizie_m"] == fer.PRECIZIE_MIN_INTRE_M, wi2)  # minim 20 m
wd, wb = fs(ad(strada=V, indiciu={"tip": "dupa", "numar": "30"})), fs(ad(strada=V, indiciu={"tip": "inainte", "numar": "30"}))
ok(wd["de_la_m"] == 180.0 and wd["pana_la_m"] == 180.0 + CS["fereastra_dupa_m"], wd)
ok(wb["de_la_m"] == 180.0 - CS["fereastra_dupa_m"] and wb["pana_la_m"] == 180.0, wb)
wc, wn = fs(ad(strada="Strada Teiului", indiciu={"tip": "capat"})), fs(ad(strada="Strada Teiului", indiciu={"tip": "inceput"}))
L_t = cale_("teiului").L
ok(wc["metoda"] == "indiciu" and wc["precizie_m"] == CS["precizie_capat_m"] and abs(wc["pana_la_m"] - L_t) < 0.2, wc)
ok(wn["de_la_m"] == 0.0 and wn["pana_la_m"] == CS["precizie_capat_m"], wn)
wk = fs(ad(strada=V, indiciu={"tip": "colt", "strada_2": "Strada Soarelui"}))
ok(wk["acuratete"] == A["intersectie"] and wk["precizie_m"] == cfg["geocodare"]["precizie_intersectie_m"] and wk["metoda"] == "indiciu", wk)
ix = geocodeaza(ad(strada=V + " colț cu Strada Soarelui"), S, cfg)  # același punct ca intersecția din geocodeaza
ok(ix["fereastra"]["punct"] == wk["punct"] and (ix["lat"], ix["lon"]) == (wk["punct"]["lat"], wk["punct"]["lon"]), (ix, wk))
wk2 = fs(ad(strada=V, indiciu={"tip": "colt", "strada_2": "Strada Oituz"}))  # nu se intersectează: toată strada
ok(wk2["de_la_m"] == 0.0 and wk2["pana_la_m"] > 300 and "nu se intersectează" in wk2["motiv"], wk2)
wv = fs(ad(strada=V, indiciu={"tip": "vizavi", "numar": "15"}))
ok(wv["latura"] == "par" and wv["de_la_m"] == w15["de_la_m"] and dd(wv["punct"], w15["punct"]) > 2 * CS["decalaj_paritate_m"] - 1, wv)
noduri = NET["noduri"]
el = min(noduri.values(), key=lambda n: cv.proiecteaza((n["lat"], n["lon"]))[1])  # nodul cel mai apropiat de Strada Viilor
se, lat_ = cv.proiecteaza((el["lat"], el["lon"]))
we1 = fs(ad(strada=V, indiciu={"tip": "element", "element_id": el["id"], "distanta_stalpi": 2}))
ok(abs(we1["de_la_m"] - (se - 80)) < 1 or we1["de_la_m"] == 0.0, we1)
ok(abs(we1["precizie_m"] - 80) < 0.1 and we1["metoda"] == "indiciu", we1)
we2 = fs({"adresa": f"Strada Viilor, la 2 stâlpi de {el['id']} spre capăt"})  # text liber + sens
ok(we2["indiciu"]["tip"] == "element" and we2["indiciu"]["distanta_stalpi"] == 2 and abs(we2["de_la_m"] - se) < 1 and abs(we2["pana_la_m"] - (se + 80)) < 1, we2)
ok(fs(ad(strada=V, indiciu={"tip": "element", "element_id": "0000000"}))["de_la_m"] == 0.0, "element necunoscut: toată strada")
wt = fs(ad(strada=V))
ok(wt["metoda"] == "indiciu" and wt["indiciu"] is None and wt["de_la_m"] == 0.0 and abs(wt["precizie_m"] - cv.L / 2) < 0.1 and wt["acuratete"] == A["strada"], wt)
wp = fs(ad(strada=V, indiciu={"tip": "parte", "paritate": "par"}))
ok(wp["latura"] == "par" and wp["acuratete"] == A["strada"], wp)
# text liber fără indiciu structurat: fallback regex (cu și fără diacritice)
RX = [("Stâlp căzut pe Strada Viilor, lângă nr. 15", "langa", "15"), ("stalp cazut pe strada viilor langa nr 15", "langa", "15"),
      ("Strada Viilor, în dreptul nr. 15", "langa", "15"), ("Strada Viilor vizavi de nr 15", "vizavi", "15"),
      ("Strada Viilor, nr 12", "numar", "12"), ("Strada Viilor numărul 12", "numar", "12"), ("Strada Viilor 12", "numar", "12"),
      ("Cablu rupt între nr. 10 și 20 pe Strada Bălții", "intre", "10"), ("Strada Viilor după nr 30", "dupa", "30"),
      ("Strada Viilor înainte de nr. 30", "inainte", "30"), ("fără curent la capătul Străzii Teiului", "capat", None),
      ("Strada Teiului la începutul străzii", "inceput", None), ("la intrarea pe stradă, Strada Teiului", "inceput", None),
      ("Strada Viilor colț cu Strada Soarelui", "colt", None), ("Strada Viilor, intersecția cu Strada Soarelui", "colt", None),
      ("Strada Viilor lângă stâlpul 7101969", "element", None), ("Strada Viilor la 2 stâlpi de 7101969", "element", None),
      ("Strada Viilor pe partea cu numere impare", "parte", None)]
for t, tip, nr in RX:
    ind = fer.deduce_indiciu(t)
    ok(ind and ind["tip"] == tip and (nr is None or ind["numar"] == nr), (t, ind))
    wr = fs({"adresa": t})
    ok(wr["status"] == "gasit" and wr["strada"] in (V, "Strada Bălții", "Strada Teiului") and (wr["indiciu"] or {}).get("tip") == tip, (t, wr))
ok(fer.deduce_indiciu("Strada Viilor") is None and fer.deduce_indiciu("lângă școală") is None, "fără indiciu = None")
ok(fer.deduce_indiciu("între nr. 10 și 20")["numar_2"] == "20" and fer.deduce_indiciu("la 2 stâlpi de 7101969")["element_id"] == "7101969", "câmpuri")
ok(fer.deduce_indiciu("colț cu Strada Soarelui")["strada_2"] == "strada soarelui" and fer.deduce_indiciu("partea cu numere pare")["paritate"] == "par", "câmpuri 2")
wl, wm = fs({"adresa": "Stâlp căzut pe Strada Viilor, lângă nr. 15"}), fs(ad(strada=V, indiciu={"tip": "langa", "numar": "15"}))
ok({k: v for k, v in wl.items() if k != "indiciu"} == {k: v for k, v in wm.items() if k != "indiciu"}, "text liber = indiciu structurat")
# stradă inexistentă / goală: necunoscut, fără punct inventat
for ref in ({"adresa": "Strada Inexistenta Zzz nr 5"}, ad(strada="Strada Inexistenta Zzz", numar="5"), {}, ad(reper="lângă școală")):
    wn_ = fs(ref)
    ok(wn_["status"] == "necunoscut" and wn_["punct"] is None and wn_["linie"] == [] and wn_["acuratete"] == 0.0, (ref, wn_))
ok(fereastra_strada({"adresa": "x"}, [], cfg, None, NET)["status"] == "necunoscut", "fără străzi")
# determinism
ref_d = {"adresa_structurata": {"strada": V, "numar": "15", "indiciu": {"tip": "langa", "numar": "15"}}}
ok(fs(ref_d) == fs(ref_d) and fs(ref_d, ANC) == fs(ref_d, ANC) and fs({"adresa": "Strada Viilor colț cu Strada Soarelui"}) == fs({"adresa": "Strada Viilor colț cu Strada Soarelui"}), "determinism")
# toate punctele (și fereastra) în zona de 3 km; safeguard: raza mică -> in_afara_zonei
for ref in (ad(strada=V, numar="15"), ad(strada=V, numar="9999"), ad(strada="Strada Teiului", indiciu={"tip": "capat"}),
            ad(strada="Șoseaua Principală", indiciu={"tip": "inceput"}), ad(strada="Șoseaua Principală", numar="30")):
    w = fs(ref)
    ok(w["status"] == "gasit" and zona_ok(w["punct"]["lat"], w["punct"]["lon"], NET, cfg)["ok"], w)
    ok(all(zona_ok(a, b, NET, cfg)["ok"] for a, b in w["linie"]), "linie în zonă")
wp_ = fs(ad(strada="Șoseaua Principală", indiciu={"tip": "capat"}))  # capătul opus al șoselei (4 km) iese din zona de 3 km
ok(wp_["status"] == "in_afara_zonei" and wp_["punct"] and "peste limita" in wp_["motiv"], wp_)
wz = fereastra_strada(ref_d, S, {**cfg, "zona": {"raza_max_m": 1}}, None, NET)
ok(wz["status"] == "in_afara_zonei" and "peste limita" in wz["motiv"] and wz["punct"], wz)
# geocodeaza cu ancore: poziția numărului vine din ancore; fereastra atașată; celelalte chei neschimbate
gz = geocodeaza(ad(strada=V, numar="15"), S, cfg, NET, ANC)
ok(gz["metoda"] == "osm_cache" and gz["precizie_m"] == CS["precizie_ancore_m"] and gz["fereastra"]["metoda"] == "ancore" and gz["acuratete"] == A["strada_numar"], gz)
ok(set(gz) == {"status", "lat", "lon", "precizie_m", "metoda", "acuratete", "motiv", "fereastra"}, set(gz))
ok("fereastra" in g(strada="Strada Liviu Rebreanu") and "fereastra" not in g(strada="Strada Inexistenta Zzz"), "cheia fereastra doar la gasit")

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
    if res["status"] == "gasit" and a["acuratete_tinta"] == "strada_numar":
        # coordonatele așteptate din geo-test.json (data/reports, ale lui C) vin din vechea fracție N/100; V6 le înlocuiește cu
        # convenția de numerotare, deci verificăm metoda, nu toleranța veche (diferența apare în tabelul tipărit)
        ok(res["fereastra"]["metoda"] == "conventie" and res["precizie_m"] == cfg["cautare_strada"]["precizie_conventie_m"], (c["id"], res))
    else:
        ok(d is None or d <= a["toleranta_m"], (c["id"], d, a["toleranta_m"]))
    if res["status"] == "gasit":  # acuratețea = cheia din tabel x factor_ai_fuzzy dacă a ales AI
        fc = FC if a["acuratete_tinta"] == "strada_numar" else 1  # V6: număr fără ancore = convenție
        ok(res["acuratete"] == round(A[a["acuratete_tinta"]] * fc * (cfg["geocodare"]["factor_ai_fuzzy"] if c["ai_strada"] else 1), 3), (c["id"], res))
    TAB.append((c["id"], res["status"], res["metoda"], None if d is None else round(d)))
for t in TAB:
    print(*t)
print(f"OK: {N} verificări")
