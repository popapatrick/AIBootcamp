"""Smoke test etapa 4: python -m backend.engine.smoke_match

Evenimente sintetice (nu sunt datele lui A) pe modelul cu defecte.
"""
from backend.engine.defects import build
from backend.engine.match import match_event


def ev(**ref):
    return {"event_id": "TEST", "echipa_sursa": "mentenanta", "tip": "avarie_semnalata",
            "referinta": ref, "status": "executat", "data": "2026-09-01", "text_original": "test"}


def main() -> None:
    r = build()
    net, real, d = r["model"], r["real"], r["defects"]
    lipsa = d["scenariul_1_nod_lipsa"]
    nod_ok = next(iter(net["noduri"].values()))
    n_lat, n_lon = nod_ok["lat"], nod_ok["lon"]
    T = []

    def check(nume, event, status, **asteptat):
        m = match_event(event, net)
        ok = m["status"] == status and all(
            (k in m["semnale"]) if k == "semnal" else m.get(k) == v
            for k, v in asteptat.items() if k != "semnal")
        if "semnal" in asteptat:
            ok = ok and asteptat["semnal"] in m["semnale"]
        T.append(ok)
        print(("OK  " if ok else "FAIL"), nume, "->", m["status"], m["element_id"], m["metoda"], m["calitate"], m["semnale"])
        if not ok:
            print("     motiv:", m["motiv"])

    check("ID nod existent", ev(element_id=nod_ok["id"]), "potrivit", element_id=nod_ok["id"], metoda="id", calitate=1.0)
    check("ID nod lipsă din model", ev(element_id=lipsa["nod_lipsa"]), "absent_din_model")
    check("ID tronson lipsă cu prefix", ev(element_id=lipsa["tronsoane_lipsa"][0]), "absent_din_model")
    check("ID tronson cu prefix existent", ev(element_id="A-T-002"), "potrivit", element_id="A-T-002")
    # T-100 există doar în categoria aeriană (S are 81 de tronsoane, R are 22)
    check("cod fără prefix, un singur tronson posibil", ev(element_id="T-100"), "potrivit", element_id="A-T-100", semnal="cod_fara_prefix")
    check("cod fără prefix ambiguu", ev(element_id="T-002"), "ambiguu", semnal="cod_fara_prefix")
    check("coordonate pe nod existent", ev(coordonate={"lat": n_lat, "lon": n_lon}), "potrivit", element_id=nod_ok["id"], metoda="coordonate")
    check("coordonate la nodul lipsă", ev(coordonate=lipsa["coordonate"]), "absent_din_model", metoda="coordonate")
    check("lat/lon inversate", ev(coordonate={"lat": n_lon, "lon": n_lat}), "potrivit", element_id=nod_ok["id"], semnal="coordonate_corectate")
    check("zecimale lipsă", ev(coordonate={"lat": 4.428, "lon": 26.06}), "nepotrivit", semnal="coordonate_in_afara_zonei")
    check("doar adresă", ev(adresa="Str. Exemplu 5", nr_cadastral="12345"), "nepotrivit", semnal="doar_adresa")
    check("fără referință", ev(), "nepotrivit")
    check("ID bun, coordonate departe", ev(element_id=nod_ok["id"], coordonate=lipsa["coordonate"]), "potrivit", semnal="inconsecventa_id_coordonate")
    assert all(T), "unele cazuri au eșuat"
    print(f"OK: {len(T)} cazuri")


if __name__ == "__main__":
    main()
