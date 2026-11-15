"""Verificări pentru modelul de acuratețe din sesiunea 4 (V1 + V2): GIS stabil, SIM-* din rapoarte mai vechi,
plafon după sursa locației, prag 0,50 la rapoarte executate, benzi de culoare; și căutarea pe stradă (V6, partea 2: motorul).
Rulează: EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune4. Date FICTIVE."""
from __future__ import annotations

import json

from backend.engine import osm
from backend.engine import scoring as S
from backend.engine.config import load_weights
from backend.engine.model import GridModel

OK: list[bool] = []


def verifica(nume, cond, detaliu=""):
    OK.append(bool(cond))
    print(("OK  " if cond else "FAIL"), nume, detaliu)


def mk() -> GridModel:
    m = GridModel()
    m.traseu_fn = osm.traseu_fn()
    return m


def ev(i, data, echipa, tip, status="executat", ref=None, det=None, sursa="tableta_coordonate", inc=0.9, forma="campuri"):
    e = {"event_id": i, "echipa_sursa": echipa, "tip": tip, "status": status, "data": data, "forma_sursa": forma,
         "incredere_extractie": inc, "text_original": "test", "referinta": ref or {}, "detalii": det or {}}
    if sursa:
        e["tip_sursa_pondere"] = sursa
    return e


def snap(m, data, eid):
    return next((f["properties"] for f in m.snapshot(data)["features"] if f["properties"]["element_id"] == eid), None)


def benzi(m, data, filtru):
    """{banda: număr} pentru elementele din snapshot la `data` care trec de `filtru(element_id)`."""
    out = {"verde": 0, "galben": 0, "portocaliu": 0, "rosu": 0}
    for f in m.snapshot(data)["features"]:
        if filtru(f["properties"]["element_id"]):
            out[f["properties"]["banda"]] += 1
    return out


def geo_strada_numar(lat, lon, w):
    """Rezultat de geocodare „stradă + număr” (cum îl produce backend.geo), pentru un raport de test."""
    return {"lat": lat, "lon": lon, "precizie_m": 200, "metoda": "osm_cache", "acuratete": w["geocodare"]["acuratete"]["strada_numar"],
            "motiv": "Strada Viilor nr. 12, interpolat pe stradă (potrivire exactă a numelui)"}


def r_adr(strada, numar=None, indiciu=None, reper=None, **extra):
    """Referință cu adresă structurată (fără ID, fără coordonate), cum o produce extracția."""
    ad = {"strada": strada, "numar": numar, "localitate": None, "reper": reper}
    if indiciu:
        ad["indiciu"] = indiciu
    return {"adresa_structurata": ad, **extra}


def pas(t, nume):
    return next((p for p in t["pasi"] if p["nume"] == nume), None)


