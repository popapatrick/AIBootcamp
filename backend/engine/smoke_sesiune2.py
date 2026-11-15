"""Verificări pentru regulile noi din sesiunea 2 (mutare_fire, activ_demontat, val de apeluri, cerere_racordare,
locația din trace, acceptare parțială). Rulează: python -m backend.engine.smoke_sesiune2. Date FICTIVE."""
from __future__ import annotations

import copy
import json

from backend.engine import osm
from backend.engine.model import GridModel, ROOT

OK: list[bool] = []


def verifica(nume, cond, info=""):
    OK.append(bool(cond))
    print(("OK  " if cond else "FAIL"), nume, info)


def mk() -> GridModel:
    m = GridModel()
    m.traseu_fn = osm.traseu_fn()
    return m


def ev(i, data, echipa, tip, status="executat", ref=None, det=None, sursa=None, inc=0.9, forma="text_liber"):
    e = {"event_id": i, "echipa_sursa": echipa, "tip": tip, "status": status, "data": data, "forma_sursa": forma,
         "incredere_extractie": inc, "text_original": "test", "referinta": ref or {}, "detalii": det or {}}
    if sursa:
        e["tip_sursa_pondere"] = sursa
    return e


def snap(m, data, eid):
    return next((f["properties"] for f in m.snapshot(data)["features"] if f["properties"]["element_id"] == eid), None)


