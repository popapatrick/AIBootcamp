"""Generează data/reports/geo-test.json: adrese FICTIVE cu coordonate așteptate calculate din geometria OSM (osm.strazi()).

    .venv/bin/python data/reports/genereaza_geo_test.py

Convenții (spec geocodare-adresa): stradă fără număr = mijlocul (pe lungime) al celui mai lung tronson cu acel nume; cu număr N =
interpolare la fracția clamp(N/100, 0.1, 0.9) din acel tronson (OSM nu are numere de casă; fără par/impar); intersecție = nodul comun
al celor două străzi, a doua stradă dată în `reper` (cum o extrage A); id/coordonate = punctul din network.geojson, dar geocodarea
NU se apelează pentru ele (`geo_apelat: false`, motorul le tratează). `ai: true` = cazul cere AI (ortografie); testul îl simulează.
"""
import json
from pathlib import Path

from backend.engine import osm
from backend.engine.network import dist_m

R = Path(__file__).resolve().parent
NET = json.loads((R.parent / "model" / "network.geojson").read_text(encoding="utf-8"))
STR = [s for s in osm.strazi() if s["nume"]]


def mijloc(nume, nr=None):
    frac = 0.5 if nr is None else min(max(int(nr) / 100, 0.1), 0.9)
    p = max((s["puncte"] for s in STR if s["nume"] == nume), key=lambda q: sum(dist_m(a, b) for a, b in zip(q, q[1:])))
    tot, acc = sum(dist_m(a, b) for a, b in zip(p, p[1:])), 0
    for a, b in zip(p, p[1:]):
        d = dist_m(a, b)
        if acc + d >= tot * frac:
            f = (tot * frac - acc) / d
            return a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])
        acc += d


def intersectie(n1, n2):
    comune = [q for a in STR if a["nume"] == n1 for b in STR if b["nume"] == n2 for q in a["puncte"] if q in b["puncte"]]
    return comune[0]


def nod(i):
    lon, lat = next(f["geometry"]["coordinates"] for f in NET["features"] if f["properties"]["id"] == i)
    return lat, lon


def ad(strada=None, numar=None, reper=None):
    return {"strada": strada, "numar": numar, "localitate": None, "reper": reper}


