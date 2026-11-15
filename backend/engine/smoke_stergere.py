"""Verificări pentru ștergerea de către om (etapa 34): evenimentul `stergere_om`.

Rulează: EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_stergere. Date FICTIVE.
Acoperă (pe scenariul real `engine.get_model()` și pe cazuri construite): lanț de racordare, element aplicat din raport
(scos din `net`, nu mai e potrivit), stâlp presupus TRK-* cu legătura lui, pin VER-*, refuzuri (GIS, SIM-*, inexistent,
a doua ștergere, element retras de „Respinge”), „Respinge” neschimbat (penalizare doar la el), `stergibil`, grup fără fire
în aer, scorurile altor elemente neschimbate, determinism, eticheta `stergere`, distribuția culorilor.
"""
from __future__ import annotations

import json
from datetime import datetime

from backend.engine import engine
from backend.engine.model import GridModel
from backend.engine.smoke_tracking_motor import ev_tura, loc_fara_stalp, mk, stationar

OK: list[bool] = []
DEL = "2026-11-20"       # după ultimul eveniment al scenariului (2026-11-14)
INAINTE = "2026-11-14"


def verifica(nume, cond, detaliu=""):
    OK.append(bool(cond))
    print(("OK  " if cond else "FAIL"), nume, detaliu)


def stergere(i: str, tinta: str, motiv: str | None = None, data: str = DEL) -> dict:
    """Evenimentul `stergere_om`, exact cum îl construiește API-ul (fără `status`/`forma_sursa`)."""
    return {"event_id": i, "tip": "stergere_om", "echipa_sursa": "om_teren", "data": data,
            "detalii": {"tinta_id": tinta, **({"motiv": motiv} if motiv else {})}}


def ids(m: GridModel, data: str) -> set[str]:
    return {f["properties"]["element_id"] for f in m.snapshot(data)["features"]}


def prop(m: GridModel, data: str, eid: str) -> dict | None:
    return next((f["properties"] for f in m.snapshot(data)["features"] if f["properties"]["element_id"] == eid), None)


def scoruri(m: GridModel, data: str, fara: set[str]) -> dict[str, float]:
    return {f["properties"]["element_id"]: f["properties"]["scor"] for f in m.snapshot(data)["features"]
            if f["properties"]["element_id"] not in fara}


def model_real() -> GridModel:
    engine.reset()
    return engine.get_model()


