"""Smoke test pentru API (etapa 7). Rulare: .venv/bin/python -m backend.api.smoke_api

Verifică fiecare endpoint pe date FICTIVE, în modul în care se află (stub / parțial / real).
"""
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

    assert c.post("/rapoarte", json={"text": "x", "sursa": "gresit"}).status_code == 422
    assert c.get("/ui/").status_code == 200
    print("OK: API")


if __name__ == "__main__":
    main()
