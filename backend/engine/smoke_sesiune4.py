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
    # --- tipuri NOI (decizia lui Victor, 15 nov.): mereu element nou la fereastra.punct, indiferent de câți stâlpi sunt în fereastră
    mn1 = mk()
    t = mn1.apply_event(ev("CS-N1", "2026-09-10", "mentenanta", "nod_lipsa", "executat", ref=r_adr("Strada Crinului", "60", {"tip": "numar", "numar": "60"}), inc=0.95))
    cs = pas(t, "cautare_strada")["rezultat"]
    nou = next((x for x in t["modificari"] if x["element_id"] == "NOU-CS-N1"), None)
    verifica("tip nou, 1 stâlp în fereastră: nod_lipsa executat -> element NOU (nu cel existent), existentul doar în candidați/motiv, `ales` null",
             len(cs["candidati"]) == 1 and cs["ales"] is None and nou and nou["element_id"] != nod1 and t["decizie"] == "adaugat"
             and pas(t, "potrivire")["rezultat"]["status"] == "absent_din_model" and nod1 in nou["motive"][0]["text"]
             and nod1 in [a["element_id"] for a in pas(t, "predictie")["rezultat"]["stalpi_existenti_in_fereastra"]]
             and abs(mn1.net["noduri"]["NOU-CS-N1"]["lat"] - cs["punct"]["lat"]) < 1e-5 and mn1.ancore == [], f"{t['decizie']} {cs['candidati']}")
    mn1b = mk()
    t = mn1b.apply_event(ev("CS-N1b", "2026-09-10", "mentenanta", "nod_lipsa", "planificat", ref=r_adr("Strada Crinului", "60", {"tip": "numar", "numar": "60"}), inc=0.95))
    nou = next(x for x in t["modificari"] if x["element_id"] == "NOU-CS-N1b")
    alt = (nou["predictie"] or {}).get("alternative") or []
    verifica("tip nou planificat (predicție) cu 1 stâlp în fereastră: alternativele elementului nou conțin stâlpul existent, cu motivul cerut",
             t["decizie"] == "predictie" and [a["element_id"] for a in alt] == [nod1] and "poate fi unul dintre aceștia (stâlp existent în fereastră)" in alt[0]["motiv"], str(alt))
    mn2 = mk()
    t = mn2.apply_event(ev("CS-N2", "2026-09-10", "mentenanta", "nod_lipsa", "executat", ref=r_adr("Strada Viilor", "12"), inc=0.95))
    cs = pas(t, "cautare_strada")["rezultat"]
    nou = next((x for x in t["modificari"] if x["element_id"] == "NOU-CS-N2"), None)
    verifica("tip nou, > 4 candidați (Strada Viilor nr. 12): element nou, NU de_verificat; toți candidații rămân informativ, `ales` null",
             len(cs["candidati"]) > mn2.w["cautare_strada"]["max_candidati_predictie"] and cs["ales"] is None and t["decizie"] == "adaugat" and nou
             and nou["sursa_locatie"] == "adresa_numar" and nou["scor"] <= 0.70
             and len(pas(t, "predictie")["rezultat"]["stalpi_existenti_in_fereastra"]) == len(cs["candidati"]), f"{t['decizie']} {len(cs['candidati'])}")
    print("    exemplu tip nou, >4 candidați:", t["decizie"], json.dumps({k: cs[k] for k in ("strada", "indiciu", "candidati", "ales", "motiv")}, ensure_ascii=False)[:700])
    mn2b = mk()
    t = mn2b.apply_event(ev("CS-N2b", "2026-09-10", "mentenanta", "nod_lipsa", "planificat", ref=r_adr("Strada Viilor", "12"), inc=0.95))
    nou = next(x for x in t["modificari"] if x["element_id"] == "NOU-CS-N2b")
    verifica("tip nou planificat, > 4 candidați: predicție pe elementul nou, toți candidații în `predictie.alternative`",
             t["decizie"] == "predictie" and len(nou["predictie"]["alternative"]) == len(pas(t, "cautare_strada")["rezultat"]["candidati"])
             and all("stâlp existent în fereastră" in a["motiv"] for a in nou["predictie"]["alternative"]))
    mr = mk()
    t = mr.apply_event(ev("CS-N3", "2026-09-10", "racordari", "racord_nou", "executat", ref=r_adr("Strada Viilor", "12"), inc=0.95))
    cs = pas(t, "cautare_strada")["rezultat"]
    verifica("racord_nou pe stradă cu stâlpi în fereastră: element nou, nu de_verificat și nu potrivit pe existent",
             cs["candidati"] and cs["ales"] is None and t["decizie"] in ("adaugat", "predictie") and any(x["element_id"].startswith("NOU-CS-N3") for x in t["modificari"])
             and pas(t, "potrivire")["rezultat"]["status"] == "absent_din_model", t["decizie"])
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


