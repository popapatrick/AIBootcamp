"""A6: date de aur (golden) pentru logica sesiunii 3. Coordonatele așteptate se CALCULEAZĂ din cache-ul OSM
(`osm.strazi()`), rețea (`network.geojson`) și `weights.yaml`; nu sunt scrise de mână. Date FICTIVE.

Rulare: .venv/bin/python data/golden/genereaza_golden.py  (determinist; rescrie cele 4 fișiere JSON din folder).
Format comun per caz: {id, intrare, asteptat, toleranta, nota}.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.engine import osm  # noqa: E402
from backend.engine.config import load_weights  # noqa: E402
from backend.engine.network import dist_m  # noqa: E402

AICI = Path(__file__).parent
CFG = load_weights()
G, Z, R = CFG["geocodare"], CFG["zona"], CFG["racordare"]
NET = json.loads((ROOT / "data/model/network.geojson").read_text(encoding="utf-8"))
NODURI = [(f["properties"]["id"], f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0])
          for f in NET["features"] if f["geometry"]["type"] == "Point"]
CENTRU = (sum(n[1] for n in NODURI) / len(NODURI), sum(n[2] for n in NODURI) / len(NODURI))
STRAZI = [s for s in osm.strazi() if s["nume"]]
R2 = lambda x: round(x, 6)  # noqa: E731


def cai(nume):
    return [s["puncte"] for s in STRAZI if s["nume"] == nume]


def lung(p):
    return sum(dist_m(a, b) for a, b in zip(p, p[1:]))


def la_fractie(p, f):
    t, acc = lung(p) * f, 0.0
    for a, b in zip(p, p[1:]):
        d = dist_m(a, b)
        if d and acc + d >= t:
            u = (t - acc) / d
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        acc += d
    return tuple(p[-1])


def mijloc(nume):
    """Punct reprezentativ: mijlocul celei mai lungi căi cu acest nume."""
    return la_fractie(max(cai(nume), key=lung), 0.5)


def dist_la_strada(pt, nume):
    """Distanța minimă (m) de la pt la orice cale cu acest nume (vârfuri + mijloace de segment, aproximare ~ <2 m)."""
    best = 1e18
    for p in cai(nume):
        for a, b in zip(p, p[1:]):
            L = dist_m(a, b)
            for k in range(0, max(1, int(L // 2)) + 1):
                f = k / max(1, int(L // 2))
                best = min(best, dist_m(pt, (a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1]))))
    return best


def intersectie(n1, n2):
    """Perechea de vârfuri cele mai apropiate între două străzi: (punct mijloc, distanță m)."""
    best = (1e18, None)
    p, q = max(cai(n1), key=lung), max(cai(n2), key=lung)  # ca backend.geo: doar cea mai lungă cale
    for a in p:
        for b in q:
            d = dist_m(a, b)
            if d < best[0]:
                best = (d, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
    return best[1], best[0]


def nod_apropiat(pt):
    n = min(NODURI, key=lambda x: dist_m(pt, (x[1], x[2])))
    return n[0], dist_m(pt, (n[1], n[2]))


def deplasat(pt, d_m, unghi_deg):
    a = math.radians(unghi_deg)
    return (pt[0] + d_m * math.cos(a) / 111_320, pt[1] + d_m * math.sin(a) / (111_320 * math.cos(math.radians(pt[0]))))


def caz(id_, intrare, asteptat, toleranta, nota):
    return {"id": id_, "intrare": intrare, "asteptat": asteptat, "toleranta": toleranta, "nota": nota}


def pe_strada(nume, dmax=30):
    return {"metrica": "pe_strada", "strada": nume, "dist_max_m": dmax}


# ---------------- geocodare ----------------
def geocodare():
    A, out = G["acuratete"], []
    s1, s2, s3 = "Strada Tineretului", "Strada Liviu Rebreanu", "Strada Orhideelor"
    m1, m2 = mijloc(s1), mijloc(s2)
    nid, nla, nlo = NODURI[1]
    pt_i, d_i = intersectie("Strada Speranței", "Strada Bălții")
    pt_j, d_j = intersectie("Strada Viilor", "Strada Soarelui")
    assert d_i <= 10 and d_j <= 10, (d_i, d_j)

    def g(id_, nivel, text, structurat, status, metoda, pct, tol, nota, mult=1.0, extra=None):
        a = {"status": status, "metoda": metoda}
        if status == "gasit":
            a.update(lat=R2(pct[0]), lon=R2(pct[1]), nivel=nivel, acuratete=round(A[nivel] * mult, 4),
                     precizie_m_max=G["precizie_reper_m" if nivel == "reper" else "precizie_strada_max_m"])
        else:
            a["acuratete"] = None
        if extra:
            a.update(extra)
        out.append(caz(id_, {"adresa": text, "adresa_structurata": structurat}, a, tol, nota))

    out.append(caz("geo-01-id", {"adresa": f"stâlp {nid} verificat", "adresa_structurata": None},
                   {"status": "gasit", "metoda": "id_existent", "lat": R2(nla), "lon": R2(nlo), "nivel": "id_existent",
                    "acuratete": A["id_existent"], "geocodare_apelata": False},
                   {"metrica": "distanta", "dist_max_m": 1}, "ID existent în rețea: geocodarea nu se apelează; coordonatele sunt ale nodului."))
    out.append(caz("geo-02-coordonate", {"adresa": f"stâlp nou la {R2(m1[0])}, {R2(m1[1])}", "adresa_structurata": None},
                   {"status": "gasit", "metoda": "coordonate", "lat": R2(m1[0]), "lon": R2(m1[1]), "nivel": "coordonate",
                    "acuratete": A["coordonate"], "geocodare_apelata": False},
                   {"metrica": "distanta", "dist_max_m": 1}, "Coordonate explicite în text: nu se apelează geocodarea."))
    g("geo-03-strada-numar", "strada_numar", f"{s1} nr. 12, 1 Decembrie",
      {"strada": s1, "numar": "12", "localitate": "1 Decembrie", "reper": None}, "gasit", "osm_cache", m1, pe_strada(s1),
      "Număr de casă: OSM nu are numere, deci doar 'pe stradă' (nu poziția exactă a lui 12). Referința e mijlocul străzii.")
    g("geo-04-strada-numar-lunga", "strada_numar", f"{s2} 40",
      {"strada": s2, "numar": "40", "localitate": None, "reper": None}, "gasit", "osm_cache", m2, pe_strada(s2),
      "Două căi OSM cu același nume; orice punct pe oricare e acceptat.")
    g("geo-05-intersectie", "intersectie", "Strada Speranței colț cu Strada Bălții",
      {"strada": "Strada Speranței colț cu Strada Bălții", "numar": None, "localitate": None, "reper": None},
      "gasit", "osm_cache", pt_i, {"metrica": "distanta", "dist_max_m": 30},
      f"Vârfurile cele mai apropiate ale celor două străzi (la {d_i:.1f} m între ele).")
    g("geo-06-intersectie-2", "intersectie", "Strada Viilor & Strada Soarelui",
      {"strada": "Strada Viilor & Strada Soarelui", "numar": None, "localitate": None, "reper": None},
      "gasit", "osm_cache", pt_j, {"metrica": "distanta", "dist_max_m": 30}, f"Intersecție, vârfuri la {d_j:.1f} m.")
    g("geo-07-strada", "strada", f"pe {s3}, în dreptul curții",
      {"strada": s3, "numar": None, "localitate": None, "reper": "în dreptul curții"}, "gasit", "osm_cache",
      mijloc(s3), pe_strada(s3), "Doar stradă; reperul 'în dreptul curții' nu e localizabil.")
    g("geo-08-fara-diacritice", "strada", "str ulmului", {"strada": "str ulmului", "numar": None, "localitate": None, "reper": None},
      "gasit", "osm_cache", mijloc("Strada Ulmului"), pe_strada("Strada Ulmului"),
      "Fără diacritice și prefix prescurtat: normalizarea deterministă o găsește (nu AI).")
    g("geo-09-ortografie", "strada", "str liviu rebrianu",
      {"strada": "str liviu rebrianu", "numar": None, "localitate": None, "reper": None}, "gasit", "ai_estimare", m2,
      pe_strada(s2), "Ortografie greșită: AI alege din cache; acuratețea se înmulțește cu factor_ai_fuzzy.", mult=G["factor_ai_fuzzy"])
    g("geo-10-vag-reper-strada", "strada", f"lângă școală, pe {s3}",
      {"strada": s3, "numar": None, "localitate": None, "reper": "lângă școală"}, "gasit", "osm_cache", mijloc(s3),
      pe_strada(s3), "Stradă + reper: cel mai bun localizator e strada (0,40), nu reperul.")
    out.append(caz("geo-11-doar-reper", {"adresa": "lângă școală", "adresa_structurata": {"strada": None, "numar": None, "localitate": None, "reper": "lângă școală"}},
                   {"status": "necunoscut", "metoda": None, "acuratete": None, "acuratete_tabel_reper": A["reper"]}, {},
                   "Doar reper fără stradă: nu avem repere în cache, deci 'necunoscut' (nu inventăm coordonate); acuratețea de tabel ar fi cea mai mică (reper)."))
    out.append(caz("geo-12-strada-necunoscuta", {"adresa": "Strada Inexistentei 5", "adresa_structurata": {"strada": "Strada Inexistentei", "numar": "5", "localitate": None, "reper": None}},
                   {"status": "necunoscut", "metoda": None, "acuratete": None}, {}, "Nicio stradă din cache: fără coordonate, cu motiv."))
    out.append(caz("geo-13-gol", {"adresa": "", "adresa_structurata": None}, {"status": "necunoscut", "metoda": None, "acuratete": None}, {}, "Fără text: necunoscut."))
    return out


# ---------------- trace ----------------
def trace():
    t = CFG["trace"]
    out = []
    pcts = {"tineretului": mijloc("Strada Tineretului"), "bălții": mijloc("Strada Bălții"), "rebreanu": mijloc("Strada Liviu Rebreanu")}

    def c(id_, nume_pct, strada, params, seed, asteptat, nota):
        p = pcts[nume_pct]
        out.append(caz(id_, {"punct": {"lat": R2(p[0]), "lon": R2(p[1])}, "adresa": strada, "params": params, "seed": seed},
                       asteptat, {"oprire_la_m": 15, "durata_min": 2}, nota))

    c("trace-01-implicit", "tineretului", "Strada Tineretului", {},
      "t-01", {"oprire_gasita": True, "durata_min_cel_putin": t["durata_min_min"], "oprire_la_punct_m_max": 15, "contradictie": False, "sens_acuratete": "creste"},
      "Parametri impliciți (trace_generat): oprire generată 12 min, zgomot 5 m, acoperire 0,9, decalaj 0. Cu zgomot 5 m grupul de opriri se poate rupe (rază 12 m): se verifică doar durata >= durata_min_min.")
    c("trace-02-oprire-lunga-zgomot-mic", "bălții", "Strada Bălții", {"durata_oprire_min": 15, "zgomot_m": 3},
      "t-02", {"oprire_gasita": True, "durata_min_cel_putin": 12, "oprire_la_punct_m_max": 12, "contradictie": False, "sens_acuratete": "creste"},
      "Scenariul din spec: 15 min, 3 m zgomot, oprire consistentă cu adresa: bonus, fără a depăși bonus_max.")
    c("trace-03-zgomot-mare", "tineretului", "Strada Tineretului", {"zgomot_m": 30}, "t-03",
      {"oprire_gasita": None, "oprire_la_punct_m_max": None, "contradictie": False, "sens_acuratete": "scade"},
      f"Zgomot 30 m (> trace.raza_oprire_m={t['raza_oprire_m']}, > zgomot_max_bonus_m): oprirea poate să nu mai fie regăsită; fără bonus. None = nu se verifică.")
    c("trace-04-acoperire-mica", "tineretului", "Strada Tineretului", {"acoperire": 0.3}, "t-04",
      {"oprire_gasita": None, "oprire_la_punct_m_max": None, "contradictie": False, "sens_acuratete": "scade"},
      "Acoperire 0,3 (< acoperire_min): penalizare; oprirea poate fi ratată (puncte puține).")
    c("trace-05-decalaj-contradictie", "rebreanu", "Strada Liviu Rebreanu", {"decalaj_m": 80, "zgomot_m": 3}, "t-05",
      {"oprire_gasita": True, "oprire_la_punct_m": 80, "contradictie": True, "sens_acuratete": "scade"},
      f"Oprirea la 80 m de adresă (> toleranta_adresa_m={CFG['trace_generat']['toleranta_adresa_m']}): contradicție; 'De ce?' o arată.")
    c("trace-06-oprire-scurta", "tineretului", "Strada Tineretului", {"durata_oprire_min": 2}, "t-06",
      {"oprire_gasita": False, "contradictie": False, "sens_acuratete": "fara_bonus"},
      f"Oprire de 2 min < trace.durata_min_min={t['durata_min_min']}: nu e oprire, deci fără bonus și fără contradicție.")
    c("trace-07-determinism", "tineretului", "Strada Tineretului", {}, "t-01",
      {"identic_cu": "trace-01-implicit"}, "Același seed și aceiași parametri = același traseu (octet cu octet).")
    for x in out:
        x["toleranta"] = {"oprire_la_m": 15, "durata_min": 2, "decalaj_m": 15}
    return out


# ---------------- racordare ----------------
def racordare():
    """Case puse pe vârfuri de stradă OSM alese după distanța la cel mai apropiat nod, plus puncte la distanțe mari."""
    varfuri = sorted({tuple(p) for s in STRAZI for p in s["puncte"]})
    out = []

    def alege(lo, hi, dupa=None):
        c = [(nod_apropiat(v)[1], v) for v in varfuri if lo <= nod_apropiat(v)[1] <= hi and dist_m(v, CENTRU) < Z["raza_max_m"]]
        assert c, (lo, hi)
        d, v = c[len(c) // 2]  # median al candidaților (stabil)
        return v

    def r(id_, pt, treapta, status, slaba, nota, net=None, zona=True):
        nid, d = nod_apropiat(pt)
        out.append(caz(id_, {"locatie": {"lat": R2(pt[0]), "lon": R2(pt[1])}, "net": net or "retea_start"},
                       {"status": status, "status_in": ["lant", "linie_dreapta"] if treapta in (1, 2) else [status], "treapta": treapta, "slaba": slaba, "nod_start": nid if net is None else None,
                        "distanta_directa_nod_m": round(d, 1) if net is None else None, "in_zona": zona,
                        "neaplicat": status == "neaplicat"}, {"distanta_directa_nod_m": 5}, nota + " Pe stradă (status lant) distanta_m din prezice_lant e lungimea traseului, >= distanța directă."))

    p1, p2 = alege(40, 120), alege(200, 380)
    p3 = deplasat(CENTRU, 1500, 200)  # ~1,5 km SV de centroid, în zonă, departe de orice nod
    p3b = deplasat(CENTRU, 2900, 90)
    assert nod_apropiat(p3)[1] > R["raza_extinsa_m"] and nod_apropiat(p3b)[1] > R["raza_extinsa_m"]
    r("rac-01-treapta1", p1, 1, "lant", False, f"Nod în raza normală ({R['raza_nod_m']} m): lanț pe stradă sau linie; predicție normală (scor peste prag_afisare).")
    r("rac-02-treapta2", p2, 2, "lant", None, f"Nod între {R['raza_nod_m']} și {R['raza_extinsa_m']} m: raza extinsă, factor_raza_extinsa; 'slaba' depinde de calibrare (None = nu se verifică).")
    r("rac-03-treapta3", p3, 3, "linie_dreapta", True, f"Niciun nod la < {R['raza_extinsa_m']} m: linie dreaptă la cel mai apropiat nod din zonă; predicție slabă.")
    r("rac-04-treapta3-limita-zonei", p3b, 3, "linie_dreapta", True, "La ~2,9 km de centroid (în zonă): tot predicție slabă, nu neaplicat.")
    r("rac-05-treapta4-doar-casa", p1, 4, "fara_nod", True, "Rețea fără niciun nod utilizabil: casa rămâne pe hartă, predicție fără lanț, cu motiv; nu neaplicat.", net="gol")
    p6 = deplasat(CENTRU, 3100, 90)
    r("rac-06-in-afara-zonei", p6, None, "neaplicat", None, "La ~3,1 km de centroid: în afara zonei, neaplicat (eronat_prototip). Decizia o ia motorul (zona_ok); prezice_lant singur ar întoarce treapta 3.", zona=False)
    out.append(caz("rac-07-fara-locatie", {"locatie": None, "net": "retea_start", "surse": {"coordonate": None, "clic": None, "adresa": None, "trace": None, "operator": None}},
                   {"status": "neaplicat", "treapta": None, "slaba": None, "motiv": "lipsește locația casei", "surse_incercate": True},
                   {}, "Niciun indiciu de locație: singurul caz neaplicat (alături de zonă), cu lista surselor încercate."))
    return out


# ---------------- în afara zonei ----------------
def zona():
    out = []
    for id_, d, sursa, nota in (
            ("zona-01-40km", 40_000, "text_liber", "Coordonate la 40 km: eronat_prototip, nu intră în model."),
            ("zona-02-5km", 5_000, "formular", "La 5 km: în afară; o geocodare care ar da 5 km = in_afara_zonei."),
            ("zona-03-3100m", 3_100, "tableta_coordonate", "Chiar peste limită (3000 m)."),
            ("zona-04-2900m", 2_900, "tableta_coordonate", "Chiar sub limită: în zonă, se aplică regulile normale."),
            ("zona-05-om-teren-40km", 40_000, "om_teren", "Fără excepții pe sursă: decizie om_teren la 40 km = eronat."),
            ("zona-06-apel-client-4km", 4_000, "apel_client", "Apel client la 4 km: eronat; fără excepții pe sursă."),
            ("zona-07-centru", 0, "formular", "Exact centroidul: în zonă.")):
        p = deplasat(CENTRU, d, 45) if d else CENTRU
        dd = dist_m(p, CENTRU)
        out.append(caz(id_, {"sursa": sursa, "lat": R2(p[0]), "lon": R2(p[1])},
                       {"eronat_prototip": dd > Z["raza_max_m"], "semnal": "in_afara_zonei_prototip" if dd > Z["raza_max_m"] else None,
                        "decizie": "neaplicat" if dd > Z["raza_max_m"] else "normala", "distanta_m": round(dd), "raza_m": Z["raza_max_m"]},
                       {"distanta_m": 20}, nota))
    return out


# ---------------- liste pentru banc (data/golden/*.json) ----------------
DATA = "2026-11-14"
# Doar cheile pe care le compară bancul: tip, decizie, nivel, origine, slaba, treapta, eronat_prototip, element_id.
# Valorile vin din specificații (nu din rularea motorului); necalibrate: bancul arată diferențele.


def _c(det, id_):
    return next(c for c in det if c["id"] == id_)


def _item(id_, sursa, text, asteptat, det_caz=None):
    x = {"id": id_, "sursa": sursa, "text": text, "data": DATA, "asteptat": asteptat}
    if det_caz:
        x["asteptat_detaliu"] = {"fisier": det_caz[0], "caz": det_caz[1], "asteptat": det_caz[2]["asteptat"],
                                 "toleranta": det_caz[2]["toleranta"]}
    return x


def lista_geocodare(det):
    nid = NODURI[1][0]
    f = lambda id_: ("detaliu/geocodare.json", id_, _c(det, id_))  # noqa: E731
    c2 = _c(det, "geo-02-coordonate")["asteptat"]
    return [
        _item("g-01-id", "mentenanta", f"verificat stalp {nid}, izolator ok, nimic de facut", {"tip": "verificare", "element_id": nid}, f("geo-01-id")),
        _item("g-02-coordonate", "mentenanta", f"stalp nou montat la {c2['lat']:.5f}, {c2['lon']:.5f} pe Strada Tineretului, echipa 2",
              {"tip": "nod_lipsa", "eronat_prototip": False}, f("geo-02-coordonate")),
        _item("g-03-strada-numar", "mentenanta", "Avem un stalp nou la nr 12 pe Strada Tineretului, lipseste din GIS. echipa 3",
              {"tip": "nod_lipsa", "nivel": "predictie", "eronat_prototip": False}, f("geo-03-strada-numar")),
        _item("g-04-intersectie", "mentenanta", "stalp nou la coltul Strada Speranței colț cu Strada Bălții, nu e in GIS",
              {"tip": "nod_lipsa", "nivel": "predictie", "eronat_prototip": False}, f("geo-05-intersectie")),
        _item("g-05-strada", "mentenanta", "stalp nou pe Strada Orhideelor, in dreptul curtii, nu e in GIS",
              {"tip": "nod_lipsa", "nivel": "predictie", "eronat_prototip": False}, f("geo-07-strada")),
        _item("g-06-ortografie", "mentenanta", "stalp nou pe str liviu rebrianu, lipseste din GIS",
              {"tip": "nod_lipsa", "nivel": "de_verificat", "eronat_prototip": False}, f("geo-09-ortografie")),
        _item("g-07-doar-reper", "mentenanta", "stalp nou langa scoala, lipseste din GIS",
              {"tip": "nod_lipsa", "nivel": "de_verificat"}, f("geo-11-doar-reper")),
        _item("g-08-strada-necunoscuta", "mentenanta", "stalp nou la nr 5 pe Strada Inexistentei, lipseste din GIS",
              {"tip": "nod_lipsa", "nivel": "de_verificat"}, f("geo-12-strada-necunoscuta")),
    ]


def lista_racordare(det):
    def rac(id_, det_id, treapta, slaba, rest=""):
        c = _c(det, det_id)
        l = c["intrare"]["locatie"]
        a = {"tip": "cerere_racordare", "eronat_prototip": treapta is None and det_id == "rac-06-in-afara-zonei"}
        if treapta is not None:
            a["treapta"] = treapta
        if slaba is not None:
            a["slaba"] = slaba
        if det_id == "rac-06-in-afara-zonei":
            a["decizie"] = "neaplicat"
        return _item(id_, "racordari", f"CERERE RACORDARE: casa noua, consum 5 kW, coordonate {l['lat']:.5f}, {l['lon']:.5f}. {rest}".strip(), a,
                     ("detaliu/racordare.json", det_id, c))
    return [
        rac("r-01-treapta1", "rac-01-treapta1", 1, False),
        rac("r-02-treapta2", "rac-02-treapta2", 2, None),
        rac("r-03-treapta3", "rac-03-treapta3", 3, True),
        rac("r-04-treapta3-limita", "rac-04-treapta3-limita-zonei", 3, True),
        rac("r-06-in-afara-zonei", "rac-06-in-afara-zonei", None, None),
        _item("r-07-fara-locatie", "racordari", "cerere de racordare pentru o casa noua, consum 5 kW. nu stiu adresa exacta",
              {"tip": "cerere_racordare", "decizie": "neaplicat"}, ("detaliu/racordare.json", "rac-07-fara-locatie", _c(det, "rac-07-fara-locatie"))),
    ]


def lista_zona(det):
    TXT = {"text_liber": ("mentenanta", "stalp nou montat la {la:.5f}, {lo:.5f}, echipa 2"),
           "formular": ("investitii", "FISA INVESTITIE: stalp nou la {la:.5f}, {lo:.5f}, executat"),
           "tableta_coordonate": ("mentenanta", "Tableta GPS {la:.5f}, {lo:.5f}: stalp nou montat"),
           "apel_client": ("apel_client", "Operator: Alo? Client (CL-52001): nu avem lumina. Coord tel {la:.5f}, {lo:.5f}. status semnalat")}
    out = []
    for c in det:
        sursa, t = TXT.get(c["intrare"]["sursa"], (None, None))
        if not sursa:  # om_teren: decizia nu poartă coordonate în text; rămâne doar în detaliu
            continue
        i, a = c["intrare"], c["asteptat"]
        ast = {"eronat_prototip": a["eronat_prototip"]}
        if a["eronat_prototip"]:
            ast["decizie"] = "neaplicat"
        out.append(_item(c["id"].replace("zona-", "z-"), sursa, t.format(la=i["lat"], lo=i["lon"]), ast, ("detaliu/zona.json", c["id"], c)))
    return out


def scrie(nume, cazuri, descriere):
    ids = [c["id"] for c in cazuri]
    assert len(ids) == len(set(ids)), nume
    (AICI / "detaliu").mkdir(exist_ok=True)
    doc = {"_nota": f"date FICTIVE; {descriere}; generat de genereaza_golden.py", "centru_zona": {"lat": R2(CENTRU[0]), "lon": R2(CENTRU[1])},
           "raza_zona_m": Z["raza_max_m"], "cazuri": cazuri}
    (AICI / "detaliu" / f"{nume}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("detaliu/" + nume, len(cazuri))


def scrie_lista(nume, lista):
    ids = [x["id"] for x in lista]
    assert len(ids) == len(set(ids)), nume
    assert all(set(x["asteptat"]) <= {"tip", "decizie", "nivel", "origine", "slaba", "treapta", "eronat_prototip", "element_id"} for x in lista)
    (AICI / f"{nume}.json").write_text(json.dumps(lista, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(nume, len(lista))


if __name__ == "__main__":
    gc, tr, rc, zn = geocodare(), trace(), racordare(), zona()
    scrie("geocodare", gc, "adrese de la foarte standardizat la vag")
    scrie("trace", tr, "parametri de traseu generat și redescoperire")
    scrie("racordare", rc, "case și treptele 1-4")
    scrie("zona", zn, "puncte față de limita de 3 km")
    scrie_lista("geocodare", lista_geocodare(gc))
    scrie_lista("racordare", lista_racordare(rc))
    scrie_lista("zona", lista_zona(zn))