def main() -> None:
    # --- mutare_fire
    m = mk()
    n = m.net["noduri"]["6513200"]
    t = m.apply_event(ev("M-1", "2026-10-20", "mentenanta", "mutare_fire", "semnalat",
                         ref={"coordonate": {"lat": n["lat"], "lon": n["lon"]}}, det={"motiv_mutare": "sens_giratoriu"}))
    marcate = [x for x in t["modificari"] if x["nivel"] == "de_verificat"]
    verifica("mutare_fire: elementele din rază trec de_verificat (plafon respectat)",
             t["decizie"] == "de_verificat" and 3 <= len(marcate) <= m.w["mutare_fire"]["max_elemente"]
             and all(x["scor"] <= m.w["mutare_fire"]["scor_marcat"] for x in marcate), str(len(marcate)))
    verifica("mutare_fire: nu șterge nimic", all(snap(m, "2026-10-21", x["element_id"]) for x in marcate))
    prop = [x for x in t["modificari"] if x["nivel"] == "predictie"]
    verifica("mutare_fire: traseu nou propus punctat, neaplicat", len(prop) >= 1 and all(
        x["predictie"]["metoda"] == "zona_mutata" and x["element_id"] not in m.net["tronsoane"] for x in prop), str(len(prop)))
    verifica("mutare_fire: schimbari cu de_verificat și predictie",
             {"de_verificat", "predictie"} <= {s["ce"] for s in t["schimbari"]})
    t2 = m.apply_event(ev("M-2", "2026-10-25", "mentenanta", "verificare", "executat", ref={"element_id": marcate[0]["element_id"]},
                          sursa="tableta_coordonate"))
    s2 = snap(m, "2026-10-26", marcate[0]["element_id"])
    verifica("mutare_fire: confirmare ulterioară readuce elementul", s2["nivel"] == "in_model" and s2["verificat_recent"], f"{s2['nivel']} {s2['scor']}")
    t3 = m.apply_event(ev("DEC-M", "2026-10-27", "om_teren", "verificare", sursa="om_teren", inc=1.0,
                          det={"decizie": {"tinta_id": prop[0]["element_id"], "decizie": "accepta"}}))
    verifica("traseul propus poate fi acceptat de om", t3["decizie"] == "aplicat" and prop[0]["element_id"] in m.net["tronsoane"])
    ms = mk()
    ts = ms.apply_event(ev("M-3", "2026-10-20", "mentenanta", "mutare_fire", "semnalat", ref={"coordonate": {"lat": 10.0, "lon": 10.0}}))
    verifica("mutare_fire fără elemente în rază: neaplicat", ts["decizie"] == "neaplicat")

    # --- activ_demontat
    md = mk()
    a = md.apply_event(ev("D-1", "2026-10-20", "mentenanta", "activ_demontat", ref={"element_id": "A-T-014"}, sursa="formular", forma="campuri"))
    verifica("demontat: o singură mențiune nu scoate elementul", a["modificari"][0]["nivel"] != "scos_din_uz" and a["decizie"] == "scor_actualizat")
    b = md.apply_event(ev("D-2", "2026-10-22", "investitii", "activ_demontat", ref={"element_id": "A-T-014"}, sursa="formular", forma="campuri"))
    verifica("demontat: a doua echipă -> scos din uz", b["decizie"] == "aplicat" and b["modificari"][0]["nivel"] == "scos_din_uz"
             and any(s["ce"] == "scos_din_uz" for s in b["schimbari"]))
    mz = mk()
    mz.apply_event(ev("D-3", "2026-10-20", "mentenanta", "activ_demontat", ref={"element_id": "A-T-015"}, sursa="formular", forma="campuri"))
    z = mz.apply_event(ev("D-4", "2026-10-21", "mentenanta", "activ_demontat", ref={"element_id": "A-T-015"}, sursa="formular", forma="campuri"))
    verifica("demontat: aceeași echipă de două ori nu ajunge", z["modificari"][0]["nivel"] != "scos_din_uz")

    # --- val de apeluri
    mv = mk()
    un = GridModel().apply_event(ev("C-0", "2026-10-20", "apel_client", "avarie_semnalata", "semnalat", ref={"element_id": "A-T-030"}))
    d1 = un["modificari"][0]["motive"][0]["efect"]      # efectul apelului (fără scăderea în timp)
    ds = []
    for i, zi in enumerate(("2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23")):
        r = mv.apply_event(ev(f"C-{i + 1}", zi, "apel_client", "avarie_semnalata", "semnalat", ref={"element_id": "A-T-030"}))
        ds.append(r["modificari"][0]["motive"][0]["efect"])
    verifica("val de apeluri: al 3-lea apel pesează mai mult decât unul singur", ds[2] < d1 - 1e-6, f"{d1:.3f} vs {ds[2]:.3f}")
    verifica("val de apeluri: plafon", sum(ds) >= -mv.w["val_apeluri"]["plafon_semnal"] - 1e-6, f"suma {sum(ds):.3f}")

    verifica("timeline: etichete pentru val de apeluri, demontat, mutare_fire",
             any(x["eticheta"] == "val_apeluri" for x in mv.timeline()) and any(x["eticheta"] == "demontat" for x in md.timeline())
             and any(x["eticheta"] == "mutare_fire" and x["tip"] == "mutare_fire" for x in m.timeline())
             and any(x["eticheta"] == "decizie_om" for x in m.timeline()))

    # --- cerere_racordare
    mr = mk()
    nn = mr.net["noduri"]["6513200"]
    casa = {"lat": nn["lat"] + 0.0009, "lon": nn["lon"] + 0.0006}
    t = mr.apply_event(ev("R-1", "2026-10-20", "racordari", "cerere_racordare", "semnalat", ref={"coordonate": casa},
                          sursa="formular", forma="campuri"))
    noduri = [x for x in t["modificari"] if x["tip_element"] == "nod"]
    verifica("racordare: lanț prezis (stâlpi + casă), punctat, scor pe fiecare", t["decizie"] in ("predictie", "adaugat")
             and len(noduri) >= 2 and all(x["scor"] > 0 for x in t["modificari"]), f"{t['decizie']} {len(noduri)} noduri")
    verifica("racordare: pas predictie cu metoda lant_racordare", t["pasi"][-2]["rezultat"]["metoda"] == "lant_racordare")
    verifica("racordare: casa e nod de clasă casa", (snap(mr, "2026-10-21", "NOU-R-1-casa") or {}).get("clasa") == "casa")
    if t["decizie"] == "predictie":
        s1 = next(x["element_id"] for x in noduri if x["element_id"].endswith("-S1"))
        d = mr.apply_event(ev("DEC-R", "2026-10-25", "om_teren", "verificare", sursa="om_teren", inc=1.0,
                              det={"decizie": {"tinta_id": s1, "decizie": "accepta"}}))
        verifica("racordare: acceptare parțială (doar primul stâlp)", d["decizie"] == "aplicat" and s1 in mr.net["noduri"]
                 and "NOU-R-1-casa" not in mr.net["noduri"], str([(x["element_id"], x["ce"]) for x in d["schimbari"]]))
        r1 = mr.apply_event(ev("DEC-R2", "2026-10-26", "om_teren", "verificare", sursa="om_teren", inc=1.0,
                               det={"decizie": {"tinta_id": "NOU-R-1-casa", "decizie": "respinge"}}))
        verifica("racordare: restul respins", r1["decizie"] == "respins" and "NOU-R-1-casa" not in mr.net["noduri"])
    far = mr.apply_event(ev("R-2", "2026-10-21", "racordari", "cerere_racordare", "semnalat", ref={"coordonate": {"lat": 10.0, "lon": 10.0}},
                            sursa="formular", forma="campuri"))
    verifica("racordare: casă prea departe -> neaplicat cu motiv", far["decizie"] == "neaplicat" and far["pasi"][-1]["motive"])

    # --- locația operatorului (simulată): scor mai mic decât la clic, mereu predicție, sursa_locatie în pași
    from backend.racordare import locatie_operator_demo
    op = locatie_operator_demo("casă pe Strada Liviu Rebreanu", mr.net, osm.strazi(), mr.w)
    ploc = {"lat": op["lat"], "lon": op["lon"]}
    lo_op = {**ploc, "precizie_m": op["precizie_m"], "simulata": True}

    def rac(i, ref, det, sursa="apel_client"):
        t_ = mk().apply_event(ev(i, "2026-10-20", sursa if sursa == "apel_client" else "racordari", "cerere_racordare", "semnalat",
                                 ref=ref, det=det, sursa=sursa, forma="campuri" if sursa == "formular" else "text_liber"))
        return t_, next(p for p in t_["pasi"] if p["nume"] == "predictie")["rezultat"], t_["pasi"][-1]
    tc, pc, sc_ = rac("RC-1", {"coordonate": ploc}, {"locatie": ploc})
    to, po, so = rac("RO-1", {"adresa": "Strada Liviu Rebreanu"}, {"locatie_operator": lo_op})
    verifica("operator: scor mai mic decât la clic, ambele predicție",
             so["rezultat"]["scor_propunere"] < sc_["rezultat"]["scor_propunere"] and to["decizie"] == tc["decizie"] == "predictie",
             f"operator {so['rezultat']['scor_propunere']} < clic {sc_['rezultat']['scor_propunere']}")
    verifica("operator: sursa_locatie în predictie și potrivire", po["sursa_locatie"] == "operator_simulat" and pc["sursa_locatie"] == "clic"
             and next(p for p in to["pasi"] if p["nume"] == "potrivire")["rezultat"]["sursa_locatie"] == "operator_simulat")
    verifica("operator: jurnal „de ce” spune simulată + precizie", "SIMULATĂ" in so["motive"][0] and f"±{op['precizie_m']:g} m" in so["motive"][0])
    verifica("operator: lanț prezis, elemente punctate", po["metoda"] == "lant_racordare" and any(
        x["nivel"] == "predictie" for x in to["modificari"]))
    tf_, _, sf_ = rac("RO-2", {}, {"locatie_operator": lo_op}, "formular")   # sursă bună, dar poziție simulată: tot predicție
    verifica("operator: nu se aplică singur, nici la sursă bună", tf_["decizie"] == "predictie")
    tp_, pp_, _ = rac("RO-3", {"coordonate": {"lat": ploc["lat"] + 0.0001, "lon": ploc["lon"]}}, {"locatie_operator": lo_op})
    verifica("operator: coordonatele din text au prioritate", pp_["sursa_locatie"] == "text")
    tq_, pq_, _ = rac("RO-4", {}, {"locatie": ploc, "locatie_operator": lo_op})
    verifica("operator: clicul are prioritate", pq_["sursa_locatie"] == "clic")

    # --- locația din traseul tabletei
    trasee = json.loads((ROOT / "data" / "reports" / "trasee-dummy.json").read_text(encoding="utf-8"))
    tr = trasee[0]
    mt = mk()
    t = mt.apply_event(ev("T-1", tr["data"], "mentenanta", "nod_lipsa", ref={"adresa": tr["adresa"]}, det={"trace": tr["puncte"]},
                          sursa="tableta_coordonate", forma="campuri"))
    pas_trace = next((p for p in t["pasi"] if p["nume"] == "trace"), None)
    verifica("trace: pas trace cu oprirea aleasă", pas_trace and pas_trace["rezultat"].get("alegere"), str((pas_trace or {}).get("rezultat", {}).get("alegere")))
    verifica("trace: stâlp nou prezis la oprirea fără stâlp", t["decizie"] in ("predictie", "adaugat")
             and any(s["ce"] in ("predictie", "adaugat") for s in t["schimbari"]), t["decizie"])
    verifica("trace: stâlpii vizitați primesc verificare", any(s["ce"] == "actualizat" for s in t["schimbari"]))
    verifica("trace: coordonatele din trace nu se aplică dacă raportul are deja ID",
             not any(p["nume"] == "trace" for p in GridModel().apply_event(
                 ev("T-2", tr["data"], "mentenanta", "verificare", ref={"element_id": "A-T-001", "adresa": tr["adresa"]},
                    det={"trace": tr["puncte"]}))["pasi"]))

    # --- safeguard: zona prototipului (3 km față de centroidul rețelei de start)
    from backend.engine.zona import zona_ok
    mz = mk()
    c0 = mz.net["_zona_centru"]
    def la_nord(m_):   # punct la m_ metri la nord de centru
        return {"lat": c0[0] + m_ / 111_320, "lon": c0[1]}
    z29, z31 = zona_ok(**la_nord(2900), net=mz.net, cfg=mz.w), zona_ok(**la_nord(3100), net=mz.net, cfg=mz.w)
    verifica("zona: 2,9 km în zonă, 3,1 km în afară", z29["ok"] and not z31["ok"], f"{z29['distanta_m']} / {z31['distanta_m']}")
    t40 = mz.apply_event(ev("Z-1", "2026-09-01", "mentenanta", "nod_lipsa", ref={"coordonate": la_nord(40_000)}))
    verifica("zona: coordonate la 40 km = eronat în prototip, neaplicat", t40["decizie"] == "neaplicat" and t40.get("eronat_prototip")
             and "in_afara_zonei_prototip" in next(p_ for p_ in t40["pasi"] if p_["nume"] == "potrivire")["rezultat"]["semnale"] and not t40["modificari"])
    verifica("zona: motivul spune distanța și limita", "40" in t40["pasi"][-1]["motive"][0] and "3000" in t40["pasi"][-1]["motive"][0],
             t40["pasi"][-1]["motive"][0])
    tm = mz.apply_event(ev("Z-2", "2026-09-02", "mentenanta", "mutare_fire", det={"centru": la_nord(5000)}))
    verifica("zona: mutare_fire în afara zonei = eronat", tm["decizie"] == "neaplicat" and tm.get("eronat_prototip"))
    tr_ = mz.apply_event(ev("Z-3", "2026-09-03", "racordari", "cerere_racordare", ref={"coordonate": la_nord(6000)}, sursa="om_teren"))
    verifica("zona: cerere de racordare în afara zonei = eronat, fără excepție pe sursă", tr_["decizie"] == "neaplicat" and tr_.get("eronat_prototip"))
    ti = mz.apply_event(ev("Z-4", "2026-09-04", "mentenanta", "nod_lipsa", ref={"coordonate": la_nord(1500)}))
    verifica("zona: 1,5 km nu e eronat", not ti.get("eronat_prototip"))

    # --- origine: rețea de start vs generat de model
    mo = mk()
    sn0 = {f["properties"]["element_id"]: f["properties"] for f in mo.snapshot("2026-08-01")["features"]}
    # V2 (sesiunea 4): KMZ = retea_start cu acuratete.initial_gis; SIM-* = generat_model (din rapoarte mai vechi), t0
    gis0 = {e_: p for e_, p in sn0.items() if not e_.startswith("SIM-")}
    sim0 = {e_: p for e_, p in sn0.items() if e_.startswith("SIM-")}
    verifica("origine: rețeaua KMZ are origine retea_start și scor acuratete.initial_gis; SIM-* sunt generat_model cu t0",
             all(p["origine"] == "retea_start" for p in gis0.values())
             and {p["scor"] for p in gis0.values()} == {mo.w["acuratete"]["initial_gis"]}
             and all(p["origine"] == "generat_model" and p["t0"] for p in sim0.values()))
    tn = mo.apply_event(ev("O-1", "2026-09-05", "mentenanta", "nod_lipsa", ref={"coordonate": la_nord(300)}, sursa="tableta_coordonate", forma="campuri"))
    nou = [m_ for m_ in tn["modificari"] if m_["element_id"] not in sn0]
    verifica("origine: elementul adăugat de sistem e generat_model", nou and all(m_["origine"] == "generat_model" for m_ in nou))
    sn1 = {f["properties"]["element_id"]: f["properties"] for f in mo.snapshot("2026-09-05")["features"]}
    verifica("origine: elementele rețelei rămân cu originea lor (KMZ retea_start, SIM-* generat_model) după evenimente",
             all(sn1[e_]["origine"] == sn0[e_]["origine"] for e_ in sn0 if e_ in sn1))
    pred = [p for p in sn1.values() if p.get("predictie")]
    verifica("origine: predicțiile au predictie.origine generat_model", all(p["predictie"]["origine"] == "generat_model" for p in pred))

    # --- puncte simulate hardcodate = parte din rețeaua de start
    mp = mk()
    sim = [e for e in mp.net["noduri"] if e.startswith("SIM-")]
    verifica("puncte simulate: 55 de noduri SIM-* în rețeaua de start, toate generat_model (din rapoarte mai vechi, t0) și în zonă",
             len(sim) == 55 and all(mp.istoric[e][0]["origine"] == "generat_model" and mp.istoric[e][0]["t0"] for e in sim)
             and all(zona_ok(mp.net["noduri"][e]["lat"], mp.net["noduri"][e]["lon"], mp.net, mp.w)["ok"] for e in sim), str(len(sim)))
    verifica("puncte simulate: tronsoanele SIM-L* au capete în rețea",
             all(c in mp.net["noduri"] for t_ in mp.net["tronsoane"].values() if t_["id"].startswith("SIM-L") for c in t_["capete"]))

    # --- geocodare în potrivire (adresă -> coordonate) și plafon de standardizare
    import backend.engine.osm as osm_g
    nume_str = next((x["nume"] for x in osm_g.strazi() if x.get("nume")), None)
    mg = mk()
    tg = mg.apply_event(ev("G-1", "2026-09-10", "mentenanta", "nod_lipsa", ref={"adresa_structurata": {"strada": nume_str, "numar": "12", "localitate": None, "reper": None}}, inc=0.95))
    pg = next((p for p in tg["pasi"] if p["nume"] == "geocodare"), None)
    verifica("geocodare: pas cu coordonate din adresă", pg and pg["rezultat"]["status"] == "gasit", str(pg and pg["rezultat"]))
    pm = next(p for p in tg["pasi"] if p["nume"] == "potrivire")["rezultat"]
    # V6 (schimbat intenționat): adresa cu stradă + număr caută în fereastra de pe stradă, deci metoda e `cautare_strada`, nu `adresa`
    verifica("geocodare: potrivirea nu mai e nepotrivit „doar adresă” (V6: căutare pe stradă)", pm["status"] != "nepotrivit" and pm["metoda"] == "cautare_strada"
             and "cautare_strada" in pm["semnale"] and any(p["nume"] == "cautare_strada" for p in tg["pasi"]), pm["status"] + " " + str(pm["metoda"]))
    verifica("standardizare: încrederea extracției plafonată la strada_numar (0,7)", tg["pasi"][0]["incredere"] == 0.7, str(tg["pasi"][0]["incredere"]))
    th = mg.apply_event(ev("G-2", "2026-09-11", "mentenanta", "nod_lipsa", ref={"adresa": "Strada Inexistenta Zzz"}, inc=0.9))
    verifica("geocodare: stradă necunoscută -> fără coordonate inventate",
             next(p for p in th["pasi"] if p["nume"] == "potrivire")["rezultat"]["status"] == "nepotrivit" and th["decizie"] == "neaplicat")
    # stradă fără număr: V6 caută în fereastra (toată strada); fără candidați, nod_lipsa devine element nou (înainte: semnalul
    # `adresa_prea_imprecisa_pentru_element_existent`, schimbat intenționat)
    tstr = mk().apply_event(ev("G-5", "2026-09-13", "mentenanta", "nod_lipsa", ref={"adresa_structurata": {"strada": nume_str, "numar": None, "localitate": None, "reper": None}}, inc=0.9))
    pstr = next(p for p in tstr["pasi"] if p["nume"] == "potrivire")["rezultat"]
    verifica("geocodare: stradă fără număr nu se potrivește pe element existent (precizie > rază)", pstr["status"] == "absent_din_model"
             and "cautare_strada" in pstr["semnale"] and tstr["decizie"] != "neaplicat", pstr["status"])
    tavr = mk().apply_event(ev("G-6", "2026-09-13", "mentenanta", "avarie_semnalata", ref={"adresa_structurata": {"strada": nume_str, "numar": None, "localitate": None, "reper": None}}, inc=0.9))
    # V6 (schimbat intenționat): avaria doar cu stradă nu mai e `neaplicat`; nu se lipește pe un element (nepotrivit ≠ ales), ci pin/de verificat
    verifica("geocodare: avarie doar cu stradă = nu se lipește pe un element, nu e neaplicat (V6)",
             next(p for p in tavr["pasi"] if p["nume"] == "potrivire")["rezultat"]["status"] in ("absent_din_model", "ambiguu")
             and tavr["decizie"] == "de_verificat" and not any(x["ce"] == "actualizat" for x in tavr["schimbari"]))
    ts = mg.apply_event(ev("G-3", "2026-09-12", "mentenanta", "verificare", ref={"element_id": "A-T-001"}, inc=1.0))
    verifica("standardizare: cu ID nu se plafonează", ts["pasi"][0]["incredere"] == 1.0)

    # --- traseu generat la raport: bonus, zgomot, decalaj (contradicție), dezactivare
    def mk_tr(activ=1):
        # sesiunea 4 (V7): traseul generat e oprit în weights; testele lui rulează cu o copie având `demo.trace_generat_activ = 1`
        w_ = copy.deepcopy(mk().w)
        w_.setdefault("demo", {})["trace_generat_activ"] = activ
        m_ = GridModel(weights=w_)
        m_.traseu_fn = osm.traseu_fn()
        return m_

    def tfac(i, par=None, coord=None):
        t_ = mk_tr().apply_event(ev(i, "2026-09-20", "mentenanta", "nod_lipsa", ref={"coordonate": coord or la_nord(200)},
                                 det={"trace_params": par} if par else {}, sursa="tableta_coordonate", forma="campuri"))
        p_ = next((x for x in t_["pasi"] if x["nume"] == "trace"), None)
        return t_, p_
    _, p_b = tfac("TG-1", {"zgomot_m": 3, "durata_oprire_min": 15})
    _, p_z = tfac("TG-2", {"zgomot_m": 40, "durata_oprire_min": 15})
    _, p_d = tfac("TG-3", {"zgomot_m": 3, "durata_oprire_min": 15, "decalaj_m": 120})
    _, p_a = tfac("TG-4", {"zgomot_m": 3, "durata_oprire_min": 15, "acoperire": 0.4})
    tz_, p_x = tfac("TG-5", {"dezactivat": True})
    fb = p_b["rezultat"]["factor_trace"] if p_b else None
    t_of = mk().apply_event(ev("TG-OFF", "2026-09-20", "mentenanta", "nod_lipsa", ref={"coordonate": la_nord(200)},
                               sursa="tableta_coordonate", forma="campuri"))
    verifica("trace generat: oprit implicit (demo.trace_generat_activ=0): fără pas trace, fără trace_*",
             mk().w["demo"]["trace_generat_activ"] == 0 and not any(x["nume"] == "trace" for x in t_of["pasi"])
             and not any(k in (t_of.get("detalii") or {}) for k in ("trace_params", "trace_sursa", "trace_factor")))
    verifica("trace generat: bonus peste 1 dar sub plafon", p_b and 1.0 < fb <= 1 + mk().w["trace_generat"]["bonus_max"] + 1e-9, str(fb))
    verifica("trace generat: etichetat simulat", p_b and p_b["rezultat"]["sursa"] == "simulat")
    verifica("trace generat: zgomot mare nu mai dă bonus", p_z and p_z["rezultat"]["factor_trace"] <= 1.0, str(p_z and p_z["rezultat"]["factor_trace"]))
    verifica("trace generat: oprire decalată = contradicție, factor mai mic",
             p_d and p_d["rezultat"]["factor_trace"] < fb and "contradic" in p_d["rezultat"]["motiv"], str(p_d and p_d["rezultat"]))
    verifica("trace generat: acoperire mică scade", p_a and p_a["rezultat"]["factor_trace"] < fb)
    verifica("trace generat: dezactivabil, fără eroare", p_x is None and tz_["decizie"] is not None)
    t1_, _ = tfac("TG-6", {"zgomot_m": 3, "durata_oprire_min": 15})
    t2_, _ = tfac("TG-6", {"zgomot_m": 3, "durata_oprire_min": 15})
    verifica("trace generat: determinist pe event_id", t1_["pasi"][-1] == t2_["pasi"][-1])

    # --- racordare cu rezerve: fără „neaplicat” din lipsă de date
    mq = mk()
    c0q = mq.net["_zona_centru"]
    def racq(i, ref, det=None, sursa="apel_client", inc=0.9):
        t_ = mk().apply_event(ev(i, "2026-10-22", "apel_client" if sursa == "apel_client" else "racordari", "cerere_racordare", "semnalat",
                                 ref=ref, det=det or {}, sursa=sursa, forma="text_liber", inc=inc))
        pr_ = next((p for p in t_["pasi"] if p["nume"] == "predictie"), None)
        return t_, (pr_ or {}).get("rezultat") or {}
    # casă la ~2,5 km de orice nod (în zonă, departe de rețea): treapta 3 sau 4, tot predicție (slabă), nu neaplicat
    t_far, p_far = racq("RQ-1", {"coordonate": {"lat": c0q[0] + 2500 / 111_320, "lon": c0q[1]}})
    verifica("racordare: casă departe de rețea nu mai e neaplicat", t_far["decizie"] in ("predictie", "adaugat") and not t_far.get("eronat_prototip"),
             t_far["decizie"] + " " + str(t_far["pasi"][-1].get("motive")))
    verifica("racordare: treapta 3 sau 4 în pași și slabă", p_far.get("treapta") in (3, 4) and t_far["pasi"][-1]["rezultat"].get("slaba") is True,
             str(p_far.get("treapta")))
    verifica("racordare: punctul casei rămâne pe hartă (modificare cu predictie.slaba)",
             any(x["element_id"].endswith("-casa") and (x.get("predictie") or {}).get("slaba") for x in t_far["modificari"]))
    # casă lângă rețea, treapta 1, scor normal
    ploc2 = {"lat": c0q[0] + 20 / 111_320, "lon": c0q[1] + 20 / 111_320}
    t_n, p_n = racq("RQ-2", {"coordonate": ploc2}, sursa="formular", inc=0.95)
    verifica("racordare: lângă rețea = treapta 1/2, nu slabă", p_n.get("treapta") in (1, 2) and t_n["pasi"][-1]["rezultat"].get("slaba") is False,
             str(p_n.get("treapta")))
    # singurele neaplicate: fără locație și în afara zonei
    t_0, _ = racq("RQ-3", {})
    verifica("racordare: fără locație = neaplicat cu motiv", t_0["decizie"] == "neaplicat" and "locația" in t_0["pasi"][-1]["motive"][0])
    t_o, _ = racq("RQ-4", {"coordonate": {"lat": c0q[0] + 9000 / 111_320, "lon": c0q[1]}})
    verifica("racordare: în afara zonei = neaplicat eronat", t_o["decizie"] == "neaplicat" and t_o.get("eronat_prototip"))

    # --- timeline derulabil: schimbari și pasi pe fiecare intrare
    mt_ = mk()
    mt_.apply_event(ev("TL-1", "2026-09-01", "mentenanta", "nod_lipsa", ref={"coordonate": la_nord(300)}, sursa="tableta_coordonate", forma="campuri"))
    mt_.apply_event(ev("TL-2", "2026-09-02", "mentenanta", "nod_lipsa", ref={"coordonate": la_nord(60_000)}))
    tl_ = mt_.timeline()
    verifica("timeline: fiecare intrare are schimbari, pasi, eronat_prototip", len(tl_) == 2 and all(
        isinstance(x["schimbari"], list) and x["pasi"] and "eronat_prototip" in x for x in tl_))
    verifica("timeline: scor înainte -> după și „de ce” în schimbări", tl_[0]["schimbari"] and all(
        {"element_id", "ce", "scor_dupa", "de_ce"} <= set(c_) for c_ in tl_[0]["schimbari"]))
    verifica("timeline: evenimentul eronat e marcat", tl_[1]["eronat_prototip"] and not tl_[0]["eronat_prototip"])

    assert all(OK), "unele verificări au eșuat"
    print(f"OK: {len(OK)} verificări")


if __name__ == "__main__":
    main()
