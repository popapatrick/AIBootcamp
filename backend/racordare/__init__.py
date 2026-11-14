"""Predicția lanțului de stâlpi pentru o cerere de racordare (rol A). Vezi README.md."""
from statistics import median

from backend.engine.network import dist_m

MAX_STRADA_M = 40  # shortcut: prag fix pentru "stradă lângă casă/nod", nu e în weights.yaml; mută-l acolo dacă se calibrează


def _lungime(pts):
    return sum(dist_m(a, b) for a, b in zip(pts, pts[1:]))


def _elemente(net):
    """Acceptă GeoJSON (network.geojson) sau dict-ul motorului {noduri, tronsoane}.
    Întoarce ([(id, (lat, lon))], [lista de puncte (lat, lon) per tronson neterân])."""
    if "features" in net:
        noduri, tr = [], []
        for f in net["features"]:
            p, g = f["properties"], f["geometry"]
            if g["type"] == "Point":
                noduri.append((p["id"], (g["coordinates"][1], g["coordinates"][0])))
            elif p.get("clasa") != "subteran":
                tr.append([(lat, lon) for lon, lat in g["coordinates"]])
        return noduri, tr
    noduri = [(n["id"], (n["lat"], n["lon"])) for n in net["noduri"].values()]
    tr = [[tuple(q) for q in t["puncte"]] for t in net["tronsoane"].values() if t.get("clasa") != "subteran"]
    return noduri, tr


def _cel_mai_aproape(p, pcts):
    """(distanță, index) al punctului din pcts cel mai apropiat de p."""
    return min((dist_m(p, q), i) for i, q in enumerate(pcts))


def _drum_strada(start, casa, strazi):
    """Puncte start -> casă pe aceeași stradă (cea cu suma distanțelor minimă), sau None."""
    best = None
    for s in strazi:
        if len(s["puncte"]) < 2:
            continue
        d1, i = _cel_mai_aproape(start, s["puncte"])
        d2, j = _cel_mai_aproape(casa, s["puncte"])
        if d1 <= MAX_STRADA_M and d2 <= MAX_STRADA_M and (best is None or d1 + d2 < best[0]):
            seg = s["puncte"][i:j + 1] if i <= j else s["puncte"][j:i + 1][::-1]
            best = (d1 + d2, [start] + [tuple(q) for q in seg] + [casa])
    return best and best[1]


def _la_distanta(drum, d):
    """Punctul (lat, lon) la distanța d (m) de începutul drumului și indexul segmentului."""
    for k, (a, b) in enumerate(zip(drum, drum[1:])):
        l = dist_m(a, b)
        if d <= l or k == len(drum) - 2:
            t = d / l if l else 0
            return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), k
        d -= l


def prezice_lant(locatie: dict, net: dict, strazi: list[dict], cfg: dict) -> dict:
    """Lanț prezis de la cel mai apropiat nod până la casa `locatie` {lat, lon}.

    net: network.geojson sau dict-ul motorului. strazi: osm.strazi(). cfg: weights.yaml.
    Întoarce {status: lant|linie_dreapta|fara_nod, nod_start, distanta_m, stalpi, cabluri,
    urmeaza_strada, ambiguu, motiv}. Stâlpii la distanța mediană a tronsoanelor existente;
    peste cfg.racordare.max_stalpi_prezisi se taie și rezultatul e ambiguu. Pură."""
    r = cfg["racordare"]
    casa = (locatie["lat"], locatie["lon"])
    out = {"status": "fara_nod", "nod_start": None, "distanta_m": None, "stalpi": [], "cabluri": [],
           "urmeaza_strada": None, "ambiguu": False, "motiv": None}
    noduri, tr = _elemente(net)
    if not noduri:
        out["motiv"] = "rețea fără noduri"
        return out
    d0, (nid, npos) = min((dist_m(casa, p), (i, p)) for i, p in noduri)
    if d0 > r["raza_nod_m"]:
        out["motiv"] = f"cel mai apropiat nod e la {d0:.0f} m (raza {r['raza_nod_m']} m)"
        return out
    out["nod_start"] = nid
    span = median(_lungime(t) for t in tr if len(t) > 1) if tr else 30.0
    drum = _drum_strada(npos, casa, strazi)
    out["status"] = "lant" if drum else "linie_dreapta"
    out["urmeaza_strada"] = 1.0 if drum else None
    drum = drum or [npos, casa]
    total = _lungime(drum)
    out["distanta_m"] = round(total, 1)
    n = max(0, round(total / span) - 1)  # ultimul cablu spre casă ~ un span
    if n > r["max_stalpi_prezisi"]:
        n = r["max_stalpi_prezisi"]
        out["ambiguu"], out["motiv"] = True, f"lanț mai lung decât {n} stâlpi; prezis doar începutul"
    # poziții pe drum: pct i = (punct, index segment); cablu = segmentele dintre două poziții
    poz = [(drum[0], 0)] + [_la_distanta(drum, k * span) for k in range(1, n + 1)] + [(drum[-1], len(drum) - 2)]
    ids = [nid] + [f"stalp-{k}" for k in range(1, n + 1)] + ["casa"]
    out["stalpi"] = [{"ordine": k, "lat": round(poz[k][0][0], 7), "lon": round(poz[k][0][1], 7)} for k in range(1, n + 1)]
    for k in range(len(ids) - 1):
        (p, i), (q, j) = poz[k], poz[k + 1]
        pts = [p] + list(drum[i + 1:j + 1]) + [q]
        out["cabluri"].append({"de_la": ids[k], "la": ids[k + 1], "puncte": [[a, b] for a, b in pts]})
    return out


from backend.racordare.operator_demo import LocalizareEroare, locatie_operator_demo  # noqa: E402,F401  (după definiții: importă _elemente)