def scenariu(m: GridModel):
    # --- lanț de racordare (EV4-017: casa prezisă + legătura)
    pas = scoruri(m, DEL, set())
    pen0 = dict(m.penalizare_metoda)
    grup_asteptat = {"NOU-EV4-017-casa", "NOU-EV4-017-L1"}
    verifica("EV4-017: ambele elemente sunt predicții ștergibile",
             grup_asteptat <= set(m.predictii) and all(prop(m, INAINTE, g)["stergibil"] for g in grup_asteptat))
    verifica("`stergere_n` din snapshot = mărimea grupului (2), 0 pe GIS",
             prop(m, INAINTE, "NOU-EV4-017-L1")["stergere_n"] == 2 and prop(m, INAINTE, "A-T-001")["stergere_n"] == 0)
    tr = m.apply_event(stergere("DEL-1", "NOU-EV4-017-L1", "nu există casa în teren"))
    sch = {s["element_id"]: s for s in tr["schimbari"]}
    verifica("lanț: decizie `sters`, grupul = casa + legătura, schimbari[].ce = sters",
             tr["decizie"] == "sters" and set(sch) == grup_asteptat and all(s["ce"] == "sters" for s in sch.values())
             and tr["stergere"]["n"] == 2 and "eroare" not in tr, str(tr["stergere"]))
    verifica("lanț: dispar din snapshot la data ștergerii și după", not (grup_asteptat & ids(m, DEL)) and not (grup_asteptat & ids(m, "2026-12-31")))
    verifica("lanț: apar la data anterioară (cu geometrie), cu scorul de dinainte",
             all(prop(m, INAINTE, g) and prop(m, INAINTE, g)["nivel"] == "predictie" for g in grup_asteptat))
    verifica("lanț: scoase din `predictii`, geometria rămâne în `retrase`",
             not (grup_asteptat & set(m.predictii)) and all(m.retrase[g]["geometrie"] for g in grup_asteptat))
    mot = prop(m, INAINTE, "NOU-EV4-017-casa")["motive"][0]["text"]
    verifica("lanț: motivul „Șters de om: <motiv>” e primul în „De ce?” (stări noi), vizibil în StepTrace",
             tr["modificari"][0]["motive"][0]["text"].startswith("Șters de om: nu există casa în teren")
             and "Cerere de racordare" in mot, tr["modificari"][0]["motive"][0]["text"][:70])
    verifica("lanț: ElementState din StepTrace are sters/sters_data/sters_motiv și stergibil=false",
             tr["modificari"][0]["sters"] is True and tr["modificari"][0]["sters_data"] == DEL
             and tr["modificari"][0]["sters_motiv"] == "nu există casa în teren" and tr["modificari"][0]["stergibil"] is False)
    j, t = m.jurnal[-1], m.timeline()[-1]
    verifica("lanț: eticheta timeline `stergere`, rezumat „Șters de om: 2 elemente (...)”, schimbari + pasi în timeline",
             t["eticheta"] == "stergere" and t["decizie"] == "sters" and t["rezumat"].startswith("Șters de om: 2 elemente (")
             and "NOU-EV4-017-L1" in t["rezumat"] and len(t["schimbari"]) == 2 and t["pasi"], t["rezumat"])
    verifica("lanț: nicio penalizare de metodă, scorurile celorlalte elemente neschimbate",
             m.penalizare_metoda == pen0 and scoruri(m, DEL, grup_asteptat) == {k: v for k, v in pas.items() if k not in grup_asteptat})
    t2 = m.apply_event(stergere("DEL-1b", "NOU-EV4-017-casa"))
    verifica("a doua ștergere: refuz deja_sters, neaplicat",
             t2["decizie"] == "neaplicat" and t2["eroare"]["cod"] == "deja_sters", str(t2.get("eroare")))

    # --- lanț lung: ștergi un capăt, stâlpii izolați cad odată cu legătura (niciun fir în aer)
    pred_inainte = set(m.predictii)
    lant = sorted(k for k in pred_inainte if k.startswith("NOU-EV4-012-"))
    verifica("EV4-012: lanț cu mai mulți stâlpi (casa + S1..S4 + L1..L5)", len(lant) == 10, str(lant))
    tr = m.apply_event(stergere("DEL-2", "NOU-EV4-012-casa", "lanț greșit"))
    g = set(tr["stergere"]["elemente"])
    verifica("stâlp (casa): se șterge cu legăturile lui, fără alt stâlp rămas izolat",
             {"NOU-EV4-012-casa"} < g and all(x in lant for x in g) and not any(
                 "capete" in m.predictii.get(x, {}) and any(c in g for c in m.predictii[x]["capete"]) for x in m.predictii if x not in g),
             str(sorted(g)))
    restul = [x for x in lant if x not in g and "capete" in m.predictii[x]]
    verifica("grup: nicio legătură rămasă cu un capăt șters (fără fire în aer)",
             all(c not in g for x in restul for c in m.predictii[x]["capete"]), str(restul))

    # --- element aplicat din raport (NOU-EV4-023): dispare, nu mai e în net, un raport ulterior nu se mai potrivește cu el
    eid = "NOU-EV4-023"
    n = m.net["noduri"][eid]
    el_lat, el_lon = n["lat"], n["lon"]
    verifica("NOU-EV4-023: element aplicat (în net, origine generat_model, fără t0), ștergibil",
             prop(m, INAINTE, eid)["origine"] == "generat_model" and not prop(m, INAINTE, eid)["t0"] and prop(m, INAINTE, eid)["stergibil"])
    leg = [t for t, v in m.net["tronsoane"].items() if eid in v["capete"]]
    rap = lambda i: {"event_id": i, "echipa_sursa": "mentenanta", "tip": "verificare", "status": "executat", "data": "2026-11-21",
                     "forma_sursa": "campuri", "tip_sursa_pondere": "tableta_coordonate", "incredere_extractie": 0.9,
                     "text_original": "test", "referinta": {"coordonate": {"lat": el_lat, "lon": el_lon}}, "detalii": {}}
    tr0 = m.apply_event(rap("R-INAINTE"))
    pm0 = next(p for p in tr0["pasi"] if p["nume"] == "potrivire")["rezultat"]
    verifica("înainte de ștergere un raport pe aceeași poziție se potrivește cu el", pm0["element_id"] == eid, str(pm0["element_id"]))
    tr = m.apply_event(stergere("DEL-3", eid, "stâlp montat greșit în raport", data="2026-11-22"))
    gr = set(tr["stergere"]["elemente"])
    verifica("aplicat: șters odată cu legăturile lui aplicate; scos din net (noduri și tronsoane)",
             eid in gr and set(leg) <= gr and eid not in m.net["noduri"] and not (gr & set(m.net["tronsoane"])), str(sorted(gr)))
    verifica("aplicat: dispare din snapshot la 2026-11-22, rămâne vizibil la 2026-11-21 cu forma lui (clasa, geometrie)",
             eid not in ids(m, "2026-11-22") and prop(m, "2026-11-21", eid) and prop(m, "2026-11-21", eid)["clasa"] == "casa"
             and prop(m, "2026-11-21", eid).get("stergibil") is False)
    pt = [f for f in m.snapshot("2026-11-21")["features"] if f["properties"]["element_id"] == eid][0]["geometry"]
    verifica("aplicat: geometria din istoric neschimbată", pt["coordinates"] == [el_lon, el_lat])
    tr1 = m.apply_event({**rap("R-DUPA"), "data": "2026-11-23"})
    pm1 = next(p for p in tr1["pasi"] if p["nume"] == "potrivire")["rezultat"]
    verifica("după ștergere un raport pe aceeași poziție NU se mai potrivește cu el",
             pm1.get("element_id") != eid and all(c["element_id"] != eid for c in pm1.get("candidati", [])), str(pm1.get("element_id")))

    # --- pin VER-*
    pin = next(iter(m.pinuri))
    verifica("pin VER-*: ștergibil în snapshot", prop(m, INAINTE, pin)["stergibil"] is True, pin)
    tr = m.apply_event(stergere("DEL-4", pin, "pin inutil", data="2026-11-24"))
    verifica("pin: șters (scos din `pinuri`, dispare după dată, apare înainte)",
             tr["decizie"] == "sters" and pin not in m.pinuri and pin not in ids(m, "2026-11-24") and pin in ids(m, INAINTE)
             and tr["schimbari"][0]["ce"] == "sters" and tr["stergere"]["n"] == 1)

    # --- refuzuri: GIS, SIM-*, inexistent
    gis = next(k for k, s in m.istoric.items() if s[-1].get("origine") == "retea_start" and k in m.net["noduri"])
    sim = next(k for k in m.net["noduri"] if k.startswith("SIM-"))
    tronson_gis = next(iter(t for t, s in m.istoric.items() if s[-1].get("origine") == "retea_start" and t in m.net["tronsoane"]))
    verifica("`stergibil` false pe GIS (nod și tronson) și pe SIM-*",
             all(prop(m, INAINTE, x)["stergibil"] is False for x in (gis, sim, tronson_gis)), f"{gis} {tronson_gis} {sim}")
    n_net = (len(m.net["noduri"]), len(m.net["tronsoane"]))
    for i, (x, cod) in enumerate([(gis, "nu_se_sterge_retea_start"), (tronson_gis, "nu_se_sterge_retea_start"),
                                  (sim, "nu_se_sterge_retea_start"), ("NU-EXISTA-999", "necunoscut"), ("", "necunoscut")]):
        t = m.apply_event(stergere(f"DEL-R{i}", x, data="2026-11-25"))
        verifica(f"refuz «{x or '(gol)'}»: neaplicat, eroare.cod = {cod}, nimic modificat",
                 t["decizie"] == "neaplicat" and t["eroare"]["cod"] == cod and t["modificari"] == []
                 and (len(m.net["noduri"]), len(m.net["tronsoane"])) == n_net and (not x or x in ids(m, "2026-11-25") or x == "NU-EXISTA-999"),
                 str(t.get("eroare")))
    verifica("refuz: eticheta tot `stergere`, rezumat „Ștergere neaplicată”",
             m.timeline()[-1]["eticheta"] == "stergere" and m.timeline()[-1]["rezumat"].startswith("Ștergere neaplicată"))

    # --- „Respinge” existent: penalizare doar la el; un element respins nu se mai șterge (deja_sters, mesaj „retras”)
    pr = next(k for k in sorted(m.predictii) if k.startswith("NOU-EV4-006-S1"))
    pen = dict(m.penalizare_metoda)
    d = {"event_id": "RESP-1", "tip": "verificare", "echipa_sursa": "om_teren", "status": "executat", "data": "2026-11-26",
         "tip_sursa_pondere": "om_teren", "incredere_extractie": 1.0, "text_original": "respins", "forma_sursa": "campuri",
         "referinta": {}, "detalii": {"decizie": {"tinta_id": pr, "decizie": "respinge"}}}
    tr = m.apply_event(d)
    verifica("Respinge: neschimbat (decizie `respins`, ce = retras, penalizarea metodei crește)",
             tr["decizie"] == "respins" and all(s["ce"] == "retras" for s in tr["schimbari"]) and m.penalizare_metoda != pen,
             f"{pen} -> {m.penalizare_metoda}")
    t = m.apply_event(stergere("DEL-R9", pr, data="2026-11-27"))
    verifica("element respins: ștergere = deja_sters (mesaj „retras”)",
             t["eroare"]["cod"] == "deja_sters" and "retras" in t["eroare"]["mesaj"], t["eroare"]["mesaj"])
    pen2 = dict(m.penalizare_metoda)
    m.apply_event(stergere("DEL-6", "NOU-EV4-038-L1", data="2026-11-28"))
    verifica("ștergerea NU penalizează metoda (spre deosebire de Respinge)", m.penalizare_metoda == pen2)

    # --- legătură: stâlpii prezisi rămași fără alte legături cad cu ea; stergibil pe NOU/PLAN/MUT
    for pref in ("NOU-EV4-0", "PLAN-", "MUT-"):
        e = next((k for k in list(ids(m, INAINTE)) if k.startswith(pref) and prop(m, INAINTE, k)["origine"] == "generat_model"
                  and not prop(m, INAINTE, k)["t0"]), None)
        verifica(f"`stergibil` true pe {pref}* ({e})", e and prop(m, INAINTE, e)["stergibil"] is True)
    return m