def teste_verificare_om() -> None:
    """V5 / D10: `verificare_om`, acceptarea ca verificare, contradicția ulterioară, scăderea în timp, API."""
    def vev(i, data, tinta=None, ref=None, motiv=None):
        det = {"tinta_id": tinta} if tinta else {}
        if motiv:
            det["motiv"] = motiv
        return ev(i, data, "om_teren", "verificare_om", "executat", ref=ref, det=det, sursa="om_teren", inc=1.0)

    m = mk()
    w = m.w
    sid = next(e for e in sorted(m.istoric) if e.startswith("SIM-") and m.istoric[e][0]["scor"] == w["retea_start"]["scor_galben"]
               and e in m.net["noduri"])
    verifica("V5 pregătire: stâlp SIM-* galben la start", snap(m, "2026-08-01", sid)["banda"] == "galben", sid)
    t = m.apply_event(vev("V5-1", "2026-11-15", sid, motiv="verificat pe teren"))
    s1 = snap(m, "2026-11-15", sid)
    verifica("V5: verificare_om pe galben -> scor 1,0, verde, verificat_om, data, confirmat_de om, in_model",
             s1["scor"] == 1.0 and s1["banda"] == "verde" and s1["verificat_om"] is True and s1["verificat_om_data"] == "2026-11-15"
             and s1["confirmat_de"] == "om" and s1["nivel"] == "in_model" and s1["ultima_verificare"] == "2026-11-15", str(s1["scor"]))
    verifica("V5: motiv 'Verificat de om în teren (data): motiv'", s1["motive"][0]["text"].startswith("Verificat de om în teren (2026-11-15): verificat pe teren"), s1["motive"][0]["text"])
    verifica("V5: decizie aplicat, schimbare actualizat galben -> verde, jurnal cu eticheta verificat_om",
             t["decizie"] == "aplicat" and t["schimbari"][0]["ce"] == "actualizat" and t["schimbari"][0]["banda_inainte"] == "galben"
             and t["schimbari"][0]["banda_dupa"] == "verde" and m.jurnal[-1]["eticheta"] == "verificat_om" and m.jurnal[-1]["tip"] == "verificare_om",
             f"{t['decizie']} {m.jurnal[-1]['eticheta']}")
    s2 = snap(m, "2027-11-15", sid)
    verifica("V5: la +365 zile scorul >= 0,95 (minim verificat_om), încă verificat", s2["scor"] >= w["verificat_om"]["minim"] and s2["verificat_om"] is True, str(s2["scor"]))
    print("StepTrace verificare_om:", json.dumps({"decizie": t["decizie"], "pasi": [p["nume"] for p in t["pasi"]],
                                                   "schimbari": t["schimbari"]}, ensure_ascii=False)[:600])
    # contradicție: apel de client ulterior
    tc = m.apply_event(ev("V5-2", "2026-12-01", "apel_client", "avarie_semnalata", "semnalat", ref={"element_id": sid}, sursa="apel_client", inc=0.9))
    s3 = snap(m, "2026-12-01", sid)
    verifica("V5: apel care contrazice -> verificat_om false, scor scade, motiv pomenește contrazicerea",
             s3["verificat_om"] is False and s3["verificat_om_data"] is None and s3["scor"] < 1.0 and "contrazisă de V5-2" in s3["motive"][0]["text"]
             and "2026-11-15" in s3["motive"][0]["text"], f"{s3['scor']} {s3['motive'][0]['text'][:90]}")
    verifica("V5: contradicția: scor = scor efectiv + efect (nu resetat)", abs(s3["scor"] - (S.scor_la_data(1.0, "2026-11-15", "2026-12-01", w, "verificat_om") + tc["modificari"][0]["motive"][0]["efect"])) < 0.002, str(s3["scor"]))
    # un raport care confirmă nu șterge flag-ul
    m2 = mk()
    m2.apply_event(vev("V5-3", "2026-11-15", sid))
    m2.apply_event(ev("V5-4", "2026-11-20", "mentenanta", "verificare", "executat", ref={"element_id": sid}))
    verifica("V5: raport care confirmă nu șterge verificat_om", snap(m2, "2026-11-20", sid)["verificat_om"] is True)
    # demontat (semnal) contrazice
    m3 = mk()
    m3.apply_event(vev("V5-5", "2026-11-15", sid))
    m3.apply_event(ev("V5-6", "2026-11-20", "mentenanta", "activ_demontat", "executat", ref={"element_id": sid}))
    verifica("V5: semnal de demontare contrazice verificarea", snap(m3, "2026-11-20", sid)["verificat_om"] is False)
    # element GIS și tronson
    kmz = next(e for e in m.net["tronsoane"] if not e.startswith("SIM-"))
    mg = mk()
    mg.apply_event(vev("V5-7", "2026-11-15", kmz))
    verifica("V5: tronson GIS verificat -> 1,0", snap(mg, "2026-11-15", kmz)["scor"] == 1.0 and snap(mg, "2026-11-15", kmz)["verificat_om"] is True)
    # fără tinta_id: ID în referință
    mi = mk()
    ti = mi.apply_event(vev("V5-8", "2026-11-15", None, ref={"element_id": sid}))
    verifica("V5: fără tinta_id, cu referinta.element_id -> verificat", snap(mi, "2026-11-15", sid)["verificat_om"] is True and ti["decizie"] == "aplicat", ti["decizie"])
    tn = mi.apply_event(vev("V5-9", "2026-11-16", None, ref={}))
    verifica("V5: fără tinta_id și fără element -> neaplicat cu motiv", tn["decizie"] == "neaplicat" and tn["pasi"][-1]["motive"][0], str(tn["pasi"][-1].get("motive")))
    tx = mi.apply_event(vev("V5-10", "2026-11-16", "NU-EXISTA-1"))
    verifica("V5: tinta_id inexistent -> neaplicat", tx["decizie"] == "neaplicat" and tx["eroare"]["cod"] == "tinta_necunoscuta", tx["decizie"])
    # predicție NOU-...
    mp = mk()
    nod = m.net["noduri"][sid]
    tp = mp.apply_event(ev("V5-11", "2026-11-15", "mentenanta", "nod_lipsa", "semnalat", ref={"coordonate": {"lat": nod["lat"] + 0.0003, "lon": nod["lon"]}},
                           sursa="text_liber", inc=0.7, forma="text_liber"))
    pred = next((x["element_id"] for x in tp["modificari"] if x["tip_element"] == "nod"), None)
    verifica("V5 pregătire: predicție de nod", tp["decizie"] == "predictie" and pred in mp.predictii, str(tp["decizie"]))
    tv = mp.apply_event(vev("V5-12", "2026-11-16", pred))
    sp = snap(mp, "2026-11-16", pred)
    verifica("V5: verificare pe predicție NOU-* -> aplicată, verificată, 1,0", tv["decizie"] == "aplicat" and pred in mp.net["noduri"] and pred not in mp.predictii
             and sp["verificat_om"] is True and sp["scor"] == 1.0 and sp["nivel"] == "in_model" and sp["confirmat_de"] == "om", str(sp and sp["scor"]))
    # „Acceptă” (decizia omului) = verificare de om
    ma = mk()
    tp = ma.apply_event(ev("V5-13", "2026-11-15", "mentenanta", "nod_lipsa", "semnalat", ref={"coordonate": {"lat": nod["lat"] + 0.0003, "lon": nod["lon"]}},
                           sursa="text_liber", inc=0.7, forma="text_liber"))
    pred = next(x["element_id"] for x in tp["modificari"] if x["tip_element"] == "nod")
    ta = ma.apply_event(ev("V5-14", "2026-11-16", "om_teren", "verificare", "executat", det={"decizie": {"tinta_id": pred, "decizie": "accepta"}}, sursa="om_teren", inc=1.0))
    sa = snap(ma, "2026-11-16", pred)
    verifica("V5: «Acceptă» prin _decizie_om -> verificat_om true, scor 1,0", ta["decizie"] == "aplicat" and sa["verificat_om"] is True and sa["scor"] == 1.0 and sa["verificat_om_data"] == "2026-11-16", str(sa["scor"]))
    # pin VER-* devine nod verificat
    mv = mk()
    pid = "VER-TEST"
    mv.pinuri[pid] = {"geometrie": {"type": "Point", "coordinates": [nod["lon"], nod["lat"] + 0.0002]}}
    mv._pune(pid, "nod", "2026-11-15", nivel="de_verificat", scor=0.3, ultima_verificare=None, origine="generat_model", t0=False, sursa_locatie="strada",
             verificat_om=False, verificat_om_data=None, predictie=None, motive=[{"text": "pin", "efect": 0.0, "eveniment": "x", "data": "2026-11-15"}])
    mv.apply_event(vev("V5-15", "2026-11-16", pid))
    sv = snap(mv, "2026-11-16", pid)
    verifica("V5: pin VER-* devine nod verificat în model", pid in mv.net["noduri"] and pid not in mv.pinuri and sv and sv["verificat_om"] is True and sv["scor"] == 1.0
             and sv["geometrie"]["coordinates"][1] == nod["lat"] + 0.0002 if sv and "geometrie" in sv else bool(sv and sv["verificat_om"]), str(sv and sv["nivel"]))
    # determinism
    def rul():
        mm = mk()
        mm.apply_event(vev("V5-1", "2026-11-15", sid))
        mm.apply_event(ev("V5-2", "2026-12-01", "apel_client", "avarie_semnalata", "semnalat", ref={"element_id": sid}, sursa="apel_client", inc=0.9))
        return json.dumps([mm.jurnal, snap(mm, "2027-01-01", sid)], sort_keys=True, default=str)
    verifica("V5: determinism (două rulări identice)", rul() == rul())
    # element cu predicția „probabil acest element” (cautare_strada): marker șters
    mm = mk()
    mm._pune(sid, "nod", "2026-11-15", predictie={"metoda": "cautare_strada", "urmeaza_strada": None, "propunere": None, "scor_propunere": 0.5})
    mm.apply_event(vev("V5-16", "2026-11-16", sid))
    verifica("V5: marker cautare_strada șters la verificare", snap(mm, "2026-11-16", sid)["predictie"] is None)
    # API: POST /element/{id}/verificare
    try:
        from fastapi.testclient import TestClient
        from backend.api.main import app
        r = TestClient(app).post(f"/element/{sid}/verificare", json={"motiv": "test"})
        verifica("V5 API: POST /element/{id}/verificare -> 200 (nu 501)", r.status_code == 200, f"{r.status_code} {r.text[:120]}")
        TestClient(app).post("/demo/reset")
    except ImportError:
        print("SKIP API (fastapi lipsă)")


