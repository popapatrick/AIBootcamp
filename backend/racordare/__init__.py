"""Predicția lanțului de stâlpi pentru o cerere de racordare (rol A). Vezi README.md."""
from statistics import median

from backend.engine.analiza_harta import traseu_pe_strazi
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


def _treapta_analiza(out, casa, noduri, net, strazi, cfg, sursa, d0):
    """Treapta 3: analiza hărții (drum pe străzi) în loc de linia dreaptă; 4 dacă nu există stâlp în zonă."""
    r = cfg["racordare"]
    net_m = net if "features" not in net else {"noduri": {i: {"id": i, "lat": p[0], "lon": p[1]} for i, p in noduri}}
    ah = traseu_pe_strazi(casa, net_m, cfg, sursa=sursa, strazi=strazi)
    out["analiza_harta"], out["factor_analiza"] = ah, ah["factor"]
    ales = ah["ales"]
    if ales is None:
        out.update(treapta=4, nod_start=None, status="fara_nod",
                   motiv=f"niciun stâlp existent în {cfg['analiza_harta']['raza_cautare_m']:g} m: doar punctul casei")
        return out
    out["nod_start"], out["distanta_m"] = ales["de_la"], ales["lungime_m"]
    out["status"] = "linie_dreapta" if ah["fara_drum"] else "lant"
    out["urmeaza_strada"] = None if ah["fara_drum"] else 1.0
    out["motiv"] = (f"cel mai apropiat nod e la {d0:.0f} m (peste raza extinsă {r['raza_extinsa_m']} m): "
                    + ("analiza hărții n-a găsit drum pe străzi, linie dreaptă" if ah["fara_drum"] else
                       f"analiza hărții: drum pe străzi de {ales['lungime_m']:g} m"))
    _lant_din_analiza(out, ah, r)
    return out


def _lant_din_analiza(out, ah, r):
    """Pune în `out` stâlpii și cablurile din analiza hărții `ah`, tăiate la `max_stalpi_prezisi` (cablul final merge pe stradă până la casă)."""
    ales = ah["ales"]
    noi, cabluri = ales["stalpi_noi"], [dict(c) for c in ales["cabluri"]]
    if len(noi) > r["max_stalpi_prezisi"]:
        m = r["max_stalpi_prezisi"]
        i = next(k for k, c in enumerate(cabluri) if c["la"] == f"stalp-{m}")
        pct = [cabluri[i]["puncte"][-1]]
        for c in cabluri[i + 1:]:
            pct += [q for q in c["puncte"] if q != pct[-1]]
        cabluri = cabluri[:i + 1] + [{"de_la": f"stalp-{m}", "la": "casa", "puncte": pct}]
        noi = noi[:m]
        out["ambiguu"], out["motiv"] = True, f"lanț mai lung decât {m} stâlpi; prezis doar începutul; {out['motiv']}"
    out["stalpi"] = [{"ordine": k, "lat": round(p[0], 7), "lon": round(p[1], 7)} for k, p in enumerate(noi, 1)]
    out["cabluri"] = cabluri
    return out