def teste_cautare_strada() -> None:
    """V6, partea 2: fereastra pe stradă -> candidați -> potrivit / predicție / de verificat / element nou / pin; ancore."""
    # --- 1 candidat în fereastră: potrivit pe nod, nu neaplicat
    m = mk()
    t = m.apply_event(ev("CS-1", "2026-09-10", "mentenanta", "avarie_semnalata", ref=r_adr("Strada Crinului", "60", {"tip": "numar", "numar": "60"})))
    cs, pm = pas(t, "cautare_strada"), pas(t, "potrivire")["rezultat"]
    nod1 = cs["rezultat"]["ales"] if cs else None
    verifica("căutare: 1 nod în fereastră (Strada Crinului nr. 60) -> potrivit pe el, metoda cautare_strada, nu neaplicat",
             cs and len(cs["rezultat"]["candidati"]) == 1 and nod1 and pm["status"] == "potrivit" and pm["element_id"] == nod1
             and pm["metoda"] == "cautare_strada" and pm["calitate"] == m.w["cautare_strada"]["calitate_cautare_unic"]
             and t["decizie"] != "neaplicat" and [p["nume"] for p in t["pasi"]].index("cautare_strada") < [p["nume"] for p in t["pasi"]].index("potrivire"),
             f"{t['decizie']} {nod1}")
    r = cs["rezultat"]
    verifica("căutare: pasul cautare_strada are câmpurile promise (strada, de_la_m, pana_la_m, punct, precizie_m, metoda, indiciu.text, ancore, candidati, ales)",
             all(k in r for k in ("strada", "de_la_m", "pana_la_m", "punct", "precizie_m", "metoda", "indiciu", "ancore", "candidati", "ales", "linie", "motiv"))
             and r["indiciu"]["text"] == "nr. 60" and r["metoda"] == "conventie" and r["strada"] == "Strada Crinului"
             and {"element_id", "distanta_m", "pozitie_m"} <= set(r["candidati"][0]), json.dumps({k: v for k, v in r.items() if k != "linie"}, ensure_ascii=False)[:400])
    print("    exemplu pas cautare_strada:", json.dumps({k: v for k, v in r.items() if k != "linie"}, ensure_ascii=False))
    mod = t["modificari"][0]
    verifica("căutare: nodul GIS potrivit rămâne GIS (sursa gis, banda verde), fără marcaj de predicție", mod["sursa_locatie"] == "gis" and mod["banda"] == "verde"
             and not mod.get("predictie"), str(mod["banda"]))
    verifica("căutare: ancoră nouă după 1 candidat unic cu număr (Strada Crinului nr. 60 la nodul ales)",
             len(m.ancore) == 1 and m.ancore[0]["numar"] == 60 and m.ancore[0]["strada"] == "Strada Crinului", str(m.ancore))
    # al doilea raport pe aceeași stradă: ancora dă metoda ancore, precizie 40 m
    t2 = m.apply_event(ev("CS-2", "2026-09-11", "mentenanta", "avarie_semnalata", ref=r_adr("Strada Crinului", "64", {"tip": "numar", "numar": "64"})))
    r2 = pas(t2, "cautare_strada")["rezultat"]
    verifica("căutare: al doilea raport pe aceeași stradă folosește ancora (metoda ancore, precizie 40 m, o ancoră în pas)",
             r2["metoda"] == "ancore" and r2["precizie_m"] == 40.0 and len(r2["ancore"]) == 1 and r2["ancore"][0]["numar"] == 60, f"{r2['metoda']} {r2['precizie_m']} {r2['ancore']}")
    # ancoră din coordonate explicite + adresă cu număr (același raport), apoi din ID
    ma = mk()
    el = ma.net["noduri"][nod1]
    ma.apply_event(ev("CS-3", "2026-09-10", "mentenanta", "verificare", ref={**r_adr("Strada Crinului", "60"), "coordonate": {"lat": el["lat"], "lon": el["lon"]}}))
    verifica("ancoră: coordonate explicite + adresă cu număr -> ancoră", len(ma.ancore) == 1 and ma.ancore[0]["numar"] == 60, str(ma.ancore))
    mi = mk()
    mi.apply_event(ev("CS-4", "2026-09-10", "mentenanta", "verificare", ref={**r_adr("Strada Crinului", "60"), "element_id": nod1}))
    verifica("ancoră: potrivit cu ID + adresă cu număr -> ancoră", len(mi.ancore) == 1 and mi.ancore[0]["numar"] == 60, str(mi.ancore))
    mn = mk()
    mn.apply_event(ev("CS-5", "2026-09-10", "mentenanta", "avarie_semnalata", ref=r_adr("Strada Viilor", "12")))
    verifica("ancoră: o predicție/de verificat nu devine ancoră (locație nesigură)", mn.ancore == [], str(mn.ancore))

    # --- 2..4 candidați: predicție pe cel mai apropiat, cu alternative; elementul existent nu își strică starea
    mp = mk()
    inainte = snap(mp, "2026-09-10", "6273923")
    t = mp.apply_event(ev("CS-6", "2026-09-10", "mentenanta", "avarie_semnalata", ref=r_adr("Strada Ion Luca Caragiale", "6", {"tip": "numar", "numar": "6"})))
    cs = pas(t, "cautare_strada")["rezultat"]
    mod = t["modificari"][0]
    pr = mod["predictie"] or {}
    verifica("căutare: 2..4 candidați -> decizie predicție, ales = cel mai apropiat de punct, ceilalți în alternative",
             t["decizie"] == "predictie" and 2 <= len(cs["candidati"]) <= 4 and cs["ales"] == cs["candidati"][0]["element_id"] == mod["element_id"]
             and pr.get("metoda") == "cautare_strada" and len(pr["alternative"]) == len(cs["candidati"]) - 1
             and all({"element_id", "distanta_m", "motiv"} <= set(a) for a in pr["alternative"])
             and t["schimbari"][0]["ce"] == "predictie" and pas(t, "scor")["rezultat"]["decizie"] == "predictie", f"{t['decizie']} {pr.get('alternative')}")
    verifica("căutare: ponderea scade cu distanța (cel mai apropiat > celelalte), scorul propunerii împărțit",
             all(pr["pondere"] >= a["pondere"] for a in pr["alternative"]) and abs(pr["pondere"] + sum(a["pondere"] for a in pr["alternative"]) - 1) < 0.01
             and pr["scor_propunere"] < 0.75, str(pr["pondere"]))
    dupa = snap(mp, "2026-09-10", "6273923")
    verifica("căutare: predicția nu strică elementul existent (nivel și sursă neschimbate, scor neschimbat), apare în snapshot cu predictie.metoda",
             dupa["nivel"] == inainte["nivel"] == "in_model" and dupa["sursa_locatie"] == "gis" and dupa["predictie"]["metoda"] == "cautare_strada"
             and abs(dupa["scor"] - inainte["scor"]) < 1e-9, f"{inainte['nivel']} {dupa['nivel']}")
    # un raport sigur ulterior pe același element șterge marcajul
    t_s = mp.apply_event(ev("CS-7", "2026-09-12", "mentenanta", "verificare", ref={"element_id": "6273923"}))
    verifica("căutare: un raport cu ID pe elementul prezis șterge marcajul de predicție", not snap(mp, "2026-09-12", "6273923")["predictie"])

    # --- peste max_candidati_predictie: de verificat pe fereastră, nimic atins
    mv = mk()
    t = mv.apply_event(ev("CS-8", "2026-09-10", "mentenanta", "avarie_semnalata", ref=r_adr("Strada Viilor", "12")))
    cs = pas(t, "cautare_strada")["rezultat"]
    verifica("căutare: peste max_candidati_predictie (Strada Viilor nr. 12) -> de_verificat pe fereastră, niciun element atins, nu neaplicat",
             t["decizie"] == "de_verificat" and len(cs["candidati"]) > mv.w["cautare_strada"]["max_candidati_predictie"] and cs["ales"] is None
             and t["modificari"] == [] and "Strada Viilor" in pas(t, "scor")["motive"][0], f"{t['decizie']} {len(cs['candidati'])}")

    # --- 0 candidați: nod_lipsa executat „între nr. 10 și 20” -> element nou, aplicat, galben/portocaliu, sursa adresa_numar
    mz = mk()
    t = mz.apply_event(ev("CS-9", "2026-09-10", "mentenanta", "nod_lipsa", "executat", ref=r_adr("Strada Liviu Rebreanu", None, {"tip": "intre", "numar": "10", "numar_2": "20"}), inc=0.95))
    cs = pas(t, "cautare_strada")["rezultat"]
    nod = next(x for x in t["modificari"] if x["tip_element"] == "nod")
    verifica("căutare: 0 candidați + nod_lipsa executat (între nr. 10 și 20) -> element nou la mijloc, aplicat (P1), galben/portocaliu, sursa adresa_numar",
             cs["candidati"] == [] and cs["indiciu"]["text"] == "între nr. 10 și 20" and t["decizie"] == "adaugat" and nod["nivel"] == "in_model"
             and nod["banda"] in ("galben", "portocaliu") and nod["sursa_locatie"] == "adresa_numar" and nod["scor"] <= 0.70
             and abs(mz.net["noduri"][nod["element_id"]]["lat"] - cs["punct"]["lat"]) < 1e-5, f"{t['decizie']} {nod['scor']} {nod['banda']}")
    # --- 0 candidați, tip despre element existent: pin „de verificat” vizibil
    mpin = mk()
    t = mpin.apply_event(ev("CS-10", "2026-09-10", "mentenanta", "avarie_semnalata", ref=r_adr("Strada Liviu Rebreanu", "12", {"tip": "numar", "numar": "12"})))
    pin = next((x for x in t["modificari"] if x["element_id"] == "VER-CS-10"), None)
    sp = snap(mpin, "2026-09-10", "VER-CS-10")
    verifica("căutare: avarie pe stradă cu 0 noduri în fereastră -> pin de verificat VER-<event_id>, scor = plafon x 0,5, vizibil în snapshot",
             t["decizie"] == "de_verificat" and pin and pin["nivel"] == "de_verificat" and abs(pin["scor"] - 0.70 * 0.5) < 1e-9
             and sp and sp["nivel"] == "de_verificat" and "nu există stâlp" in pin["motive"][0]["text"].lower()
             and "Strada Liviu Rebreanu" in pin["motive"][0]["text"], str(pin and (pin["scor"], pin["motive"][0]["text"][:80])))
    ft = next(f for f in mpin.snapshot("2026-09-10")["features"] if f["properties"]["element_id"] == "VER-CS-10")
    verifica("căutare: pinul are geometrie Point la punctul estimat", ft["geometry"]["type"] == "Point", str(ft["geometry"]))

    # --- „lângă stâlpul <ID existent>”: fereastra pornește de la elementul numit
    me = mk()
    t = me.apply_event(ev("CS-11", "2026-09-10", "mentenanta", "avarie_semnalata", ref=r_adr("Strada Crinului", None, {"tip": "element", "element_id": nod1, "distanta_stalpi": 1})))
    cs = pas(t, "cautare_strada")["rezultat"]
    verifica("căutare: „lângă stâlpul <ID>” -> fereastră de ±40 m în jurul lui, elementul numit e candidat, indiciu.text corect",
             cs["indiciu"]["text"] == f"lângă stâlpul {nod1}" and cs["precizie_m"] == 40.0 and cs["metoda"] == "indiciu"
             and nod1 in [c["element_id"] for c in cs["candidati"]] and t["decizie"] != "neaplicat", f"{cs['precizie_m']} {[c['element_id'] for c in cs['candidati']]}")

    # --- doar stradă (fără număr) -> rezultat, nu neaplicat
    md = mk()
    t = md.apply_event(ev("CS-12", "2026-09-10", "mentenanta", "avarie_semnalata", ref=r_adr("Strada Crinului")))
    cs = pas(t, "cautare_strada")["rezultat"]
    verifica("căutare: doar stradă, fără număr -> de_verificat/predicție, nu neaplicat; indiciu.text „doar strada”",
             t["decizie"] in ("predictie", "de_verificat") and cs["indiciu"]["text"] == "doar strada" and cs["metoda"] == "indiciu", f"{t['decizie']}")
    # text liber „Strada Crinului nr. 60” (fără adresă structurată) deduce indiciul prin regex
    tl = mk().apply_event(ev("CS-13", "2026-09-10", "mentenanta", "avarie_semnalata", ref={"adresa": "Strada Crinului, lângă nr. 60"}))
    verifica("căutare: adresă text liber „lângă nr. 60” -> indiciu din regex, rezultat nu neaplicat",
             pas(tl, "cautare_strada")["rezultat"]["indiciu"]["text"] == "lângă nr. 60" and tl["decizie"] != "neaplicat", tl["decizie"])

    # --- fără niciun indiciu de loc -> tot neaplicat; stradă necunoscută -> neaplicat; în afara zonei -> eronat
    tn = mk().apply_event(ev("CS-14", "2026-09-10", "mentenanta", "avarie_semnalata", ref={}))
    verifica("fără niciun indiciu de loc -> neaplicat, fără pas cautare_strada", tn["decizie"] == "neaplicat" and pas(tn, "cautare_strada") is None, tn["decizie"])
    tx = mk().apply_event(ev("CS-15", "2026-09-10", "mentenanta", "avarie_semnalata", ref={"adresa": "Strada Inexistenta Zzz nr. 4"}))
    verifica("stradă necunoscută (nu e în cache) -> neaplicat ca azi", tx["decizie"] == "neaplicat" and pas(tx, "cautare_strada") is None, tx["decizie"])
    tf_ = mk().apply_event(ev("CS-16", "2026-09-10", "mentenanta", "avarie_semnalata", ref=r_adr("Șoseaua Principală", None, {"tip": "capat"})))
    verifica("capătul Șoselei Principale (4 km) -> eronat în prototip, neaplicat", tf_["decizie"] == "neaplicat" and tf_.get("eronat_prototip") is True, tf_["decizie"])
    tc = mk().apply_event(ev("CS-17", "2026-09-10", "mentenanta", "avarie_semnalata", ref={"element_id": nod1}))
    verifica("ID în text: neschimbat (potrivit cu ID, fără căutare pe stradă)", pas(tc, "cautare_strada") is None and pas(tc, "potrivire")["rezultat"]["metoda"] == "id")

    # --- determinism: același set de rapoarte, de două ori, același rezultat
    def ruleaza():
        mm = mk()
        out = []
        for i, (st, nr, ind) in enumerate([("Strada Crinului", "60", {"tip": "numar", "numar": "60"}), ("Strada Crinului", "64", {"tip": "numar", "numar": "64"}),
                                            ("Strada Ion Luca Caragiale", "6", {"tip": "numar", "numar": "6"}), ("Strada Viilor", "12", None)]):
            tt = mm.apply_event(ev(f"D-{i}", "2026-09-10", "mentenanta", "avarie_semnalata", ref=r_adr(st, nr, ind)))
            out.append((tt["decizie"], [(x["element_id"], x["scor"], x["nivel"]) for x in tt["modificari"]], pas(tt, "cautare_strada")["rezultat"]))
        return json.dumps(out, sort_keys=True, ensure_ascii=False), mm.ancore
    verifica("determinism: două rulări identice dau aceleași decizii, scoruri, ferestre, candidați și ancore", ruleaza() == ruleaza())


