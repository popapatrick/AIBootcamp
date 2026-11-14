"""Verificări pentru regulile noi din sesiunea 2 (mutare_fire, activ_demontat, val de apeluri, cerere_racordare,
locația din trace, acceptare parțială). Rulează: python -m backend.engine.smoke_sesiune2. Date FICTIVE."""
from __future__ import annotations

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

    assert all(OK), "unele verificări au eșuat"
    print(f"OK: {len(OK)} verificări")


if __name__ == "__main__":
    main()