def teste_analiza_harta() -> None:
    """V3: analiza hărții (`backend.engine.analiza_harta`) pe graful de străzi OSM; integrarea în racordare și în nodul lipsă."""
    import math

    from backend.engine.analiza_harta import traseu_pe_strazi
    from backend.engine.network import dist_m
    from backend.engine.zona import zona_ok

    w, m0 = load_weights(), GridModel()
    net, a = m0.net, load_weights()["analiza_harta"]
    S_osm = osm.strazi()
    segs = [(tuple(u), tuple(v)) for s_ in S_osm for u, v in zip(s_["puncte"], s_["puncte"][1:])]
    d_strada = lambda p: min(osm._proiecteaza(tuple(p), u, v)[1] for u, v in segs)
    # casă la ~300 m de rețea, la ~10 m de Strada Liviu Rebreanu (capătul de vest) și una la ~100 m
    c300, c100 = (44.28482, 26.05638), (44.27731, 26.05886)
    d300 = min(dist_m(c300, (n["lat"], n["lon"])) for n in net["noduri"].values())
    d100 = min(dist_m(c100, (n["lat"], n["lon"])) for n in net["noduri"].values())
    verifica("analiza: casele de test sunt la ~300 m și ~100 m de rețea", 250 <= d300 <= 350 and 90 <= d100 <= 140, f"{d300:.0f} / {d100:.0f}")
    r3, r1 = traseu_pe_strazi(c300, net, w), traseu_pe_strazi(c100, net, w)
    al = r3["ales"]
    verifica("analiza: casă la ~300 m: drum pe străzi (nu fara_drum), cu nume de străzi și stâlpi noi",
             not r3["fara_drum"] and al["strazi"] and al["stalpi_noi"] and al["lungime_m"] >= d300, f"{al['de_la']} {al['lungime_m']} m {al['strazi']}")
    verifica("analiza: fiecare punct al traseului (fără capetele de branșament) la ≤ 15 m de o stradă OSM",
             len(al["traseu"]) > 3 and all(d_strada(p) <= 15 for p in al["traseu"][1:-1]), f"{max(d_strada(p) for p in al['traseu'][1:-1]):.1f} m")
    verifica("analiza: stâlpii noi sunt pe stradă și la ≥ distanța minimă de nodurile existente",
             all(d_strada(p) <= 15 for p in al["stalpi_noi"]) and all(
                 dist_m(tuple(p), (n["lat"], n["lon"])) >= w["potrivire"]["distanta_max_element_nou_m"] for p in al["stalpi_noi"] for n in net["noduri"].values()))
    verifica("analiza: stâlpii noi la cel mult pas_stalp_m unul de altul",
             all(dist_m(tuple(x["puncte"][0]), tuple(x["puncte"][-1])) <= a["pas_stalp_m"] + 1 for x in al["cabluri"][:-1]))
    verifica("analiza: scorul scade cu lungimea (300 m < 100 m)", r3["acuratete"] < r1["acuratete"], f"{r3['acuratete']} < {r1['acuratete']}")
    verifica("analiza: acuratețea = plafon[sursa] × factor; stâlpii plafonați la analiza_harta",
             abs(r3["acuratete"] - w["plafon_locatie"]["analiza_harta"] * r3["factor"]) < 0.002 and r3["acuratete_stalpi"] <= w["plafon_locatie"]["analiza_harta"]
             and traseu_pe_strazi(c300, net, w, sursa="coordonate")["acuratete"] > r3["acuratete"])
    verifica("analiza: alternativele au traseu și motiv", r3["alternative"] and all(x["traseu"] and x["motiv"] and x["de_la"] for x in r3["alternative"]),
             str([x["motiv"] for x in r3["alternative"]][:3]))
    verifica("analiza: explicația are 3 fraze", len(r3["explicatie"]) == 3 and all(isinstance(x, str) and x for x in r3["explicatie"]), str(r3["explicatie"]))
    verifica("analiza: determinist (două rulări identice)", json.dumps(traseu_pe_strazi(c300, net, w), sort_keys=True) == json.dumps(r3, sort_keys=True))
    verifica("analiza: ținta peste max_bransament_m scade acuratețea",
             traseu_pe_strazi((c300[0] + 100 / 111_320, c300[1]), net, w)["factor"] < r3["factor"] and traseu_pe_strazi((c300[0] + 100 / 111_320, c300[1]), net, w)["bransament_m"] > a["max_bransament_m"])
    # safeguard: cu zona restrânsă, niciun stâlp nou în afara ei
    wz = load_weights()
    wz["zona"]["raza_max_m"] = dist_m(net["_zona_centru"], (net["noduri"][al["de_la"]]["lat"], net["noduri"][al["de_la"]]["lon"])) + 60
    rz = traseu_pe_strazi(c300, net, wz)
    verifica("analiza: stâlpii noi în afara zonei sunt tăiați (tăiat, toți în zonă)",
             rz["ales"]["taiat"] and all(zona_ok(p[0], p[1], net, wz)["ok"] for p in rz["ales"]["stalpi_noi"]) and len(rz["ales"]["stalpi_noi"]) < len(al["stalpi_noi"]),
             f"{len(rz['ales']['stalpi_noi'])} < {len(al['stalpi_noi'])}")
    verifica("analiza: pe rularea normală niciun stâlp nou în afara zonei de 3 km", all(zona_ok(p[0], p[1], net, w)["ok"] for p in al["stalpi_noi"]))

    # --- rețea sintetică (metri față de un punct de lângă rețea): reutilizare, fără drum, evită, preferate
    la0, lo0 = 44.2800, 26.0600
    P = lambda x, y: (round(la0 + y / 111_320, 7), round(lo0 + x / (111_320 * math.cos(math.radians(la0))), 7))
    st = lambda nume, *pts: {"nume": nume, "puncte": [list(P(*p)) for p in pts]}
    nod = lambda i, x, y: (i, {"id": i, "lat": P(x, y)[0], "lon": P(x, y)[1]})
    net_s = {"noduri": dict([nod("A", 0, 0), nod("Q", 100, 3)]), "tronsoane": {}}
    r_n = traseu_pe_strazi(P(250, 0), net_s, w, strazi=[st("Test", (0, 0), (300, 0))])
    verifica("analiza: pornește din stâlpul existent cel mai bun (Q, la 150 m de țintă, nu A la 250 m)", r_n["ales"]["de_la"] == "Q" and r_n["ales"]["lungime_m"] < 160,
             f"{r_n['ales']['de_la']} {r_n['ales']['lungime_m']}")
    r = traseu_pe_strazi(P(250, 0), net_s, w, strazi=[st("Test", (0, 0), (300, 0))], de_la="A")
    verifica("analiza: stâlp existent pe drum (la 3 m) refolosit, fără stâlp nou lângă el",
             r["ales"]["de_la"] == "A" and r["ales"]["stalpi_reutilizati"] == ["Q"] and all(dist_m(tuple(p), P(100, 3)) > 10 for p in r["ales"]["stalpi_noi"])
             and any(c["la"] == "Q" for c in r["ales"]["cabluri"]), str(r["ales"]["stalpi_reutilizati"]))
    verifica("analiza: `exclus` scoate stâlpul din plecare/reutilizare",
             traseu_pe_strazi(P(250, 0), net_s, w, strazi=[st("Test", (0, 0), (300, 0))], exclus={"A", "Q"})["ales"] is None)
    # fără drum: două străzi nelegate
    net_f = {"noduri": dict([nod("A", 0, 0)]), "tronsoane": {}}
    rf = traseu_pe_strazi(P(250, 100), net_f, w, strazi=[st("Vest", (-20, 0), (60, 0)), st("Est", (200, 100), (300, 100))])
    verifica("analiza: punct fără legătură pe străzi -> fara_drum, scor analiza_harta.fara_drum, linie dreaptă",
             rf["fara_drum"] and rf["acuratete"] == a["fara_drum"] and rf["ales"]["strazi"] == [] and len(rf["ales"]["traseu"]) == 2
             and "Nu există drum pe străzi; linie dreaptă, de verificat." in rf["explicatie"], str(rf["explicatie"]))
    verifica("analiza: fara_drum fără stâlp în raza de căutare -> ales None",
             traseu_pe_strazi(P(5000, 0), net_f, w, strazi=[st("Vest", (-20, 0), (60, 0))])["ales"] is None)
    # evită: drum direct (y=0) vs ocol (y=80); cercul pe drumul direct îl blochează
    s2 = [st("Direct", (0, 0), (200, 0)), st("Ocol", (0, 0), (0, 80), (200, 80), (200, 0))]
    net_e = {"noduri": dict([nod("A", 0, 0)]), "tronsoane": {}}
    r_d = traseu_pe_strazi(P(200, 0), net_e, w, strazi=s2)
    r_e = traseu_pe_strazi(P(200, 0), net_e, w, strazi=s2, evita={"centru": P(100, 0), "raza_m": 20})
    cen = P(100, 0)
    verifica("analiza: fără evită drumul direct, cu evită ocolește cercul (≥ 20 m de centru)",
             r_d["ales"]["lungime_m"] < 210 and r_e["ales"]["lungime_m"] > 350 and all(
                 osm._proiecteaza(cen, tuple(u), tuple(v))[1] >= 20 for u, v in zip(r_e["ales"]["traseu"], r_e["ales"]["traseu"][1:])),
             f"{r_d['ales']['lungime_m']} / {r_e['ales']['lungime_m']}")
    verifica("analiza: cercul pe unicul drum -> fara_drum",
             traseu_pe_strazi(P(200, 0), net_e, w, strazi=[s2[0]], evita={"centru": P(100, 0), "raza_m": 20})["fara_drum"])
    # preferate: două drumuri apropiate (200 m și 240 m); strada preferată costă 0,5×
    s3 = [st("Scurta", (0, 0), (200, 0)), st("Noua", (0, 0), (0, 20), (200, 20), (200, 0))]
    r_n, r_p = traseu_pe_strazi(P(200, 0), net_e, w, strazi=s3), traseu_pe_strazi(P(200, 0), net_e, w, strazi=s3, preferate=["Noua"])
    verifica("analiza: `preferate` schimbă alegerea (Scurta -> Noua), lungimea raportată rămâne reală",
             r_n["ales"]["strazi"] == ["Scurta"] and r_p["ales"]["strazi"] == ["Noua"] and r_p["ales"]["lungime_m"] > r_n["ales"]["lungime_m"],
             f"{r_n['ales']['strazi']} -> {r_p['ales']['strazi']}")

    # --- racordare: casă la ~480 m (treapta 3, analiza hărții), pas nou `analiza_harta`, elemente `traseu_pe_strazi`
    far = {"lat": 44.28466, "lon": 26.05401}
    t = mk().apply_event(ev("AH-1", "2026-11-10", "racordari", "cerere_racordare", "semnalat", ref={"coordonate": far}, sursa="formular", forma="text_liber", inc=0.95))
    pa, pp = pas(t, "analiza_harta"), pas(t, "predictie")
    ras = (pa or {}).get("rezultat") or {}
    verifica("racordare: treapta 3 are pasul analiza_harta (înainte de predictie) cu drum pe străzi",
             pa and ras["ales"] and not ras["fara_drum"] and ras["ales"]["strazi"] and pp["rezultat"]["treapta"] == 3
             and t["pasi"].index(pa) < t["pasi"].index(pp) and pp["rezultat"]["metoda"] == "traseu_pe_strazi", str(pp["rezultat"].get("treapta")))
    mod = {x["element_id"]: x for x in t["modificari"]}
    stalpi = [x for k, x in mod.items() if "-S" in k]
    verifica("racordare: stâlpii prezisi au sursa analiza_harta, metoda traseu_pe_strazi, traseu și alternative",
             stalpi and all(x["sursa_locatie"] == "analiza_harta" and x["scor"] <= w["plafon_locatie"]["analiza_harta"] and
                            x["predictie"]["metoda"] == "traseu_pe_strazi" and x["predictie"]["traseu"] and x["predictie"]["alternative"] is not None and
                            x["predictie"]["treapta"] == 3 for x in stalpi))
    verifica("racordare: scorul scade față de o casă din treapta 2 la aceeași sursă",
             t["pasi"][-1]["rezultat"]["scor_propunere"] < mk().apply_event(ev("AH-1b", "2026-11-10", "racordari", "cerere_racordare", "semnalat",
                 ref={"coordonate": {"lat": c300[0], "lon": c300[1]}}, sursa="formular", forma="text_liber", inc=0.95))["pasi"][-1]["rezultat"]["scor_propunere"])
    # fără stâlp în raza de căutare (3 km de centru, în zonă): treapta 4, doar casa, pasul analiza_harta cu ales None
    c0 = net["_zona_centru"]
    t4 = mk().apply_event(ev("AH-4", "2026-11-10", "racordari", "cerere_racordare", "semnalat",
                             ref={"coordonate": {"lat": c0[0] - 2500 / 111_320, "lon": c0[1]}}, sursa="formular", forma="text_liber", inc=0.95))
    p4 = pas(t4, "analiza_harta")
    verifica("racordare: fără stâlp în raza de căutare -> treapta 4, doar casa", p4 and p4["rezultat"]["ales"] is None and pas(t4, "predictie")["rezultat"]["treapta"] == 4
             and [x["element_id"] for x in t4["modificari"]] == ["NOU-AH-4-casa"], str([x["element_id"] for x in t4["modificari"]]))
    verifica("racordare: pasul analiza_harta e doar la treapta 3 (treapta 1 nu-l are)",
             pas(mk().apply_event(ev("AH-5", "2026-11-10", "racordari", "cerere_racordare", "semnalat", ref={"coordonate": {"lat": c0[0] + 20 / 111_320, "lon": c0[1]}},
                                     sursa="formular", forma="text_liber", inc=0.95)), "analiza_harta") is None)

    # --- nod lipsă departe de rețea (> 80 m de orice tronson), legătură lungă care ar fi linie dreaptă: pe străzi
    pt = {"lat": far["lat"] + 60 / 111_320, "lon": far["lon"]}
    nodes = sorted(m0.net["noduri"].values(), key=lambda n: dist_m((pt["lat"], pt["lon"]), (n["lat"], n["lon"])))
    tn = mk().apply_event(ev("AH-2", "2026-11-10", "mentenanta", "nod_lipsa", "executat", ref={"coordonate": pt}, det={"noduri_vecine": [n["id"] for n in nodes[:2]]}))
    pn = pas(tn, "analiza_harta")
    mn = {x["element_id"]: x for x in tn["modificari"]}
    verifica("nod lipsă departe: legătura lungă are pasul analiza_harta și stâlpi intermediari plafonați (sursa analiza_harta)",
             pn and pn["rezultat"]["vecin"] and any("-S" in k for k in mn) and all(
                 x["sursa_locatie"] == "analiza_harta" and x["scor"] <= w["plafon_locatie"]["analiza_harta"] for k, x in mn.items() if "-S" in k), str(list(mn)[:4]))
    tn2 = mk().apply_event(ev("AH-3", "2026-11-10", "mentenanta", "nod_lipsa", "executat",
                              ref={"coordonate": {"lat": c0[0] + 15 / 111_320, "lon": c0[1]}}, det={"noduri_vecine": [n["id"] for n in sorted(
                                  m0.net["noduri"].values(), key=lambda n: dist_m(c0, (n["lat"], n["lon"])))[:2]]}))
    verifica("nod lipsă lângă rețea: fără pas analiza_harta (legături scurte ca înainte)", pas(tn2, "analiza_harta") is None)