def tracking():
    m = mk()
    D = "2026-08-01"
    la, lo = loc_fara_stalp(m)
    m.apply_event(ev_tura("TR-3", D, stationar(la, lo, datetime.fromisoformat(f"{D}T08:00:00"), 15)))
    verifica("TRK: stâlp presupus + legătura -L există ca predicții ștergibile",
             "TRK-TR-3-1" in m.predictii and "TRK-TR-3-1-L" in m.predictii and prop(m, D, "TRK-TR-3-1")["stergibil"] is True)
    tr = m.apply_event(stergere("DEL-T", "TRK-TR-3-1", "oprire la un colț, nu stâlp", data="2026-08-05"))
    verifica("TRK: dispare cu legătura lui TRK-…-L (grup de 2), apare la data anterioară",
             set(tr["stergere"]["elemente"]) == {"TRK-TR-3-1", "TRK-TR-3-1-L"} and not ({"TRK-TR-3-1", "TRK-TR-3-1-L"} & ids(m, "2026-08-05"))
             and {"TRK-TR-3-1", "TRK-TR-3-1-L"} <= ids(m, D) and "TRK-TR-3-1" not in m.predictii, str(tr["stergere"]))
    # legătura (nu stâlpul) ca țintă: stâlpul rămas fără alte legături cade odată cu ea
    m2 = mk()
    m2.apply_event(ev_tura("TR-3", D, stationar(la, lo, datetime.fromisoformat(f"{D}T08:00:00"), 15)))
    tr = m2.apply_event(stergere("DEL-T2", "TRK-TR-3-1-L", data="2026-08-05"))
    verifica("legătura ca țintă: stâlpul TRK rămas fără alte legături se șterge cu ea; capătul existent (GIS/SIM) rămâne",
             set(tr["stergere"]["elemente"]) == {"TRK-TR-3-1", "TRK-TR-3-1-L"}
             and len(ids(m2, "2026-08-05")) == len(ids(m2, D)) - 2)
    # element de start la capătul legăturii nu se atinge
    cap = m.retrase["TRK-TR-3-1-L"]["capete"][0]
    verifica("capătul de start al legăturii (stâlp existent) rămâne în snapshot și în net", cap in ids(m, "2026-08-05") and cap in m.net["noduri"], cap)


