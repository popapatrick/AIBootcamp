"""Smoke test pentru API (etapa 7). Rulare: .venv/bin/python -m backend.api.smoke_api

Verifică fiecare endpoint pe date FICTIVE, în modul în care se află (stub / parțial / real).
"""
from fastapi.testclient import TestClient

from backend.api.main import app


def main() -> None:
    c = TestClient(app)
    h = c.get("/health").json()
    assert h["status"] == "ok", h
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

    assert c.post("/rapoarte", json={"text": "x", "sursa": "gresit"}).status_code == 422
    assert c.get("/ui/").status_code == 200
    print("OK: API")


if __name__ == "__main__":
    main()