def teste_mutare_fire_document() -> None:
    """V4: fire mutate descrise doar în text (fără clic): centrul din intersecție/stradă, zona marcată, traseul nou pe străzi care ocolește zona,
    aplicat (P1) sau predicție, traseul vechi „demontat probabil” (scos_din_uz, nu șters)."""
    import copy

    from backend.engine.sesiune2 import _dist_la_linie
    from backend.engine.zona import zona_ok

    TEXT = ("Ca urmare a construirii sensului giratoriu de la intersecția Șoseaua Principală cu Strada Liviu Rebreanu, rețeaua aeriană JT "
            "a fost mutată pe Strada Crinului. Lucrare finalizată 10.10.2026.")
    IX = {"strada_1": "Șoseaua Principală", "strada_2": "Strada Liviu Rebreanu"}

    def mf(i, status="executat", echipa="mentenanta", det=None, text=TEXT, ref=None, model=None):
        e = ev(i, "2026-10-10", echipa, "mutare_fire", status, ref=ref or {}, det={"motiv_mutare": "sens_giratoriu", **(det or {})}, sursa="formular", inc=0.5)
        e["text_original"] = text
        mm = model or mk()
        return mm, mm.apply_event(e)

    def legaturi(m, t):
        return [x for x in t["modificari"] if x["element_id"].startswith("MUT-")]

    def geom(m, eid):
        return m.net["tronsoane"][eid]["puncte"] if eid in m.net["tronsoane"] else m.predictii[eid]["puncte"]

    w = load_weights()
    cd = w["mutare_fire_document"]
    # --- exemplul de intro: intersecția + strada nouă, executat de mentenanță
    m, t = mf("MF-1", det={"intersectie": IX, "strada_noua": "Strada Crinului"})
    pm, mut = pas(t, "potrivire")["rezultat"], None
    centru, raza = (pm["centru"]["lat"], pm["centru"]["lon"]), pm["raza_m"]
    verifica("mutare fire (text): centrul = intersecția geocodată, raza = raza_intersectie_m, sursa intersectie",
             pm["status"] == "zona" and pm["sursa_centru"] == "intersectie" and raza == cd["raza_intersectie_m"] and abs(centru[0] - 44.282179) < 1e-4
             and abs(centru[1] - 26.065232) < 1e-4 and pm["strada_noua"] == "Strada Crinului", f"{centru} {raza} {pm['sursa_centru']}")
    marc = [x for x in t["modificari"] if not x["element_id"].startswith("MUT-")]
    verifica("mutare fire (text): zonă cu ≥ 1 element marcat, scor ≤ scor_marcat, motiv „Fire mutate”/„Demontat probabil”, nimic șters",
             len(marc) >= 1 and all(x["scor"] <= w["mutare_fire"]["scor_marcat"] and x["nivel"] in ("de_verificat", "scos_din_uz") for x in marc)
             and all(x["element_id"] in m.net["noduri"] or x["element_id"] in m.net["tronsoane"] for x in marc), str(len(marc)))
    mut = legaturi(m, t)
    verifica("mutare fire (text): ≥ 1 tronson nou MUT-<event>-<n>", len(mut) >= 1 and all(x["tip_element"] == "tronson" for x in mut), str([x["element_id"] for x in mut]))
    verifica("mutare fire (text): traseul nou nu intră în cercul zonei (niciun segment la ≤ rază de centru)",
             all(_dist_la_linie(centru, geom(m, x["element_id"])) > raza for x in mut), str([round(_dist_la_linie(centru, geom(m, x["element_id"]))) for x in mut]))
    ap = [x for x in mut if x["nivel"] == "in_model"]
    verifica("mutare fire (text): executat de mentenanță -> traseul scurt e aplicat (P1, ≥ 0,50, linie plină), plafon intersectie × factor de lungime",
             t["decizie"] == "aplicat" and ap and all(x["element_id"] in m.net["tronsoane"] and x["predictie"] is None
                                                      and x["scor"] >= w["acuratete"]["aplicat_raport_executat"] and x["scor"] <= w["plafon_locatie"]["intersectie"]
                                                      and x["sursa_locatie"] == "intersectie" for x in ap), str([(x["element_id"], x["scor"]) for x in mut]))
    old = [x for x in marc if x["nivel"] == "scos_din_uz"]
    verifica("mutare fire (text): traseul vechi (tronsoane aeriene marcate) trece pe scos_din_uz („demontat probabil”), nu e șters, motiv explicit",
             old and all(x["tip_element"] == "tronson" and x["element_id"] in m.net["tronsoane"] and "Demontat probabil" in x["motive"][0]["text"] for x in old)
             and any(s_["ce"] == "scos_din_uz" for s_ in t["schimbari"]), str(len(old)))
    ah = [p for p in t["pasi"] if p["nume"] == "analiza_harta"]
    verifica("mutare fire (text): pas analiza_harta pe legătură (ales.traseu, alternative, acuratete, explicatie, evita, legatura)",
             len(ah) == len(mut) and all(p["rezultat"]["ales"]["traseu"] and "alternative" in p["rezultat"] and p["rezultat"]["explicatie"] and p["rezultat"]["evita"]["raza_m"] == raza
                                         and p["rezultat"]["legatura"].startswith("MUT-MF-1-") for p in ah), str(len(ah)))
    strazi_ales = {s_ for p in ah for s_ in p["rezultat"]["ales"]["strazi"]}
    verifica("mutare fire (text): traseul nou folosește Strada Crinului (există drum pe ea, preferată din document)",
             "Strada Crinului" in strazi_ales and all(p["rezultat"]["strada_preferata"] == "Strada Crinului" for p in ah), str(sorted(strazi_ales)))
    ls = [x for x in mut if x["nivel"] == "predictie"]
    verifica("mutare fire (text): legăturile lungi (scor sub 0,50) rămân predicții punctate, cu traseu, alternative și slaba sub 0,40",
             ls and all(x["predictie"]["metoda"] == "traseu_pe_strazi" and x["predictie"]["traseu"] and "alternative" in x["predictie"]
                        and x["predictie"]["slaba"] == (x["scor"] < w["praguri"]["predictie"]) and x["element_id"] not in m.net["tronsoane"] for x in ls),
             str([(x["element_id"], x["scor"]) for x in ls]))
    verifica("mutare fire (text): nimic nou în afara zonei de 3 km", all(zona_ok(p[0], p[1], m.net, w)["ok"] for x in mut for p in geom(m, x["element_id"])))
    m2, t2 = mf("MF-1", det={"intersectie": IX, "strada_noua": "Strada Crinului"})
    sig = lambda mm, tt: [(x["element_id"], x["nivel"], x["scor"], len(geom(mm, x["element_id"])) if x["element_id"].startswith("MUT-") else 0) for x in tt["modificari"]]
    verifica("mutare fire (text): determinist (două rulări dau același rezultat)", sig(m, t) == sig(m2, t2))

    # --- fără strada_noua: tot iese un traseu
    mn, tn = mf("MF-2", det={"intersectie": IX}, text=TEXT.replace("mutată pe Strada Crinului", "mutată"))
    verifica("mutare fire: fără strada_noua tot iese un traseu nou (fără stradă preferată)",
             legaturi(mn, tn) and pas(tn, "potrivire")["rezultat"]["strada_noua"] is None
             and all(p["rezultat"]["strada_preferata"] is None for p in tn["pasi"] if p["nume"] == "analiza_harta"))

    # --- planificat: predicție, nu aplicat; zona rămâne „de verificat"
    mp, tp = mf("MF-3", "planificat", det={"intersectie": IX, "strada_noua": "Strada Crinului"})
    lp = legaturi(mp, tp)
    verifica("mutare fire: status planificat -> traseu nou doar predicție (punctat), nimic aplicat, zona de_verificat",
             lp and all(x["nivel"] == "predictie" and x["element_id"] not in mp.net["tronsoane"] for x in lp) and tp["decizie"] == "de_verificat"
             and all(x["nivel"] == "de_verificat" for x in tp["modificari"] if not x["element_id"].startswith("MUT-")), tp["decizie"])
    ms, ts = mf("MF-4", "semnalat", det={"intersectie": IX})
    verifica("mutare fire: raport semnalat (nu executat) nu aplică traseul nou",
             all(x["nivel"] == "predictie" for x in legaturi(ms, ts)) and ts["decizie"] == "de_verificat")
    mi, ti = mf("MF-5", echipa="investitii", det={"intersectie": IX})
    verifica("mutare fire: executat de investiții aplică la fel ca mentenanța (P1)", ti["decizie"] == "aplicat" and any(x["nivel"] == "in_model" for x in legaturi(mi, ti)))

    # --- intersecție negăsită -> strada
    mg, tg = mf("MF-6", det={"intersectie": {"strada_1": "Strada Speranței", "strada_2": "Strada Inexistentă"}})
    pg = pas(tg, "potrivire")["rezultat"]
    verifica("mutare fire: intersecție negăsită -> centrul din strada numită (sursa strada, rază dublă), tot marchează o zonă",
             pg["sursa_centru"] == "strada" and pg["raza_m"] == 2 * cd["raza_intersectie_m"] and tg["decizie"] != "neaplicat" and "intersecția nu a fost găsită" in pg["text_centru"],
             f"{pg['sursa_centru']} {pg['raza_m']} {tg['decizie']}")
    # --- nicio stradă -> neaplicat (P3)
    mz, tz = mf("MF-7", text="S-au mutat firele aeriene din cauza lucrărilor la drum.")
    verifica("mutare fire: text fără stradă/intersecție/coordonate -> neaplicat, cu motiv", tz["decizie"] == "neaplicat" and not tz["modificari"]
             and "fără locație" in tz["pasi"][-1]["motive"][0])
    # --- doar din text (fără detalii.intersectie): regex
    mt, tt = mf("MF-8")
    pt = pas(tt, "potrivire")["rezultat"]
    verifica("mutare fire: doar text_original (fără detalii.intersectie): regex găsește intersecția și strada nouă",
             pt["sursa_centru"] == "intersectie" and pt["intersectie"]["sursa"] == "regex" and pt["intersectie"]["strada_1"] == "Șoseaua Principală"
             and pt["strada_noua"] == "Strada Crinului" and pt["strada_noua_sursa"] == "regex" and legaturi(mt, tt), f"{pt['intersectie']} {pt['strada_noua']}")
    # --- nod din ID (EV4-026-like): zonă din nodul numit, nu neaplicat
    nid = "5481763"
    mi2, ti2 = mf("MF-9", ref={"element_id": nid}, text="Firul de la nodul 5481763 mutat la sensul giratoriu.")
    verifica("mutare fire: doar nodul din ID (fără stradă) -> zonă din nod, sursa id", pas(ti2, "potrivire")["rezultat"]["sursa_centru"] == "id" and ti2["decizie"] != "neaplicat")
    # --- fără drum de ocolire: legătură fara_drum (linie dreaptă, predicție slabă)
    w2 = copy.deepcopy(w)
    w2["mutare_fire_document"]["max_ocolire_m"] = 1
    m3 = GridModel(weights=w2)
    m3.traseu_fn = osm.traseu_fn()
    _, t3 = mf("MF-10", det={"intersectie": IX, "strada_noua": "Strada Crinului"}, model=m3)
    l3 = legaturi(m3, t3)
    verifica("mutare fire: niciun drum care ocolește zona -> o legătură fara_drum (linie dreaptă, predicție slabă, de verificat), neaplicată",
             len(l3) == 1 and l3[0]["predictie"]["fara_drum"] and l3[0]["predictie"]["metoda"] == "linie_dreapta" and l3[0]["nivel"] == "predictie"
             and l3[0]["predictie"]["slaba"] and t3["decizie"] == "de_verificat", str([(x["element_id"], x["scor"]) for x in l3]))
    # --- evenimentul real din fixture (EV4-026) nu mai iese neaplicat
    try:
        evs = json.load(open("data/events/events.json", encoding="utf-8"))
        evs = evs if isinstance(evs, list) else evs.get("events", [])
        e26 = next(e for e in evs if e["event_id"] == "EV4-026")
        t26 = mk().apply_event(e26)
        verifica("mutare fire: EV4-026 (doar „Șoseaua Principală” + nodul 5481763) nu mai iese neaplicat", t26["decizie"] != "neaplicat" and t26["modificari"], t26["decizie"])
    except (OSError, StopIteration):
        verifica("mutare fire: EV4-026 indisponibil (fixture lipsă)", True)