def main() -> None:
    w = load_weights()
    m = mk()
    sim = lambda e: e.startswith("SIM-")      # noqa: E731
    gis = lambda e: not e.startswith("SIM-") and e in m.net["noduri"] or (e in m.net["tronsoane"] and not e.startswith("SIM-"))  # noqa: E731

    # --- (f) banda()
    verifica("banda: 0,85 verde, 0,65 galben, 0,45 portocaliu, 0,2 roșu, praguri incluse",
             [S.banda(x, w) for x in (0.85, 0.65, 0.45, 0.2, 0.8, 0.6, 0.4)] == ["verde", "galben", "portocaliu", "rosu", "verde", "galben", "portocaliu"])
    verifica("plafon(): gis/None = 1,0; adresa_numar 0,70; analiza_harta 0,40",
             S.plafon("gis", w) == 1.0 and S.plafon(None, w) == 1.0 and S.plafon("adresa_numar", w) == 0.70 and S.plafon("analiza_harta", w) == 0.40)
    verifica("scor_la_data: minim GIS nu e ridicat dacă scorul e deja sub el",
             S.scor_la_data(0.60, "2026-08-01", "2027-08-01", w, "gis") == 0.60
             and S.scor_la_data(0.95, "2026-08-01", "2030-08-01", w, "gis") == w["acuratete"]["minim_gis"]
             and S.scor_la_data(0.9, "2026-08-01", "2026-08-31", w) == 0.85)
    verifica("decizie: executat_teren coboară pragul la 0,50", S.decizie(0.55, w) == "predictie" and S.decizie(0.55, w, executat_teren=True) == "in_model"
             and S.decizie(0.55, w, planificat=True, executat_teren=True) == "predictie")

    # --- (a) element KMZ neatins
    kmz = next(e for e in m.net["tronsoane"] if not sim(e))
    a1, a2, a3 = (snap(m, d, kmz) for d in ("2026-08-01", "2026-11-15", "2027-08-01"))
    verifica("KMZ neatins: 0,95 la start, origine retea_start, t0, sursa gis",
             a1["scor"] == 0.95 and a1["origine"] == "retea_start" and a1["t0"] is True and a1["sursa_locatie"] == "gis" and a1["verificat_om"] is False,
             f"{a1['scor']}")
    verifica("KMZ neatins: la 2026-11-15 scor >= 0,91 (0,95 - 0,01*106/30 = 0,915) și verde; la 2027-08-01 nu sub 0,85",
             a2["scor"] >= 0.91 and a2["banda"] == "verde" and a3["scor"] >= 0.85, f"{a2['scor']} {a3['scor']}")
    verifica("mesajul de scădere spune rata GIS (0,01)", "0.01" in a2["motive"][0]["text"] and "GIS" in a2["motive"][0]["text"], a2["motive"][0]["text"])

    # --- (b) benzi la 2026-08-01 și 2026-11-15
    nodes_tr = list(m.net["noduri"]) + list(m.net["tronsoane"])
    n_gis = [e for e in nodes_tr if not sim(e)]
    for d in ("2026-08-01", "2026-11-15"):
        bg, bs = benzi(m, d, lambda e: e in n_gis), benzi(m, d, sim)
        print("    benzi", d, "GIS", bg, "SIM", bs)
    bg, bs = benzi(m, "2026-08-01", lambda e: e in n_gis), benzi(m, "2026-08-01", sim)
    verifica("2026-08-01: toate KMZ sunt verzi, niciun SIM-* nu e verde, SIM-* au toate cele trei benzi",
             bg["verde"] == len(n_gis) and bs["verde"] == 0 and bs["galben"] > 0 and bs["portocaliu"] > 0 and bs["rosu"] > 0, f"{bg} {bs}")
    verifica("SIM-*: origine generat_model, t0, motiv „din rapoarte mai vechi”",
             all(snap(m, "2026-08-01", e)["origine"] == "generat_model" and snap(m, "2026-08-01", e)["t0"]
                 and "rapoarte mai vechi" in snap(m, "2026-08-01", e)["motive"][-1]["text"] for e in list(m.net["noduri"])[-5:] if sim(e)))

    # --- (c) determinist
    m2 = mk()
    verifica("același model construit de două ori: aceleași scoruri SIM-*",
             {e: m.istoric[e][0]["scor"] for e in m.istoric if sim(e)} == {e: m2.istoric[e][0]["scor"] for e in m2.istoric if sim(e)}
             and any(sim(e) for e in m.istoric))

    # --- (d) raport executat, nod lipsă localizat doar din adresă (stradă + număr)
    c0 = m.net["_zona_centru"]
    lat, lon = c0[0] + 300 / 111_320, c0[1]
    ref = {"coordonate": {"lat": lat, "lon": lon}, "adresa": "Strada Viilor nr. 12"}
    det = {"geocodare": geo_strada_numar(lat, lon, w)}
    md = mk()
    t = md.apply_event(ev("S4-1", "2026-09-10", "mentenanta", "nod_lipsa", "executat", ref=ref, det=det, inc=0.95))
    nod = next(x for x in t["modificari"] if x["tip_element"] == "nod")
    pr = snap(md, "2026-09-10", nod["element_id"])
    verifica("executat de mentenanță, doar adresă cu număr: aplicat (in_model), scor <= 0,70, galben/portocaliu, sursa adresa_numar",
             nod["nivel"] == "in_model" and t["decizie"] == "adaugat" and nod["scor"] <= 0.70 and nod["banda"] in ("galben", "portocaliu")
             and nod["sursa_locatie"] == "adresa_numar" and pr["sursa_locatie"] == "adresa_numar" and pr["origine"] == "generat_model" and pr["t0"] is False,
             f"{t['decizie']} {nod['nivel']} {nod['scor']} {nod['banda']} {nod.get('sursa_locatie')}")
    print("    motiv:", nod["motive"][0]["text"][:300])
    sch = next(s for s in t["schimbari"] if s["element_id"] == nod["element_id"])
    verifica("jurnal: schimbari cu banda_inainte/banda_dupa", sch["banda_inainte"] is None and sch["banda_dupa"] == nod["banda"], str(sch))
    # aceeași situație ca cerere: planificat și racordare -> predicție
    tp = mk().apply_event(ev("S4-2", "2026-09-10", "mentenanta", "nod_lipsa", "planificat", ref=ref, det=det, inc=0.95))
    verifica("aceeași situație, status planificat -> predicție (neaplicat)", tp["decizie"] == "predictie", tp["decizie"])
    tr = mk().apply_event(ev("S4-3", "2026-09-10", "racordari", "cerere_racordare", "semnalat", ref=ref, det=det, inc=0.95))
    verifica("aceeași situație ca cerere de racordare -> predicție", tr["decizie"] == "predictie", tr["decizie"])
    casa = next((x for x in tr["modificari"] if x["element_id"].endswith("-casa")), None)
    verifica("racordare: casa localizată din adresă cu număr are sursa adresa_numar și scor <= 0,70; stâlpii analiza_harta <= 0,40",
             casa and casa["sursa_locatie"] == "adresa_numar" and casa["scor"] <= 0.70
             and all(x["sursa_locatie"] == "analiza_harta" and x["scor"] <= 0.40 for x in tr["modificari"] if x["tip_element"] == "nod" and not x["element_id"].endswith("-casa")),
             str([(x["element_id"], x["scor"], x["sursa_locatie"]) for x in tr["modificari"] if x["tip_element"] == "nod"]))
    verifica("racordare: există cel puțin un stâlp prezis", any(x["tip_element"] == "nod" and not x["element_id"].endswith("-casa") for x in tr["modificari"]))

    # --- (e) raport ulterior cu coordonate exacte ridică plafonul
    t2 = md.apply_event(ev("S4-4", "2026-09-20", "mentenanta", "verificare", "executat", ref={"coordonate": {"lat": lat, "lon": lon}}))
    p2 = snap(md, "2026-09-20", nod["element_id"])
    print("    după coordonate exacte:", t2["decizie"], p2 and (p2["scor"], p2["sursa_locatie"], p2["banda"]))
    verifica("confirmare cu coordonate exacte: sursa devine coordonate, scorul poate trece de 0,70 dar nu de 0,85",
             p2 and p2["sursa_locatie"] == "coordonate" and 0.70 < p2["scor"] <= 0.85, str(p2 and (p2["scor"], p2["sursa_locatie"])))
    # confirmare tot din adresă: rămâne sub plafon
    md2 = mk()
    md2.apply_event(ev("S4-5", "2026-09-10", "mentenanta", "nod_lipsa", "executat", ref=ref, det=det, inc=0.95))
    nid = next(e for e in md2.istoric if e.startswith("NOU-S4-5") and e in md2.net["noduri"])
    md2.apply_event(ev("S4-6", "2026-09-12", "mentenanta", "verificare", "executat", ref={"element_id": nid}))   # ID: sursă mai bună
    verifica("confirmare cu ID: sursa devine id (plafon 0,85)", snap(md2, "2026-09-12", nid)["sursa_locatie"] == "id", str(snap(md2, "2026-09-12", nid)["sursa_locatie"]))

    # --- GIS: confirmarea nu e plafonată; mesaj de ce la plafon
    mg = mk()
    mg.apply_event(ev("S4-7", "2026-09-01", "mentenanta", "verificare", "executat", ref={"element_id": kmz}))
    sg = snap(mg, "2026-09-01", kmz)
    verifica("GIS confirmat: rămâne verde, sursa gis, fără plafon", sg["banda"] == "verde" and sg["sursa_locatie"] == "gis" and sg["scor"] >= 0.95, str(sg["scor"]))

    # --- P1: raport executat de investiții/racordari vs semnalat
    pe = mk().apply_event(ev("S4-8", "2026-09-10", "investitii", "nod_lipsa", "executat", ref={"coordonate": {"lat": lat, "lon": lon}}, inc=0.7, sursa="formular"))
    ps = mk().apply_event(ev("S4-9", "2026-09-10", "investitii", "nod_lipsa", "semnalat", ref={"coordonate": {"lat": lat, "lon": lon}}, inc=0.7, sursa="formular"))
    verifica("P1: același scor, executat aplică (>= 0,50), semnalat rămâne predicție (< 0,75)",
             pe["decizie"] == "adaugat" and ps["decizie"] == "predictie", f"{pe['decizie']} / {ps['decizie']}")

    # --- (g) statistici
    st = m.statistici("2026-11-15")
    verifica("statistici(): procent_banda cu cele patru benzi, suma ~100",
             set(st["procent_banda"]) == {"verde", "galben", "portocaliu", "rosu"} and abs(sum(st["procent_banda"].values()) - 100) < 0.5, str(st["procent_banda"]))
    verifica("snapshot: t0, sursa_locatie, verificat_om, verificat_om_data, banda în properties",
             all(k in snap(m, "2026-08-01", kmz) for k in ("t0", "sursa_locatie", "verificat_om", "verificat_om_data", "banda")))

    # --- sim_din_rapoarte = 0: SIM-* tratate ca GIS
    w0 = load_weights()
    w0["retea_start"]["sim_din_rapoarte"] = 0
    m0 = GridModel(weights=w0)
    e0 = next(e for e in m0.istoric if sim(e))
    verifica("retea_start.sim_din_rapoarte = 0: SIM-* sunt GIS (retea_start, 0,95)",
             m0.istoric[e0][0]["origine"] == "retea_start" and m0.istoric[e0][0]["scor"] == 0.95)

    teste_cautare_strada()

    ok, tot = sum(OK), len(OK)
    print(f"\nsmoke_sesiune4: {ok}/{tot} OK")
    if ok != tot:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