def determinism():
    def ruleaza():
        m = model_real()
        out = [m.apply_event(stergere("DEL-D1", "NOU-EV4-012-casa", "x")), m.apply_event(stergere("DEL-D2", "NOU-EV4-023")),
               m.apply_event(stergere("DEL-D3", next(iter(m.pinuri))))]
        return json.dumps([out, m.snapshot(DEL), m.snapshot(INAINTE), m.timeline()[-3:]], sort_keys=True, ensure_ascii=False)
    verifica("determinism: două rulări identice dau exact aceleași StepTrace, snapshot-uri și timeline", ruleaza() == ruleaza())


def distributie(m: GridModel):
    """Elementele șterse nu intră în distribuția pe benzi (`verifica_reglaje.distributie_model`): aceeași regulă ca la „Respinge”."""
    from backend.engine.verifica_reglaje import distributie_model

    def total(d):
        proc, _, pred = distributie_model(m, d)
        n_net = len([f for f in m.snapshot(d)["features"] if f["properties"]["element_id"] in m._elemente()
                     and f["properties"]["nivel"] not in ("predictie", "scos_din_uz")])
        return n_net + pred["n"] + pred["scoase_din_uz"], proc, pred
    t0, _, _ = total(INAINTE)
    t1, proc, pred = total("2026-12-31")
    sters = [k for k, s in m.istoric.items() if s[-1].get("sters")]
    retrase_total = [k for k, s in m.istoric.items() if s[-1].get("retras")]
    verifica("distribuție: elementele șterse nu sunt numărate (nici în rețea, nici în predicții); history intact",
             sters and not any(k in ids(m, "2026-12-31") for k in sters) and all(k in ids(m, INAINTE) for k in sters)
             and t0 - t1 == len(retrase_total) and pred["n"] == sum(pred[b] for b in ("verde", "galben", "portocaliu", "rosu"))
             and abs(sum(proc.values()) - 100) < 0.5, f"{len(sters)} șterse (+{len(retrase_total) - len(sters)} respinse), total {t0} -> {t1}")


def main():
    m = model_real()
    # modelul dinaintea ștergerilor: referința pentru distribuție (scenariul în sine nu are ștergeri)
    verifica("scenariul real nu conține ștergeri", not any(s[-1].get("sters") for s in m.istoric.values())
             and all(j["eticheta"] != "stergere" for j in m.jurnal))
    scenariu(m)
    distributie(m)
    tracking()
    determinism()
    engine.reset()
    ok, tot = sum(OK), len(OK)
    print(f"\nsmoke_stergere: {ok}/{tot} OK")
    if ok != tot:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
