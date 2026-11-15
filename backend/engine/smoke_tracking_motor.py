"""Verificări pentru tracking echipe în motor (B2): evenimentul `tracking_tura`.

Rulează: EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_tracking_motor. Date FICTIVE.
Acoperă: validare (stâlp portocaliu -> galben), stâlp presupus + legătură pe străzi, oprire scurtă, oprire neclară, verificat de om,
două opriri la același stâlp, aceeași tură de două ori, tură generată cu `genereaza_tura`, regimul de scădere la data turei,
zona de 3 km, determinism, snapshot/timeline.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from backend.engine import osm
from backend.engine import scoring as S
from backend.engine.network import dist_m
from backend.engine.model import GridModel
from backend.engine.zona import zona_ok
from backend.tracking import genereaza_tura

OK: list[bool] = []
M_LAT = 111_320.0


def verifica(nume, cond, detaliu=""):
    OK.append(bool(cond))
    print(("OK  " if cond else "FAIL"), nume, detaliu)


def mk() -> GridModel:
    m = GridModel()
    m.traseu_fn = osm.traseu_fn()
    return m


def ev_tura(i: str, data: str, puncte: list[dict], tura_id: str | None = None, echipa: str = "mentenanta") -> dict:
    return {"event_id": i, "echipa_sursa": echipa, "tip": "tracking_tura", "status": "executat", "data": data,
            "tip_sursa_pondere": "tracking_gps", "incredere_extractie": 1.0, "forma_sursa": "campuri", "referinta": {},
            "detalii": {"tura": {"tura_id": tura_id or f"TURA-{i}", "seed": "test", "echipa": echipa, "puncte": puncte}}}


def stationar(lat: float, lon: float, t0: datetime, minute: float, pas: int = 15) -> list[dict]:
    """Puncte GPS pe loc `minute` minute (zgomot determinist sub 1 m); prima la t0, ultima la t0 + minute."""
    jit = [(0.0, 0.0), (0.4, 0.0), (0.0, 0.4), (-0.4, 0.0), (0.0, -0.4)]
    n = int(round(minute * 60 / pas))
    out = []
    for k in range(n + 1):
        dy, dx = jit[k % len(jit)]
        out.append({"t": (t0 + timedelta(seconds=k * pas)).isoformat(), "lat": lat + dy / M_LAT, "lon": lon + dx / (M_LAT * 0.7)})
    return out


def mers(lat: float, lon: float, t0: datetime, pasi: int, dlon_m: float = 20.0, pas: int = 15) -> list[dict]:
    """`pasi` puncte de mers spre est, la `dlon_m` metri unul de altul (peste raza de oprire, deci nu formează oprire)."""
    return [{"t": (t0 + timedelta(seconds=k * pas)).isoformat(), "lat": lat, "lon": lon + (k + 1) * dlon_m / (M_LAT * 0.7)}
            for k in range(pasi)]


def lat_n(lat: float, m: float) -> float:
    return lat + m / M_LAT


def snap(m, data, eid):
    return next((f["properties"] for f in m.snapshot(data)["features"] if f["properties"]["element_id"] == eid), None)


def opriri(tr: dict) -> list[dict]:
    return next(p for p in tr["pasi"] if p["nume"] == "opriri")["rezultat"]["opriri"]


def izolat(m: GridModel, cond, raza: float = 35.0) -> str | None:
    """Un nod SIM-* cu `cond(stare)` și niciun alt nod la mai puțin de `raza` m (ca potrivirea să fie neambiguă)."""
    noduri = m.net["noduri"]
    for eid in sorted(noduri):
        if not eid.startswith("SIM-") or not cond(m.istoric[eid][-1]):
            continue
        n = noduri[eid]
        if all(dist_m((n["lat"], n["lon"]), (o["lat"], o["lon"])) >= raza for k, o in noduri.items() if k != eid):
            return eid
    return None


def loc_fara_stalp(m: GridModel, minim: float = 60.0) -> tuple[float, float]:
    """Un punct de pe o stradă OSM, în zonă, la cel puțin `minim` m de orice nod."""
    noduri = [(n["lat"], n["lon"]) for n in m.net["noduri"].values()]
    for s in osm.strazi():
        for p in s["puncte"]:
            if zona_ok(p[0], p[1], m.net, m.w)["ok"] and zona_ok(p[0], p[1], m.net, m.w)["distanta_m"] < 2500 \
                    and min(dist_m(tuple(p), q) for q in noduri) >= minim:
                return (p[0], p[1])
    raise SystemExit("nu există loc fără stâlp pe o stradă")


def teste_manuale():
    D = "2026-08-01"      # data de start a modelului: fără scădere în timp, ca scorurile „înainte” să fie cele stocate
    t0 = datetime.fromisoformat(f"{D}T08:00:00")
    m = mk()
    T = m.w["tracking"]
    portocaliu = izolat(m, lambda st: st["scor"] == m.w["retea_start"]["scor_portocaliu"])
    verifica("exista un SIM portocaliu izolat (scor 0,50) pentru teste", portocaliu is not None, str(portocaliu))
    n = m.net["noduri"][portocaliu]

    # --- validare: 8 min la 4 m de un SIM portocaliu
    p = stationar(lat_n(n["lat"], 4), n["lon"], t0, 8)
    tr = m.apply_event(ev_tura("TR-1", D, p))
    o = opriri(tr)
    verifica("validare: o oprire, tip validare, la ~4 m", len(o) == 1 and o[0]["tip"] == "validare" and o[0]["element_id"] == portocaliu
             and 3.5 <= o[0]["distanta_m"] <= 4.5, str({k: o[0].get(k) for k in ("tip", "element_id", "distanta_m", "durata_min")}))
    cal = 1 - 0.5 * o[0]["distanta_m"] / T["raza_validare_m"]
    asteptat = 0.5 + m.w["scor"]["confirmare_teren"] * m.w["fiabilitate_sursa"]["tracking_gps"] * cal
    s = snap(m, D, portocaliu)
    verifica("validare: scorul crește ~+0,13 (0,50 -> ~0,63) și devine galben", abs(s["scor"] - asteptat) < 0.005 and 0.60 <= s["scor"] <= 0.66
             and s["banda"] == "galben", f"scor {s['scor']} (așteptat {asteptat:.3f}), banda {s['banda']}")
    verifica("validare: sursa_locatie devine coordonate (plafon 0,85), ultima_verificare și ultima_validare_tracking = data",
             s["sursa_locatie"] == "coordonate" and s["ultima_verificare"] == D and s.get("ultima_validare_tracking") == D,
             f"{s['sursa_locatie']} {s['ultima_verificare']} {s.get('ultima_validare_tracking')}")
    verifica("validare: motivul pomenește tura, echipa, durata și distanța",
             "TURA-TR-1" in s["motive"][0]["text"] and "mentenanta" in s["motive"][0]["text"] and "8 min" in s["motive"][0]["text"]
             and "m." in s["motive"][0]["text"], s["motive"][0]["text"][:110])
    verifica("validare: decizia scor_actualizat, eticheta tracking, schimbari cu înainte/după/bandă",
             tr["decizie"] == "scor_actualizat" and m.jurnal[-1]["eticheta"] == "tracking"
             and tr["schimbari"][0]["element_id"] == portocaliu and tr["schimbari"][0]["scor_inainte"] == 0.5
             and tr["schimbari"][0]["banda_inainte"] == "portocaliu" and tr["schimbari"][0]["banda_dupa"] == "galben"
             and tr["schimbari"][0]["ce"] == "actualizat", str(tr["schimbari"][0]))
    verifica("validare: oprirea are scor_inainte/scor_dupa/banda și t_ajungere = inceput",
             o[0]["scor_inainte"] == 0.5 and o[0]["scor_dupa"] == s["scor"] and o[0]["banda_inainte"] == "portocaliu"
             and o[0]["banda_dupa"] == "galben" and o[0]["t_ajungere"] == o[0]["inceput"])
    ev = m.jurnal[-1]
    verifica("jurnal/timeline: rezumat lizibil, pași opriri + validari_tracking, eticheta tracking",
             "Tura echipei mentenanta: 1 stâlp confirmat" in ev["rezumat"] and [p["nume"] for p in tr["pasi"]][:2] == ["opriri", "validari_tracking"]
             and m.timeline()[-1]["eticheta"] == "tracking" and "confirmat" in m.timeline()[-1]["rezumat"], ev["rezumat"])
    # --- aceeași tură a doua oară
    inainte = snap(m, D, portocaliu)["scor"]
    tr2 = m.apply_event(ev_tura("TR-1b", D, p, tura_id="TURA-TR-1"))
    verifica("aceeași tură de două ori: a doua `fara_efect`, motiv „deja aplicată”, scorul neschimbat",
             tr2["decizie"] == "fara_efect" and "deja aplicată" in tr2["pasi"][-1]["motive"][0] and "TURA-TR-1" in tr2["pasi"][-1]["motive"][0]
             and snap(m, D, portocaliu)["scor"] == inainte and not tr2["modificari"], tr2["pasi"][-1]["motive"][0])

    # --- oprire scurtă 1-2 min lângă un stâlp: ignorată
    m = mk()
    n = m.net["noduri"][izolat(m, lambda st: True)]
    eid_s = izolat(m, lambda st: True)
    e2 = ev_tura("TR-2", D, stationar(lat_n(n["lat"], 3), n["lon"], t0, 1.5))
    tr = m.apply_event(e2)
    o = opriri(tr)
    verifica("oprire de 1,5 min lângă stâlp: `scurta`, fără efect, nimic modificat",
             len(o) == 1 and o[0]["tip"] == "scurta" and tr["decizie"] == "fara_efect" and not tr["modificari"]
             and snap(m, D, eid_s)["scor"] == m.istoric[eid_s][0]["scor"], str(o))
    verifica("oprire scurtă: detalii.tracking.ignorate = 1, rezumat „1 oprire scurtă”",
             e2["detalii"]["tracking"]["ignorate"] == 1 and "1 oprire scurtă" in m.jurnal[-1]["rezumat"], m.jurnal[-1]["rezumat"])

    # --- oprire 15 min fără stâlp
    m = mk()
    la, lo = loc_fara_stalp(m)
    p = stationar(la, lo, t0, 15)
    e = ev_tura("TR-3", D, p)
    tr = m.apply_event(e)
    o = opriri(tr)
    trk = [x for x in o if x["tip"] == "stalp_presupus"]
    verifica("oprire 15 min fără stâlp: tip stalp_presupus, TRK-<event>-1", len(o) == 1 and len(trk) == 1 and trk[0]["element_id"] == "TRK-TR-3-1",
             str(trk))
    sp = snap(m, D, "TRK-TR-3-1")
    verifica("TRK: predicție (nivel predictie), scor <= 0,45, metoda oprire_tracking, sursa coordonate, origine model",
             sp and sp["nivel"] == "predictie" and sp["scor"] <= T["plafon_stalp_presupus"] and sp["predictie"]["metoda"] == "oprire_tracking"
             and sp["sursa_locatie"] == "coordonate" and sp["predictie"]["origine"] == "generat_model", str(sp and (sp["nivel"], sp["scor"])))
    verifica("TRK: nu e în rețea (net) și nu a fost aplicat", "TRK-TR-3-1" not in m.net["noduri"] and "TRK-TR-3-1" in m.predictii)
    leg = snap(m, D, "TRK-TR-3-1-L")
    verifica("TRK: legătura pe străzi TRK-…-L e predicție, scor <= plafon analiza_harta, capete (stâlp existent, TRK)",
             leg and leg["nivel"] == "predictie" and leg["scor"] <= S.plafon("analiza_harta", m.w) and leg["predictie"]["metoda"] == "traseu_pe_strazi"
             and m.predictii["TRK-TR-3-1-L"]["capete"][1] == "TRK-TR-3-1" and m.predictii["TRK-TR-3-1-L"]["capete"][0] in m.net["noduri"],
             str(leg and (leg["nivel"], leg["scor"], leg["predictie"]["metoda"])))
    verifica("TRK: `analiza_harta` în pași, decizie predictie, schimbari ce=predictie pe nod și legătură, detalii.tracking.presupuneri",
             "analiza_harta" in [p["nume"] for p in tr["pasi"]] and tr["decizie"] == "predictie"
             and {s["element_id"]: s["ce"] for s in tr["schimbari"]} == {"TRK-TR-3-1": "predictie", "TRK-TR-3-1-L": "predictie"}
             and e["detalii"]["tracking"]["presupuneri"] == ["TRK-TR-3-1"], str([s["ce"] for s in tr["schimbari"]]))
    verifica("TRK: în zona de 3 km", zona_ok(la, lo, m.net, m.w)["ok"])
    # omul acceptă: devine nod real (compatibil cu decizia omului)
    dec = {"event_id": "DEC-1", "echipa_sursa": "om_teren", "tip": "verificare", "status": "executat", "data": D, "forma_sursa": "campuri",
           "incredere_extractie": 1.0, "text_original": "ok", "referinta": {}, "detalii": {"decizie": {"tinta_id": "TRK-TR-3-1", "decizie": "accepta"}}}
    m.apply_event(dec)
    verifica("TRK acceptat de om în teren: intră în rețea, verificat de om (grupul nod + legătură)",
             "TRK-TR-3-1" in m.net["noduri"] and "TRK-TR-3-1-L" in m.net["tronsoane"] and snap(m, D, "TRK-TR-3-1")["verificat_om"] is True)

    # --- oprire în afara zonei (15 min, ~5 km nord): niciun element nou
    m = mk()
    c = m.net["_zona_centru"]
    tr = m.apply_event(ev_tura("TR-4", D, stationar(c[0] + 0.045, c[1], t0, 15)))
    o = opriri(tr)
    verifica("oprire de 15 min în afara zonei de 3 km: neclara, fără TRK, fără modificări",
             o[0]["tip"] == "neclara" and "zonei" in o[0]["motiv"] and not tr["modificari"] and tr["decizie"] == "fara_efect"
             and not any(k.startswith("TRK-") for k in m.predictii), o[0]["motiv"])

    # --- oprire 8 min la 20 m (între praguri): neclară
    m = mk()
    eid = izolat(m, lambda st: True, raza=45.0)
    n = m.net["noduri"][eid]
    inainte = snap(m, D, eid)["scor"]
    tr = m.apply_event(ev_tura("TR-5", D, stationar(lat_n(n["lat"], 20), n["lon"], t0, 8)))
    o = opriri(tr)
    verifica("oprire 8 min la 20 m (între praguri): neclara, fără efect, scor neschimbat",
             len(o) == 1 and o[0]["tip"] == "neclara" and tr["decizie"] == "fara_efect" and snap(m, D, eid)["scor"] == inainte
             and not any(k.startswith("TRK-") for k in m.predictii), str(o[0]["tip"]))

    # --- stâlp verificat de om: neschimbat
    m = mk()
    eid = izolat(m, lambda st: st["scor"] < 0.7)
    n = m.net["noduri"][eid]
    m.apply_event({"event_id": "VER-1", "echipa_sursa": "om_teren", "tip": "verificare_om", "status": "executat", "data": D,
                   "forma_sursa": "campuri", "incredere_extractie": 1.0, "text_original": "", "referinta": {}, "detalii": {"tinta_id": eid}})
    inainte = snap(m, D, eid)
    tr = m.apply_event(ev_tura("TR-6", D, stationar(lat_n(n["lat"], 4), n["lon"], t0, 8)))
    dupa = snap(m, D, eid)
    verifica("stâlp verificat de om: scorul și verificat_om neschimbate, motiv în jurnal despre tură",
             dupa["scor"] == inainte["scor"] and dupa["verificat_om"] is True and dupa["motive"][0]["eveniment"] == "TR-6"
             and "verificat de om" in dupa["motive"][0]["text"] and "TURA-TR-6" in dupa["motive"][0]["text"]
             and tr["schimbari"][0]["scor_inainte"] == tr["schimbari"][0]["scor_dupa"] and tr["decizie"] == "fara_efect",
             f"{inainte['scor']} -> {dupa['scor']} {tr['decizie']}")
    verifica("stâlp verificat de om: nu primește ultima_validare_tracking", "ultima_validare_tracking" not in dupa)

    # --- două opriri la același stâlp: o singură validare (oprirea cea mai lungă)
    m = mk()
    eid = izolat(m, lambda st: st["scor"] < 0.7)
    n = m.net["noduri"][eid]
    p1 = stationar(lat_n(n["lat"], 4), n["lon"], t0, 8)
    tm = datetime.fromisoformat(p1[-1]["t"])
    pm = mers(lat_n(n["lat"], 4), n["lon"], tm + timedelta(seconds=15), 6)
    pm += list(reversed([{"t": None, "lat": q["lat"], "lon": q["lon"]} for q in pm[:-1]]))
    tt = tm + timedelta(seconds=15)
    for k, q in enumerate(pm):
        q["t"] = (tt + timedelta(seconds=15 * k)).isoformat()
    p2 = stationar(lat_n(n["lat"], -6), n["lon"], datetime.fromisoformat(pm[-1]["t"]) + timedelta(seconds=15), 6)
    inainte = snap(m, D, eid)["scor"]
    tr = m.apply_event(ev_tura("TR-7", D, p1 + pm + p2))
    o = opriri(tr)
    delta = snap(m, D, eid)["scor"] - inainte
    verifica("două opriri la același stâlp: o validare și o `neclara` (numărat o singură dată)",
             [x["tip"] for x in o] == ["validare", "neclara"] and len([s for s in tr["schimbari"] if s["element_id"] == eid]) == 1,
             str([(x["tip"], x["durata_min"]) for x in o]))
    cal = 1 - 0.5 * o[0]["distanta_m"] / T["raza_validare_m"]
    verifica("două opriri la același stâlp: delta o singură dată (≈ 0,25 × 0,60 × calitate), nu dublu",
             abs(delta - 0.25 * 0.6 * cal) < 0.01 and "o singură dată" in o[1]["motiv"], f"delta {delta:.3f}")

    # --- regimul de scădere: tura la 90 de zile după start pornește de la scorul efectiv
    m = mk()
    eid = izolat(m, lambda st: st["scor"] == m.w["retea_start"]["scor_portocaliu"])
    n = m.net["noduri"][eid]
    D2 = "2026-10-30"
    efectiv = m.stare_efectiva(eid, D2)["scor"]
    tr = m.apply_event(ev_tura("TR-8", D2, stationar(lat_n(n["lat"], 4), n["lon"], t0.replace(month=10, day=30), 8)))
    o = opriri(tr)[0]
    verifica("scorul „înainte” e cel efectiv la data turei (nu cel stocat), „după” pornește de la el",
             abs(o["scor_inainte"] - efectiv) < 0.001 and efectiv < 0.5 and abs(o["scor_dupa"] - (efectiv + 0.15 * o["calitate"])) < 0.005
             and tr["schimbari"][0]["scor_inainte"] == o["scor_inainte"], f"efectiv {efectiv}, înainte {o['scor_inainte']}, după {o['scor_dupa']}")

    # --- GIS: fără plafon, sursa rămâne gis
    m = mk()
    kmz = next(e for e, v in m.istoric.items() if v[0]["origine"] == "retea_start" and not e.startswith("SIM-") and e in m.net["noduri"]
               and not e.endswith("-casa") and all(dist_m((m.net["noduri"][e]["lat"], m.net["noduri"][e]["lon"]), (o["lat"], o["lon"])) >= 35
                                                   for k, o in m.net["noduri"].items() if k != e))
    n = m.net["noduri"][kmz]
    tr = m.apply_event(ev_tura("TR-9", D, stationar(lat_n(n["lat"], 2), n["lon"], t0, 6)))
    s = snap(m, D, kmz)
    verifica("element GIS validat: sursa rămâne gis, ultima_validare_tracking setată, scorul nu scade",
             s["sursa_locatie"] == "gis" and s["ultima_validare_tracking"] == D and s["scor"] >= m.istoric[kmz][0]["scor"], f"{s['scor']}")


def teste_tura_generata():
    D = "2026-09-25"
    m = mk()
    scoruri = {k: v[-1]["scor"] for k, v in m.istoric.items() if v}
    tura = genereaza_tura(m.net, osm.strazi(), m.w, "mentenanta", "smoke-b2", D, scoruri=scoruri)
    e = ev_tura("TR-G", D, tura["puncte"], tura_id=tura["tura_id"])
    tr = m.apply_event(e)
    o = opriri(tr)
    plan_s = [x for x in tura["plan"] if x["tip_plan"] == "stalp"]
    plan_f = [x for x in tura["plan"] if x["tip_plan"] == "fara_stalp"]
    plan_c = [x for x in tura["plan"] if x["tip_plan"] == "scurta"]
    val = [x for x in o if x["tip"] == "validare"]
    pres = [x for x in o if x["tip"] == "stalp_presupus"]
    scurte = [x for x in o if x["tip"] == "scurta"]
    verifica("tură generată: câte o validare pentru fiecare oprire de stâlp din plan", len(val) == len(plan_s) and len(plan_s) >= 3,
             f"{len(val)} validări / {len(plan_s)} în plan")
    # stâlpul validat = cel mai apropiat stâlp de poziția din plan (poate fi altul decât cel ales, dacă doi stâlpi sunt la câțiva metri)
    cel_mai = []
    for x in plan_s:
        c = min(((dist_m((x["lat"], x["lon"]), (n["lat"], n["lon"])), n["id"]) for n in m.net["noduri"].values()
                 if not n["id"].endswith("-casa")))
        cel_mai.append(c[1])
    verifica("tură generată: stâlpii validați sunt cei din plan (sau cel mai apropiat, la egalitate de vecinătate)",
             {x["element_id"] for x in val} == set(cel_mai) and sum(x["element_id"] in {y["element_id"] for y in plan_s} for x in val) >= len(plan_s) - 1,
             str(sorted(x["element_id"] for x in val)) + " vs plan " + str(sorted(y["element_id"] for y in plan_s)))
    verifica("tură generată: exact un stâlp presupus, la locul `fara_stalp` (< 15 m de el)",
             len(pres) == 1 and len(plan_f) == 1 and dist_m((pres[0]["lat"], pres[0]["lon"]), (plan_f[0]["lat"], plan_f[0]["lon"])) < 15,
             str(pres and pres[0]["element_id"]))
    verifica("tură generată: opririle scurte apar ca `scurta` (câte detectează detectorul din plan), niciuna cu efect",
             len(scurte) >= 1 and len(scurte) <= len(plan_c) and all(not x.get("element_id") for x in scurte),
             f"{len(scurte)} scurte / {len(plan_c)} în plan")
    verifica("tură generată: nicio oprire neclară (tura e curată)", not [x for x in o if x["tip"] == "neclara"], str([x["tip"] for x in o]))
    verifica("tură generată: toți stâlpii validați cresc sau rămân (niciun scor nu scade față de „înainte”)",
             all(x["scor_dupa"] >= x["scor_inainte"] for x in val))
    verifica("tură generată: decizie scor_actualizat, detalii.tracking scris pe eveniment",
             tr["decizie"] == "scor_actualizat" and e["detalii"]["tracking"]["ignorate"] == len(scurte)
             and len(e["detalii"]["tracking"]["validari"]) == len(val) and len(e["detalii"]["tracking"]["presupuneri"]) == 1
             and len(e["detalii"]["tracking"]["opriri"]) == len(o), e["detalii"]["tracking"]["de_ce"])
    print("     ", m.jurnal[-1]["rezumat"])
    # nimic în afara zonei
    noi = [f for f in m.snapshot(D)["features"] if f["properties"]["element_id"].startswith("TRK-")]
    afara = [f for f in noi if f["geometry"]["type"] == "Point" and not zona_ok(f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0], m.net, m.w)["ok"]]
    verifica("niciun element TRK în afara zonei de 3 km", noi and not afara, f"{len(noi)} elemente TRK")
    # determinism
    m2 = mk()
    e2 = ev_tura("TR-G", D, tura["puncte"], tura_id=tura["tura_id"])
    tr2 = m2.apply_event(e2)
    verifica("determinism: aceeași tură în două modele = același StepTrace (pași, schimbări, decizie) și același snapshot",
             json.dumps([tr["pasi"], tr["schimbari"], tr["decizie"]], sort_keys=True, default=str)
             == json.dumps([tr2["pasi"], tr2["schimbari"], tr2["decizie"]], sort_keys=True, default=str)
             and json.dumps(m.snapshot(D), sort_keys=True) == json.dumps(m2.snapshot(D), sort_keys=True))
    # tură generată de altă echipă / seed, la alt moment: merge și ea; aceeași tură pe același model nu dublează
    snapA = json.dumps(m.snapshot(D), sort_keys=True)
    tr3 = m.apply_event(ev_tura("TR-G2", D, tura["puncte"], tura_id=tura["tura_id"]))
    verifica("aceeași tură generată aplicată a doua oară: fara_efect, snapshot identic", tr3["decizie"] == "fara_efect"
             and json.dumps(m.snapshot(D), sort_keys=True) == snapA)
    # a doua tură (alt seed) peste aceeași zonă nu strică modelul și scorurile rămân în [0, 1]
    t2 = genereaza_tura(m.net, osm.strazi(), m.w, "investitii", "smoke-b2-2", "2026-10-30", scoruri={k: v[-1]["scor"] for k, v in m.istoric.items() if v})
    tr4 = m.apply_event(ev_tura("TR-G3", "2026-10-30", t2["puncte"], tura_id=t2["tura_id"], echipa="investitii"))
    verifica("o a doua tură (alt seed, altă echipă) se aplică; scorurile rămân în [0, 1]",
             tr4["decizie"] in ("scor_actualizat", "predictie") and all(0 <= f["properties"]["scor"] <= 1 for f in m.snapshot("2026-10-30")["features"]),
             tr4["decizie"])
    snap_p = m.snapshot("2026-10-30")["features"]
    verifica("snapshot: `ultima_validare_tracking` apare doar pe elementele validate",
             any(f["properties"].get("ultima_validare_tracking") for f in snap_p)
             and all("ultima_validare_tracking" in f["properties"] for f in snap_p if f["properties"]["element_id"] in {x["element_id"] for x in val}))


def teste_fara_regresii():
    """Un raport obișnuit nu e atins de ramura nouă: pașii încep cu `extractie`."""
    m = mk()
    eid = next(e for e in m.net["noduri"] if e.startswith("SIM-"))
    n = m.net["noduri"][eid]
    e = {"event_id": "R-1", "echipa_sursa": "mentenanta", "tip": "verificare", "status": "executat", "data": "2026-09-01",
         "forma_sursa": "campuri", "incredere_extractie": 0.9, "text_original": "verificat", "tip_sursa_pondere": "tableta_coordonate",
         "referinta": {"coordonate": {"lat": n["lat"], "lon": n["lon"]}}, "detalii": {}}
    tr = m.apply_event(e)
    verifica("raport obișnuit: primul pas rămâne `extractie`, eticheta nu e `tracking`", tr["pasi"][0]["nume"] == "extractie"
             and m.jurnal[-1]["eticheta"] != "tracking" and m.timeline()[-1]["rezumat"].startswith("mentenanta:"))
    tr = m.apply_event({"event_id": "T-0", "echipa_sursa": "mentenanta", "tip": "tracking_tura", "status": "executat", "data": "2026-09-02",
                        "referinta": {}, "detalii": {"tura": {"tura_id": "TURA-GOALA", "puncte": []}}})
    verifica("tură fără puncte: fara_efect, fără excepție", tr["decizie"] == "fara_efect")


def main():
    teste_manuale()
    teste_tura_generata()
    teste_fara_regresii()
    ok, tot = sum(OK), len(OK)
    print(f"\nsmoke_tracking_motor: {ok}/{tot} OK")
    if ok != tot:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
