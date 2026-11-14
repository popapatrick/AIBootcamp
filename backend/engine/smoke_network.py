"""Smoke test etapa 1: python -m backend.engine.smoke_network"""
from backend.engine.network import load_network
from backend.engine.defects import build


def main() -> None:
    n = load_network()
    assert n["post"] and n["post"]["id"] == "DX10-2-099812", "post lipsă"
    assert len(n["noduri"]) == 265, len(n["noduri"])
    assert len(n["tronsoane"]) == 264, len(n["tronsoane"])
    nelegat = [t["id"] for t in n["tronsoane"].values() if None in t["capete"]]
    assert not nelegat, f"capete nelegate: {nelegat}"
    r = build()
    d = r["defects"]["scenariul_1_nod_lipsa"]
    assert d["nod_lipsa"] not in r["model"]["noduri"]
    assert all(t not in r["model"]["tronsoane"] for t in d["tronsoane_lipsa"])
    t2 = r["defects"]["scenariul_2_cablu_inlocuit"]["tronson"]
    assert r["model"]["tronsoane"][t2]["sectiune"] != r["real"]["tronsoane"][t2]["sectiune"]
    print("OK: 1 post, 265 noduri, 264 tronsoane, toate capetele legate, defecte aplicate")


if __name__ == "__main__":
    main()


def _test_clasa() -> None:
    """Clasele KMZ (aspect-harta-kmz): 148 casa, 113 important, 4 origine, 1 post; 161 aerian, 22 ramura, 81 subteran."""
    from collections import Counter
    from backend.engine.network import clasa_element, load_network, to_geojson
    net = load_network()
    g = to_geojson(net)
    n = Counter(f["properties"]["clasa"] for f in g["features"] if f["geometry"]["type"] == "Point")
    t = Counter(f["properties"]["clasa"] for f in g["features"] if f["geometry"]["type"] != "Point")
    assert n == {"casa": 148, "important": 113, "origine": 4, "post": 1}, n
    assert t == {"aerian": 161, "ramura": 22, "subteran": 81}, t
    assert clasa_element({"tip_element": "nod", "serie": "Nod JT (adăugat din raport)"}) == "casa"
    print("OK: clase KMZ", dict(n), dict(t))


if __name__ == "__main__":
    _test_clasa()