def prezice_lant(locatie: dict, net: dict, strazi: list[dict], cfg: dict, sursa: str | None = None) -> dict:
    """Lanț prezis de la cel mai apropiat nod până la casa `locatie` {lat, lon}.

    net: network.geojson sau dict-ul motorului. strazi: osm.strazi(). cfg: weights.yaml. sursa: sursa locației casei
    (cheie din `plafon_locatie`), doar pentru acuratețea analizei hărții.
    Întoarce {status: lant|linie_dreapta|fara_nod, treapta, nod_start, distanta_m, stalpi, cabluri,
    urmeaza_strada, ambiguu, motiv} (+ `analiza_harta` și `factor_analiza` la treapta 3). Scara (Sesiunea 4):
    1 nod în raza_nod_m; 2 nod în raza_extinsa_m (stâlpi la distanța mediană a tronsoanelor); 3 casa e mai departe de
    raza extinsă: ANALIZA HĂRȚII (`backend.engine.analiza_harta.traseu_pe_strazi`): drumul cel mai scurt pe străzi de la
    unul dintre cei mai apropiați stâlpi, stâlpi la ~40 m (status `lant`), sau, fără drum pe străzi, linie dreaptă spre
    cel mai apropiat stâlp (status `linie_dreapta`, scor `analiza_harta.fara_drum`); 4 niciun stâlp existent în
    `analiza_harta.raza_cautare_m` (sau rețea goală): doar casa (status fara_nod, fără lanț). Scorul îl calculează motorul
    din `treapta` (factor_*; la treapta 3 din `factor_analiza`), nu această funcție. Stâlpii refolosiți apar în cabluri
    cu ID-ul lor real; cei noi sunt `stalp-k` (doar ei sunt în `stalpi`). Peste cfg.racordare.max_stalpi_prezisi se taie
    și rezultatul e ambiguu. Pură."""
    r = cfg["racordare"]
    casa = (locatie["lat"], locatie["lon"])
    out = {"status": "fara_nod", "treapta": 4, "nod_start": None, "distanta_m": None, "stalpi": [], "cabluri": [],
           "urmeaza_strada": None, "ambiguu": False, "motiv": None}
    noduri, tr = _elemente(net)
    if not noduri:
        out["motiv"] = "rețea fără noduri: doar punctul casei"
        return out
    d0, (nid, npos) = min((dist_m(casa, p), (i, p)) for i, p in noduri)
    out["treapta"] = 1 if d0 <= r["raza_nod_m"] else 2 if d0 <= r["raza_extinsa_m"] else 3
    if out["treapta"] > 1:
        out["motiv"] = f"cel mai apropiat nod e la {d0:.0f} m (raza {r['raza_nod_m']} m, extinsă {r['raza_extinsa_m']} m)"
    out["nod_start"] = nid
    if out["treapta"] == 3:
        return _treapta_analiza(out, casa, noduri, net, strazi, cfg, sursa, d0)
    span = median(_lungime(t) for t in tr if len(t) > 1) if tr else 30.0
    drum = _drum_strada(npos, casa, strazi)
    if not drum and dist_m(npos, casa) > MAX_STRADA_M:
        # „nu prin case” și la treptele 1-2 (V4): linia dreaptă mai lungă de ~40 m devine drum pe străzi (analiza hărții) de la nod
        net_m = net if "features" not in net else {"noduri": {i: {"id": i, "lat": p[0], "lon": p[1]} for i, p in noduri}}
        ah = traseu_pe_strazi(casa, net_m, cfg, sursa=sursa, strazi=strazi, de_la=nid)
        if ah["ales"] is not None and not ah["fara_drum"]:
            out["analiza_harta"], out["status"], out["urmeaza_strada"] = ah, "lant", 1.0
            out["distanta_m"] = ah["ales"]["lungime_m"]
            out["motiv"] = ((out["motiv"] + "; ") if out["motiv"] else "") + f"analiza hărții: drum pe străzi de {ah['ales']['lungime_m']:g} m în loc de linie dreaptă"
            return _lant_din_analiza(out, ah, r)
    out["status"] = "lant" if drum else "linie_dreapta"
    out["urmeaza_strada"] = 1.0 if drum else None
    drum = drum or [npos, casa]
    total = _lungime(drum)
    out["distanta_m"] = round(total, 1)
    n = max(0, round(total / span) - 1)  # ultimul cablu spre casă ~ un span
    if n > r["max_stalpi_prezisi"]:
        n = r["max_stalpi_prezisi"]
        out["ambiguu"], out["motiv"] = True, f"lanț mai lung decât {n} stâlpi; prezis doar începutul" + (f"; {out['motiv']}" if out["motiv"] else "")
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
