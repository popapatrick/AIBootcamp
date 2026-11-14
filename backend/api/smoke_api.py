"""Smoke test pentru API (etapa 7). Rulare: .venv/bin/python -m backend.api.smoke_api

Verifică fiecare endpoint pe date FICTIVE, în modul în care se află (stub / parțial / real).
"""
import os

os.environ.setdefault("EXTRACT_CLI", "0")   # fără Claude headless real în teste (textele noi cad pe regex)

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api import sources
from backend.api.sources import ROOT


def main() -> None:
    c = TestClient(app)
    apply = sources.engine_func("apply_event")
    h = c.get("/health").json()
    assert h["status"] == "ok", h
    assert "ultima_actualizare" in h, h
    print("health:", h["mod"])

    ev = c.get("/evenimente").json()
    assert isinstance(ev, list), ev
    if not ev:   # motor real fără data/events/events.json (A nu a livrat încă): pornim de la azi
        ev = [{"data": c.get("/date").json()[-1]}]
    print("evenimente:", len(ev))

    fc = c.get("/retea").json()
    assert fc["type"] == "FeatureCollection" and fc["features"], "rețea goală"
    fc0 = c.get("/retea", params={"data": ev[0]["data"]}).json()
    print("retea:", len(fc["features"]), "elemente; la", ev[0]["data"], ":", len(fc0["features"]))

    eid = fc["features"][0]["properties"].get("element_id")
    el = c.get(f"/element/{eid}").json()
    assert el["istoric"], el
    assert c.get("/element/NU-EXISTA").status_code == 404
    print("element:", eid, "istoric", len(el["istoric"]))

    # Scenariul 2: cablu înlocuit, cu ID -> potrivit
    t = c.post("/rapoarte", json={"text": "Am înlocuit cablul pe tronsonul A-T-002 cu TYIR 3x70+54,6 OL-Al.",
                                  "sursa": "investitii", "data": "2026-10-15"}).json()
    nume = [p["nume"] for p in t["pasi"]]
    assert nume[0] == "extractie" and "scor" in nume, nume
    pot = next(p for p in t["pasi"] if p["nume"] == "potrivire")["rezultat"]
    print("raport A-T-002:", pot["status"], t["modificari"][0]["nivel"], t["modificari"][0]["scor"])

    # Scenariul 1: stâlp lipsă, doar coordonate -> absent din model, apare pe hartă
    t = c.post("/rapoarte", json={"text": "Stâlp nou care nu apare în GIS, coordonate 44.2849717, 26.0601908.",
                                  "sursa": "mentenanta", "data": "2026-10-20"}).json()
    pot = next(p for p in t["pasi"] if p["nume"] == "potrivire")["rezultat"]
    nid = t["modificari"][0]["element_id"]
    print("raport nod lipsă:", pot["status"], nid, t["modificari"][0]["nivel"], t["modificari"][0]["scor"])
    ids = {f["properties"].get("element_id") for f in c.get("/retea").json()["features"]}
    if t["mod"]["motor"] != "real":
        assert nid in ids, "raportul live nu apare pe hartă"
        assert c.get(f"/element/{nid}").status_code == 200
    assert any(e["event_id"] == t["event_id"] for e in c.get("/evenimente").json())

    # --- sesiunea 2 (C1)
    assert isinstance(t["schimbari"], list), "schimbari lipsește din StepTrace"
    if t["mod"]["motor"] == "real":   # B3 legat real, nu []/null
        assert t["schimbari"] and t["schimbari"][0]["ce"] and t["ultima_actualizare"], t
        assert c.get("/retea").json()["ultima_actualizare"] and c.get("/health").json()["ultima_actualizare"]
    assert "ultima_actualizare" in t and "ultima_actualizare" in c.get("/retea").json()
    loc, tr = {"lat": 44.285, "lon": 26.061}, [{"t": "2026-10-20T10:00:00", "lat": 44.285, "lon": 26.061}]
    t2 = c.post("/rapoarte", json={"text": "Cerere racordare casă nouă.", "sursa": "racordari",
                                   "data": "2026-10-21", "locatie": loc, "trace": tr}).json()
    det = next(p for p in t2["pasi"] if p["nume"] == "extractie")["rezultat"]["detalii"]
    assert det["locatie"] == loc and det["centru"] == loc and det["trace"] == tr, det
    assert c.post("/rapoarte", json={"text": "x", "sursa": "mentenanta", "locatie": {"lat": "a"}}).status_code == 422

    # mutare_fire -> potrivire.status == "zona" (Event direct: extracția stub nu știe tipul mutare_fire)
    if apply:
        tz = apply({"event_id": "EV-SMOKE-MF", "echipa_sursa": "mentenanta", "tip": "mutare_fire", "status": "semnalat",
                    "data": "2026-10-23", "forma_sursa": "text_liber", "incredere_extractie": 0.9,
                    "text_original": "smoke mutare fire", "campuri_lipsa": [], "referinta": {},
                    "detalii": {"centru": {"lat": 44.2830448, "lon": 26.0636533}, "motiv_mutare": "sens_giratoriu"}})
        assert next(p for p in tz["pasi"] if p["nume"] == "potrivire")["rezultat"]["status"] == "zona", tz["pasi"]

    # --- metoda_cod (ai_cache | ai_api | regex), fără AI nou: cache hit sau regex
    import random
    xc = h.get("extractie_cod")
    assert xc in ("ai_cache", "regex"), h   # niciodată ai_api în teste (fără cheie, EXTRACT_ALLOW_API oprit)
    if xc == "ai_cache":
        ex0 = c.get("/exemple", params={"sursa": "mentenanta"}).json()[0]
        r0 = c.post("/rapoarte", json={"text": ex0["text"], "sursa": "mentenanta", "data": ex0.get("data")}).json()
        assert r0["pasi"][0]["metoda_cod"] == "ai_cache", r0["pasi"][0]
    rn = c.post("/rapoarte", json={"text": f"Text nou fără cache {random.random()}", "sursa": "mentenanta",
                                   "data": "2026-10-25"}).json()
    assert rn["pasi"][0]["metoda_cod"] == "regex", rn["pasi"][0]
    if xc == "ai_cache":
        assert "fără cache" in rn["pasi"][0]["motiv"], rn["pasi"][0]
    print("metoda_cod:", xc, "-> text nou:", rn["pasi"][0]["metoda_cod"])

    # textele butoanelor UI (C5-C7) dau tipul corect și fără AI (regex)
    def ext(t):
        return next(p for p in t["pasi"] if p["nume"] == "extractie")["rezultat"]
    lr = {"lat": 44.2850305, "lon": 26.0595998}
    tr1 = next(x for x in c.get("/trasee-demo").json() if x["id"] == "trace-1")
    tb = c.post("/rapoarte", json={"text": "Cerere racordare: client nou, casă la coord 44.2850305, 26.0595998",
                                   "sursa": "apel_client", "data": "2026-10-28", "locatie": lr}).json()
    assert ext(tb)["tip"] == "cerere_racordare" and ext(tb)["referinta"]["coordonate"] == lr, ext(tb)
    if apply:
        assert any(p["nume"] == "predictie" for p in tb["pasi"]) and \
            any(m.get("predictie", {}) and m["predictie"].get("metoda") == "lant_racordare" for m in tb["modificari"]), tb["pasi"]
    cf = {"lat": 44.2830448, "lon": 26.0636533}
    tf = c.post("/rapoarte", json={"text": "Fire mutate: sens giratoriu, centru 44.2830448, 26.0636533. "
                                   "S-au mutat firele aeriene.", "sursa": "mentenanta", "data": "2026-10-29",
                                   "locatie": cf}).json()
    assert ext(tf)["tip"] == "mutare_fire" and ext(tf)["detalii"]["centru"] == cf \
        and ext(tf)["detalii"]["motiv_mutare"] == "sens_giratoriu", ext(tf)
    if apply:
        assert next(p for p in tf["pasi"] if p["nume"] == "potrivire")["rezultat"]["status"] == "zona", tf["pasi"]
    tt = c.post("/rapoarte", json={"text": f"Raport tabletă: stâlp nou necartat pe {tr1['adresa']}, lucrare executată. Am verificat și stâlpii din jur.",
                                   "sursa": "mentenanta", "data": tr1["data"], "trace": tr1["puncte"]}).json()
    assert ext(tt)["tip"] == "nod_lipsa", ext(tt)
    if apply:
        assert any(p["nume"] == "trace" for p in tt["pasi"]) and \
            any(str(m["element_id"]).startswith("NOU-") for m in tt["modificari"]), tt["pasi"]
    sc = lambda t: sorted({round(m["scor"], 3) for m in t["modificari"]})[-3:]
    print("butoane (regex?):", xc, "racordare", sc(tb), "zona", len(tf["modificari"]), "trace", sc(tt))

    for s_ in ("mentenanta", "investitii", "racordari", "apel_client"):
        r = c.get("/exemple", params={"sursa": s_})
        assert r.status_code == 200 and isinstance(r.json(), list), r.text
    assert c.get("/exemple", params={"sursa": "gresit"}).status_code == 422
    assert isinstance(c.get("/trasee-demo").json(), list)

    # decizia omului (B4): predicția se pregătește direct în motor (Event nod_lipsa), independent de extracție
    if apply:
        pe = {"event_id": "EV-SMOKE-PRED", "echipa_sursa": "apel_client", "tip": "nod_lipsa", "status": "semnalat",
              "data": "2026-10-22", "forma_sursa": "text_liber", "tip_sursa_pondere": "apel_client",
              "incredere_extractie": 0.6, "text_original": "smoke: lipsește un stâlp", "campuri_lipsa": [],
              "referinta": {"coordonate": {"lat": 44.2851, "lon": 26.0612}}, "detalii": {}}
        pt = apply(pe)
        pid = next((m["element_id"] for m in pt["modificari"] if m["nivel"] == "predictie"), None)
        assert pid, "nicio predicție creată: " + str(pt["modificari"])
        r = c.post(f"/predictii/{pid}/decizie", json={"decizie": "accepta", "motiv": "văzut în teren"})
        assert r.status_code == 200, r.text
        assert r.json()["decizie"] == "aplicat" and r.json()["schimbari"], r.text
        assert c.post(f"/predictii/{pid}/decizie", json={"decizie": "respinge"}).status_code == 409
        assert c.post("/predictii/NU-EXISTA-X/decizie", json={"decizie": "accepta"}).status_code == 404
        assert c.post("/predictii/%20/decizie", json={"decizie": "accepta"}).status_code in (400, 404)
        print("decizie: 200 / 409 / 404 pe", pid)
    assert c.post("/predictii/PRED-X/decizie", json={"decizie": "poate"}).status_code == 422

    r = c.get("/evenimente", params={"scenariu": "extrem"})
    if (ROOT / "data" / "events" / "events.extreme.json").is_file():
        assert r.status_code == 200 and len(r.json()) > len(c.get("/evenimente").json()), r.text
        assert c.get("/retea", params={"scenariu": "extrem"}).status_code == 200
        if apply:   # B6: eticheta pe timeline, verificat_recent / scos_din_uz în snapshot
            et = {e.get("eticheta") for e in r.json()}
            assert {"val_apeluri", "demontat"} <= et and all("tip" in e for e in r.json()), et
            fe = c.get("/retea", params={"scenariu": "extrem"}).json()["features"]
            assert all("verificat_recent" in f["properties"] for f in fe)
            assert any(f["properties"]["nivel"] == "scos_din_uz" for f in fe), "niciun scos_din_uz în extrem"
    else:
        assert r.status_code == 404 and "extrem" in r.json()["detail"], r.text
        assert c.get("/retea", params={"scenariu": "extrem"}).status_code == 404
    print("scenariu extrem:", r.status_code, len(r.json()) if r.status_code == 200 else "")
    assert c.get("/evenimente", params={"scenariu": "altul"}).status_code == 422

    # --- locația operatorului (simulată) din textul lui
    q = "casă pe Strada Liviu Rebreanu"
    lo = c.get("/locatie-operator-demo", params={"text": q})
    assert lo.status_code == 200, lo.text
    lo = lo.json()
    assert lo["simulata"] is True and lo["strada"] == "Strada Liviu Rebreanu" and lo["precizie_m"] > 0, lo
    assert lo["indicii"] == [{"tip": "strada", "valoare": "Strada Liviu Rebreanu", "gasit": True}] and lo["zona"], lo
    assert c.get("/locatie-operator-demo", params={"adresa": q}).json() == lo, "alias adresa + determinist"
    li = c.get("/locatie-operator-demo", params={"text": "Strada Liviu Rebreanu colț cu strada Ion Luca Caragiale"}).json()
    assert any(i["tip"] == "intersectie" and i["gasit"] for i in li["indicii"]) and li["precizie_m"] < lo["precizie_m"], li
    lc = c.get("/locatie-operator-demo", params={"text": "strada Foo din cartierul 1 Decembrie"}).json()
    assert [(i["tip"], i["gasit"]) for i in lc["indicii"]] == [("strada", False), ("cartier", True)] and lc["strada"] is None, lc
    for bad in ({"text": "undeva pe lângă școală"}, {"text": "strada Inexistenta"}, {}):
        e = c.get("/locatie-operator-demo", params=bad)
        assert e.status_code == 422 and e.json()["detail"]["mesaj"], e.text
    assert c.get("/locatie-operator-demo", params={"text": "strada Inexistenta"}).json()["detail"]["indicii"] == \
        [{"tip": "strada", "valoare": "Strada Inexistenta", "gasit": False}]
    assert c.post("/rapoarte", json={"text": "x", "sursa": "mentenanta",
                                     "locatie_operator": {**{k: lo[k] for k in ("lat", "lon")}, "simulata": False}}).status_code == 422
    txt = "Cerere racordare: client nou, casă pe Strada Liviu Rebreanu"
    lop = {k: lo[k] for k in ("lat", "lon", "precizie_m", "simulata")}
    to = c.post("/rapoarte", json={"text": txt, "sursa": "apel_client", "data": "2026-10-30", "locatie_operator": lop}).json()
    eo = ext(to)
    assert eo["tip"] == "cerere_racordare" and "referinta.coordonate" in eo["campuri_lipsa"] and not eo["referinta"]["coordonate"], eo
    assert eo["detalii"]["locatie_operator"] == lop, eo["detalii"]
    if apply:
        po = next(p for p in to["pasi"] if p["nume"] == "predictie")["rezultat"]
        assert po["metoda"] == "lant_racordare" and po["sursa_locatie"] == "operator_simulat", po
        assert next(p for p in to["pasi"] if p["nume"] == "potrivire")["rezultat"]["sursa_locatie"] == "operator_simulat"
        assert any(m["nivel"] == "predictie" for m in to["modificari"]) and to["decizie"] == "predictie", to["pasi"][-1]
        assert "SIMULATĂ" in to["pasi"][-1]["motive"][0], to["pasi"][-1]["motive"]
        tcl = c.post("/rapoarte", json={"text": txt, "sursa": "apel_client", "data": "2026-10-31", "locatie": lop}).json()
        assert to["pasi"][-1]["rezultat"]["scor_propunere"] < tcl["pasi"][-1]["rezultat"]["scor_propunere"], "operator < clic"
    print("locatie operator:", lo["lat"], lo["lon"], "±", lo["precizie_m"], "m", to["modificari"][0]["nivel"] if to["modificari"] else "")

    # --- sesiunea 3 (C1): trace_params, geocodare, zona, /reguli, /geocodeaza
    tp = {"puncte": 60, "zgomot_m": 5, "durata_oprire_min": 12, "acoperire": 0.9, "decalaj_m": 0}
    t3 = c.post("/rapoarte", json={"text": "Stâlp nou care nu apare în GIS, coordonate 44.2849717, 26.0601908.",
                                   "sursa": "mentenanta", "data": "2026-10-26", "trace_params": tp}).json()
    assert ext(t3)["detalii"]["trace_params"] == tp, ext(t3)["detalii"]
    assert c.post("/rapoarte", json={"text": "x", "sursa": "mentenanta", "trace_params": {"puncte": "a"}}).status_code == 422
    assert "trace_params" not in ext(rn).get("detalii", {}), "trace_params apare fără să fie cerut"
    from backend.api import pipeline as _pl
    geo = {"lat": 44.28, "lon": 26.06, "precizie_m": 25, "metoda": "osm_cache", "acuratete": 0.55, "motiv": "smoke"}
    o = {"pasi": [{"nume": "extractie", "rezultat": {"detalii": {"geocodare": geo}}}, {"nume": "scor"}]}
    _pl._pas_geocodare({"detalii": {}}, o)
    assert [p["nume"] for p in o["pasi"]] == ["extractie", "geocodare", "scor"] and o["pasi"][1]["rezultat"] == geo \
        and o["pasi"][1]["incredere"] == 0.55, o
    o = {"pasi": [{"nume": "extractie", "rezultat": {"detalii": {}}}]}
    _pl._pas_geocodare({"detalii": {}}, o)
    assert [p["nume"] for p in o["pasi"]] == ["extractie"], "fără geocodare în Event nu se inventează pasul"
    z = c.get("/retea").json()["zona"]
    assert set(z) == {"centru", "raza_m"} and z["raza_m"] == 3000 and 44 < z["centru"]["lat"] < 45 \
        and 26 < z["centru"]["lon"] < 27, z
    rg = c.get("/reguli")
    assert rg.status_code == 200 and rg.json()["zona"]["raza_max_m"] == 3000 and "praguri" in rg.json(), rg.text
    g = c.get("/geocodeaza", params={"adresa": "Strada Liviu Rebreanu 12"})
    if sources.geocodeaza_func():
        assert g.status_code == 200 and "status" in g.json(), g.text
    else:
        assert g.status_code == 501 and "B2/A1" in g.json()["detail"], g.text
    assert c.get("/geocodeaza").status_code == 422
    print("sesiunea 3: zona", z["raza_m"], "m, /reguli ok, /geocodeaza", g.status_code)

    assert c.post("/rapoarte", json={"text": "x", "sursa": "gresit"}).status_code == 422
    assert c.get("/ui/").status_code == 200
    print("OK: API")


if __name__ == "__main__":
    main()