# (id, grad, sursa, data, text, adresa_structurata, (lat, lon)|None, toleranta_m, acuratete_tinta, plafon_incredere, nota)
N1, N2 = "6925190", "0287329"
RB, CR, FG = "Strada Liviu Rebreanu", "Strada Crinului", "Strada Fagului"
C = [
    ("gt-01", "id", "mentenanta", "2026-09-14", f"Verificare nod {N1}, fără defecte.", ad(), nod(N1), 5, "id_existent", 1.0, "cod existent: geocodarea nu se apelează (geo = necunoscut; motorul potrivește pe ID)"),
    ("gt-02", "coordonate", "mentenanta", "2026-09-14", "Control în teren la coordonatele {:.6f}, {:.6f}: stâlp înclinat.".format(*nod(N2)), ad(), nod(N2), 5, "coordonate", 0.9, "coordonate explicite: geocodarea nu se apelează (geo = necunoscut; motorul potrivește pe coordonate)"),
    ("gt-03", "strada_numar", "apel_client", "2026-10-02", "Fără curent la Strada Liviu Rebreanu nr. 12, Popești.", {**ad(RB, "12"), "localitate": "Popești"}, mijloc(RB, 12), 30, "strada_numar", 0.7, "interpolat la N/100 pe cea mai lungă cale"),
    ("gt-04", "strada_numar", "racordari", "2026-10-03", "Cerere racordare casă, Strada Fagului nr. 7.", ad(FG, "7"), mijloc(FG, 7), 30, "strada_numar", 0.7, "interpolat (N=7 -> fracția 0.1)"),
    ("gt-05", "strada_numar", "apel_client", "2026-10-05", "Scântei la Strada Tineretului 18.", ad("Strada Tineretului", "18"), mijloc("Strada Tineretului", 18), 30, "strada_numar", 0.7, "interpolat la 0.18"),
    ("gt-06", "intersectie", "apel_client", "2026-10-06", "Nu avem curent la intersecția Strada Liviu Rebreanu cu Strada Crinului.", ad(RB, reper="intersecția cu Strada Crinului"), intersectie(RB, CR), 30, "intersectie", 0.5, "nod comun; a doua stradă în reper; plafonul 0.5 (intersecția nu e în tabelul de plafoane)"),
    ("gt-07", "intersectie", "mentenanta", "2026-10-07", "Inspecție la colțul dintre Strada Viilor și Strada Carpati, cablu vizibil uzat.", ad("Strada Viilor", reper="colțul cu Strada Carpati"), intersectie("Strada Viilor", "Strada Carpati"), 30, "intersectie", 0.5, "nod comun"),
    ("gt-08", "strada", "apel_client", "2026-10-12", "Lumina pâlpâie pe Strada Liliacului.", ad("Strada Liliacului"), mijloc("Strada Liliacului"), 150, "strada", 0.5, "mijlocul străzii"),
    ("gt-09", "strada", "apel_client", "2026-10-14", "Stâlp căzut pe Strada Crinului.", ad(CR), mijloc(CR), 150, "strada", 0.5, "mijlocul străzii"),
    ("gt-10", "strada_ortografie", "apel_client", "2026-10-19", "Defect cablu pe str liviu rebrianu nr 5.", ad("str liviu rebrianu", "5"), mijloc(RB, 5), 30, "strada_numar", 0.45, "ortografie greșită: AI alege din cache, acuratețe x factor_ai_fuzzy; fără CLI = necunoscut"),
    ("gt-11", "strada_ortografie", "apel_client", "2026-10-20", "Fără curent pe str. I. L. Caragiale.", ad("str. I. L. Caragiale"), mijloc("Strada Ion Luca Caragiale"), 150, "strada", 0.4, "abreviere: AI alege din cache; fără CLI = necunoscut"),
    ("gt-12", "strada_ortografie", "apel_client", "2026-10-21", "Scântei pe sos principala, aproape de Carpati.", ad("sos principala", None, "aproape de Carpati"), intersectie("Strada Carpati", "Șoseaua Principală"), 30, "intersectie", 0.4, "stradă fără diacritice + reper cu a doua stradă = intersecție"),
    ("gt-13", "reper", "apel_client", "2026-10-27", "Nu e curent lângă școală.", ad(None, None, "lângă școală"), None, None, "reper", 0.3, "reper vag fără locație în cache: necunoscut, predicție, nu se aplică"),
    ("gt-14", "necunoscut", "apel_client", "2026-11-04", "Fără curent pe Strada Mihai Eminescu nr. 3.", ad("Strada Mihai Eminescu", "3"), None, None, "strada_numar", 0.7, "stradă inexistentă în zonă: necunoscut sau in_afara_zonei, fără coordonate inventate"),
    ("gt-15", "lipsa", "apel_client", "2026-11-05", "Nu avem curent, vă rog trimiteți pe cineva.", None, None, None, None, 0.2, "fără localizator: adresa_structurata null"),
]

NU_GEO = {"gt-01", "gt-02"}  # id / coordonate: geocodarea nu se apelează
AI = {"gt-10": RB, "gt-11": "Strada Ion Luca Caragiale"}  # strada pe care o alege AI (simulat în test)

out = [{"id": i, "grad": g, "sursa": s, "data": d, "text": t, "adresa_structurata_asteptata": a,
        "asteptat": {"status": "gasit" if c else "necunoscut", "lat": round(c[0], 6) if c else None, "lon": round(c[1], 6) if c else None,
                     "status_geo": "necunoscut" if i in NU_GEO else ("gasit" if c else "necunoscut"), "toleranta_m": tol, "acuratete_tinta": ac},
        "plafon_incredere": pf, "geo_apelat": i not in NU_GEO, "ai_strada": AI.get(i), "nota": n} for i, g, s, d, t, a, c, tol, ac, pf, n in C]
doc = {"_nota": "DATE FICTIVE. Coordonatele așteptate sunt calculate din geometria OSM (genereaza_geo_test.py), nu ghicite.", "adrese": out}
(R / "geo-test.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
print(len(out), "adrese")
