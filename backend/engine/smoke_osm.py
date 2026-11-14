"""Smoke test etapa 6: python -m backend.engine.smoke_osm"""
from backend.engine import osm
from backend.engine.defects import build
from backend.engine.model import GridModel
from backend.engine.network import dist_m

OK: list[bool] = []


def verifica(nume, cond, info=""):
    OK.append(bool(cond))
    print(("OK  " if cond else "FAIL"), nume, info)


def main() -> None:
    verifica("cache OSM disponibil", osm.disponibil())
    r = build()
    D = r["defects"]["scenariul_1_nod_lipsa"]
    c = (D["coordonate"]["lat"], D["coordonate"]["lon"])
    ev = {"event_id": "T-OSM", "echipa_sursa": "mentenanta", "tip": "nod_lipsa", "status": "executat",
          "data": "2026-08-10", "forma_sursa": "campuri", "incredere_extractie": 0.9, "text_original": "test",
          "referinta": {"element_id": D["nod_lipsa"], "coordonate": D["coordonate"]},
          "detalii": {"noduri_vecine": D["noduri_vecine"]}}

    m0 = GridModel()                       # fără OSM: linie dreaptă
    t0 = m0.apply_event(ev)
    m1 = GridModel()
    m1.traseu_fn = osm.traseu_fn()         # cu OSM
    t1 = m1.apply_event(ev)
    p0, p1 = t0["pasi"][2]["rezultat"], t1["pasi"][2]["rezultat"]
    verifica("fără OSM: linie dreaptă", p0["metoda"] == "linie_dreapta" and p0["urmeaza_strada"] is None)
    verifica("cu OSM: traseu pe stradă", p1["metoda"] == "traseu_strada_osm" and p1["urmeaza_strada"] > 0,
             f"urmeaza_strada={p1['urmeaza_strada']}")
    s0 = t0["pasi"][-1]["rezultat"]["scor_propunere"]
    s1 = t1["pasi"][-1]["rezultat"]["scor_propunere"]
    print("     scor propunere fără OSM / cu OSM:", s0, "/", s1)

    # geometria traseului pe stradă are mai multe puncte decât linia dreaptă și ocolește colțul
    leg = [x for x in m1.net["tronsoane"].values() if x["id"].startswith("NOU-")]
    verifica("legături adăugate", len(leg) == 2, str([len(x["puncte"]) for x in leg]))
    verifica("cel puțin o legătură urmează o stradă (mai multe puncte)", any(len(x["puncte"]) > 2 for x in leg))
    for x in leg:
        a, b = x["puncte"][0], x["puncte"][-1]
        verifica(f"{x['id']}: capetele sunt neschimbate", dist_m(a, c) < 0.5 or dist_m(b, c) < 0.5)

    # rutare simplă între două puncte de pe aceeași stradă
    t = osm.traseu(c, (r["real"]["noduri"][D["noduri_vecine"][0]]["lat"], r["real"]["noduri"][D["noduri_vecine"][0]]["lon"]))
    verifica("traseu are lungime ≥ linia dreaptă", t and t["lungime_m"] >= t["lungime_dreapta_m"] - 0.5, str(t and (t["lungime_m"], t["lungime_dreapta_m"])))
    verifica("punct departe de orice stradă -> None", osm.traseu((44.30, 26.10), (44.3001, 26.1001)) is None)
    assert all(OK), "unele verificări au eșuat"
    print(f"OK: {len(OK)} verificări")


if __name__ == "__main__":
    main()