def teste_linie_planificata() -> None:
    """Linie planificată: 2 noduri / 2 GPS / stradă + indiciu -> predicție punctată pe străzi (`PLAN-*`), niciodată aplicată;
    fără loc -> neaplicat; determinist; în zona de 3 km (backend/engine/linie_planificata.py)."""
    from backend.engine.network import dist_m
    from backend.engine.zona import zona_ok

    def plan(m, i, ref=None, det=None, inc=0.8, sursa="formular", text="test"):
        e = ev(i, "2026-09-20", "investitii", "linie_planificata", "planificat", ref=ref, det=det, sursa=sursa, inc=inc)
        e["text_original"] = text
        return m.apply_event(e)

    def predictie_ok(t, sid, metoda="traseu_pe_strazi"):
        st = (t["modificari"] or [{}])[0]
        pr = st.get("predictie") or {}
        return (t["decizie"] == "predictie" and st.get("element_id") == sid and st["nivel"] == "predictie"
                and pr.get("metoda") == metoda and (pr.get("propunere") or {}).get("proprietate") == "linie_planificata")

    m = mk()
    nodes = sorted(n for n in m.net["noduri"] if not n.startswith("SIM-") and not n.endswith("-casa"))
    a = nodes[0]
    pa = (m.net["noduri"][a]["lat"], m.net["noduri"][a]["lon"])
    b = next(n for n in nodes[1:] if 150 <= dist_m(pa, (m.net["noduri"][n]["lat"], m.net["noduri"][n]["lon"])) <= 400)
    pb = (m.net["noduri"][b]["lat"], m.net["noduri"][b]["lon"])

    # --- 1. două noduri cunoscute: traseu pe străzi între ele, nu linie dreaptă
    t = plan(m, "LP-1", det={"noduri": [a, b]})
    p1 = m.predictii.get("PLAN-LP-1") or {}
    verifica("linie planificată (2 noduri): predicție punctată PLAN-*, metoda traseu_pe_strazi, propunere linie_planificata, nu aplicat",
             predictie_ok(t, "PLAN-LP-1") and not any(x["nivel"] == "in_model" for x in t["modificari"]), str(t["decizie"]))
    verifica("linie planificată (2 noduri): are pas analiza_harta, capete = cele 2 noduri, geometrie pe străzi (> 2 puncte), sursa id",
             pas(t, "analiza_harta") and p1.get("capete") == (a, b) and len(p1["puncte"]) > 2 and t["modificari"][0]["sursa_locatie"] == "id",
             f"{len(p1.get('puncte', []))} puncte")
    verifica("linie planificată (2 noduri): scorul nu depășește plafonul `id`; element în `predictii`, nu în rețea (PLAN-LP-1 nu e în net)",
             t["modificari"][0]["scor"] <= m.w["plafon_locatie"]["id"] and "PLAN-LP-1" not in m._elemente())
    t_id = plan(mk(), "LP-1b", det={}, text=f"Linie între {a} și {b}.")
    verifica("linie planificată: ID-urile a 2 noduri din textul raportului dau același rezultat ca `detalii.noduri`", predictie_ok(t_id, "PLAN-LP-1b"))

    # --- 2. două puncte GPS: traseu pe străzi între ele
    m2 = mk()
    t = plan(m2, "LP-2", det={"puncte": [{"lat": pa[0], "lon": pa[1]}, {"lat": pb[0], "lon": pb[1]}]})
    p2 = m2.predictii.get("PLAN-LP-2") or {}
    verifica("linie planificată (2 puncte GPS): predicție punctată pe străzi, sursa coordonate, geometrie cu > 2 puncte",
             predictie_ok(t, "PLAN-LP-2") and t["modificari"][0]["sursa_locatie"] == "coordonate" and len(p2.get("puncte", [])) > 2, str(len(p2.get("puncte", []))))

    # --- 3. stradă + indiciu ("între nr. 10 și 40"): segmentul de stradă din fereastră
    m3 = mk()
    t = plan(m3, "LP-3", ref=r_adr("Strada Crinului", None, {"tip": "intre", "numar": "40", "numar_2": "70"}), det={"lungime_m": 150})
    p3 = m3.predictii.get("PLAN-LP-3") or {}
    cs = pas(t, "cautare_strada")
    verifica("linie planificată (stradă + „între nr.”): predicție pe stradă, pas cautare_strada, sursa adresa_numar, nu neaplicat",
             predictie_ok(t, "PLAN-LP-3") and cs and t["modificari"][0]["sursa_locatie"] == "adresa_numar" and len(p3.get("puncte", [])) >= 2,
             f"{t['decizie']} {len(p3.get('puncte', []))} puncte")
    verifica("linie planificată (stradă): toate punctele segmentului sunt în zona de 3 km",
             all(zona_ok(p[0], p[1], m3.net, m3.w)["ok"] for p in p3["puncte"]))
    # fără indiciu, doar strada: segment tăiat la LINIE_MAX_M, sursa strada
    m3b = mk()
    t = plan(m3b, "LP-3b", ref=r_adr("Strada Crinului"))
    p3b = m3b.predictii.get("PLAN-LP-3b") or {}
    lung = sum(dist_m(x, y) for x, y in zip(p3b.get("puncte", []), p3b.get("puncte", [])[1:]))
    verifica("linie planificată (doar strada): predicție, sursa strada, segment nu toată strada", predictie_ok(t, "PLAN-LP-3b")
             and t["modificari"][0]["sursa_locatie"] == "strada", f"{lung:.0f} m")
    # colț „până la capăt"
    m3c = mk()
    t = plan(m3c, "LP-3c", ref=r_adr("Strada Crinului", None, {"tip": "colt", "strada_2": "Strada Liviu Rebreanu"}),
             text="Linie de la colțul cu Strada Liviu Rebreanu până la capăt.")
    verifica("linie planificată („de la colț până la capăt”): predicție pe stradă, sursa intersectie", predictie_ok(t, "PLAN-LP-3c")
             and t["modificari"][0]["sursa_locatie"] == "intersectie", f"{t['decizie']}")

    # --- 4. un singur nod + stradă: de la nod de-a lungul străzii
    m4 = mk()
    t = plan(m4, "LP-4", ref=r_adr("Strada Crinului", None, None, element_id=a), det={"lungime_m": 120})
    verifica("linie planificată (un nod + stradă): predicție de la nod de-a lungul străzii, sursa id", predictie_ok(t, "PLAN-LP-4")
             and t["modificari"][0]["sursa_locatie"] == "id", f"{t['decizie']}")

    # --- 5. fără loc -> neaplicat; un nod singur, fără direcție -> neaplicat
    m5 = mk()
    t = plan(m5, "LP-5", det={})
    verifica("linie planificată fără niciun indiciu de loc: neaplicat, nimic pe hartă", t["decizie"] == "neaplicat" and not t["modificari"]
             and "PLAN-LP-5" not in m5.predictii, t["decizie"])
    t = plan(m5, "LP-5b", det={"noduri": [a]})
    verifica("linie planificată cu un singur nod, fără stradă: neaplicat (fără direcție)", t["decizie"] == "neaplicat" and not t["modificari"], t["decizie"])

    # --- niciodată in_model, determinism, zona
    verifica("linie planificată: niciodată in_model, chiar cu sursă și extracție perfecte",
             predictie_ok(plan(mk(), "LP-6", det={"noduri": [a, b]}, inc=1.0, sursa="tableta_coordonate"), "PLAN-LP-6"))
    r1 = json.dumps(plan(mk(), "LP-7", ref=r_adr("Strada Crinului", None, {"tip": "intre", "numar": "40", "numar_2": "70"}))["modificari"], sort_keys=True)
    r2 = json.dumps(plan(mk(), "LP-7", ref=r_adr("Strada Crinului", None, {"tip": "intre", "numar": "40", "numar_2": "70"}))["modificari"], sort_keys=True)
    verifica("linie planificată: determinist (aceeași intrare, același rezultat)", r1 == r2)
    m8 = mk()
    t = plan(m8, "LP-8", det={"puncte": [{"lat": 44.30, "lon": 26.10}, {"lat": 44.301, "lon": 26.101}]})
    verifica("linie planificată: capete în afara zonei de 3 km -> neaplicat, eronat în cadrul prototipului", t["decizie"] == "neaplicat"
             and bool(t.get("eronat_prototip")) and "PLAN-LP-8" not in m8.predictii, t["decizie"])


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
             and abs(S.scor_la_data(0.9, "2026-08-01", "2026-08-31", w) - (0.9 + w["scor"]["scadere_per_30_zile"])) < 1e-9)   # rata normală din weights, nu constantă
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
    teste_verificare_om()
    teste_analiza_harta()
    teste_mutare_fire_document()
    teste_linie_planificata()

    ok, tot = sum(OK), len(OK)
    print(f"\nsmoke_sesiune4: {ok}/{tot} OK")
    if ok != tot:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
