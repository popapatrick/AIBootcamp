"""Rețeaua JT în graf: parsare KMZ/KML -> noduri + tronsoane -> GeoJSON.

Date FICTIVE (PTAB 7812). Doar bibliotecă standard.

Folosire:
    python -m backend.engine.network            # scrie data/model/network.geojson
    from backend.engine.network import load_network
    net = load_network()                        # dict cu "noduri", "tronsoane", "post"
"""
from __future__ import annotations

import json
import math
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KMZ = ROOT / "data" / "network" / "Retea_JT_PTAB_7812.kmz"
OUT = ROOT / "data" / "model" / "network.geojson"
NS = {"k": "http://www.opengis.net/kml/2.2"}
SNAP_M = 12.0  # distanța maximă (m) la care un capăt de tronson se leagă de un nod (cablurile subterane se opresc la 5-10 m de nod)


def _cells(html: str) -> dict[str, str]:
    """Extrage perechile <b>cheie</b></td><td>valoare din descrierea HTML."""
    return {k: v for k, v in re.findall(r"<b>([^<]+)</b></td><td>([^<]*)</td>", html or "")}


def _coords(text: str) -> list[tuple[float, float]]:
    """'lon,lat,alt lon,lat,alt' -> [(lat, lon), ...] (ordinea lat, lon)."""
    out = []
    for tok in text.split():
        p = tok.split(",")
        out.append((float(p[1]), float(p[0])))
    return out


def dist_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distanță aproximativă în metri între două puncte (lat, lon)."""
    dlat = (a[0] - b[0]) * 111_320
    dlon = (a[1] - b[1]) * 111_320 * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot(dlat, dlon)


def _kml_text() -> str:
    with zipfile.ZipFile(KMZ) as z:
        return z.read("doc.kml").decode("utf-8")


def load_network() -> dict:
    """Citește KMZ-ul. Întoarce {"post", "noduri", "tronsoane"}.

    noduri[cod]    = {id, tip_element, serie, lat, lon, plecare?}
    tronsoane[id]  = {id, cod_original, tip_element, categorie, sectiune, lungime_m, puncte, capete}
    id tronson = prefix categorie + cod din KMZ: A-T-001 (aerian), R-T-001 (ramuri), S-T-001 (subteran)
    capete = (id_nod_start | None, id_nod_final | None), prin potrivire pe coordonate.
    """
    root = ET.fromstring(_kml_text())
    post, noduri, tronsoane = None, {}, {}

    def walk(folder, path):
        for ch in folder:
            tag = ch.tag.split("}")[1]
            if tag == "Folder":
                yield from walk(ch, path + [ch.findtext("k:name", "", NS)])
            elif tag == "Placemark":
                yield path, ch

    doc = root.find("k:Document", NS)
    for path, pm in walk(doc, []):
        f = _cells(pm.findtext("k:description", "", NS))
        pt = pm.find("k:Point/k:coordinates", NS)
        ls = pm.find("k:LineString/k:coordinates", NS)
        multi = pm.findall("k:MultiGeometry/k:LineString/k:coordinates", NS)
        if multi:
            # Cablurile subterane sunt desenate punctat: mai multe segmente scurte.
            # Le unim într-un singur traseu (de la începutul primului la sfârșitul ultimului).
            ls = multi[0]
            ls.text = " ".join(c.text.strip() for c in multi)
        if pt is not None:
            lat, lon = _coords(pt.text)[0]
            if "Cod post" in f:
                post = {"id": f["Cod post"], "tip_element": "post_transformare",
                        "nume": f.get("Denumire"), "putere": f.get("Putere instalată"),
                        "lat": lat, "lon": lon}
            else:
                cod = f["Cod nod"]
                noduri[cod] = {"id": cod, "tip_element": "nod", "serie": f.get("Tip", ""),
                               "plecare": f.get("Plecare JT"), "lat": lat, "lon": lon}
        elif ls is not None:
            cat = path[-1] if path else ""
            # Codurile T-001... se repetă în fiecare categorie (aerian/ramuri/subteran),
            # deci id-ul unic are prefix: A-T-001, R-T-001, S-T-001.
            pref = "R" if "ramuri" in cat else "S" if "subteran" in cat else "A"
            cod = f["Tronson"]
            tid = f"{pref}-{cod}"
            lung = float(f["Lungime"].split()[0])
            tronsoane[tid] = {"id": tid, "cod_original": cod, "tip_element": "tronson",
                              "categorie": cat, "sectiune": f.get("Secțiune"),
                              "lungime_m": lung, "puncte": _coords(ls.text),
                              "capete": (None, None)}

    # Legăm capetele tronsoanelor de cel mai apropiat nod (sub SNAP_M metri).
    pool = list(noduri.values())
    for t in tronsoane.values():
        ends = []
        for p in (t["puncte"][0], t["puncte"][-1]):
            best = min(pool, key=lambda n: dist_m(p, (n["lat"], n["lon"])))
            ends.append(best["id"] if dist_m(p, (best["lat"], best["lon"])) <= SNAP_M else None)
        t["capete"] = tuple(ends)
    return {"post": post, "noduri": noduri, "tronsoane": tronsoane}


SIMULARE = ROOT / "data" / "simulare" / "puncte-simulare.json"


def incarca_puncte_simulare(net: dict, cale: Path = SIMULARE) -> int:
    """Adaugă în `net` punctele simulate hardcodate (data/simulare/puncte-simulare.json, A4): ele fac parte din rețeaua de
    start considerată reală. Fișier lipsă = nimic adăugat. Întoarce numărul de noduri adăugate. Date FICTIVE."""
    if not cale.exists():
        return 0
    d = json.loads(cale.read_text(encoding="utf-8"))
    for n in d.get("noduri", []):
        net["noduri"][n["id"]] = {"id": n["id"], "tip_element": "nod", "serie": n.get("serie", ""), "plecare": None,
                                  "lat": n["lat"], "lon": n["lon"]}
    for t in d.get("tronsoane", []):
        pts = [tuple(p) for p in t["puncte"]]
        net["tronsoane"][t["id"]] = {"id": t["id"], "cod_original": None, "tip_element": "tronson",
                                     "categorie": t.get("categorie", "aerian"), "sectiune": None,
                                     "lungime_m": round(sum(dist_m(a, b) for a, b in zip(pts, pts[1:])), 1),
                                     "puncte": pts, "capete": tuple(t["capete"])}
    return len(d.get("noduri", []))


def clasa_element(el: dict) -> str:
    """Clasa vizuală din KMZ (contracts/state.schema.json, `clasa`).
    Noduri: serie 7 = casa, serie 5/6 = important, origine plecare JT = origine; post = post.
    Tronsoane: aerian | ramura | subteran după categorie. Elementele fără serie/categorie
    (adăugate din rapoarte): nod = casa, tronson = aerian."""
    tip = el.get("tip_element")
    if tip == "post_transformare":
        return "post"
    if tip == "tronson":
        cat = (el.get("categorie") or "").lower()
        if "subteran" in cat:
            return "subteran"
        if "ramur" in cat:
            return "ramura"
        return "aerian"
    serie = (el.get("serie") or "").lower()
    if "origine" in serie:
        return "origine"
    if "serie 7" in serie:
        return "casa"
    if "serie 5" in serie or "serie 6" in serie:
        return "important"
    return "casa"


def to_geojson(net: dict) -> dict:
    """GeoJSON FeatureCollection (coordonate [lon, lat]), pentru hartă."""
    feats = []
    if net["post"]:
        p = net["post"]
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
                      "properties": {**{k: v for k, v in p.items() if k not in ("lat", "lon")},
                                     "clasa": clasa_element(p)}})
    for n in net["noduri"].values():
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [n["lon"], n["lat"]]},
                      "properties": {**{k: v for k, v in n.items() if k not in ("lat", "lon")},
                                     "clasa": clasa_element(n)}})
    for t in net["tronsoane"].values():
        props = {k: v for k, v in t.items() if k != "puncte"}
        props["capete"] = list(t["capete"])
        props["clasa"] = clasa_element(t)
        feats.append({"type": "Feature",
                      "geometry": {"type": "LineString",
                                   "coordinates": [[lon, lat] for lat, lon in t["puncte"]]},
                      "properties": props})
    return {"type": "FeatureCollection",
            "name": "Rețea JT PTAB 7812 (date fictive)", "features": feats}


def main() -> None:
    net = load_network()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(to_geojson(net), ensure_ascii=False), encoding="utf-8")
    leg = sum(1 for t in net["tronsoane"].values() if None not in t["capete"])
    print(f"post: {1 if net['post'] else 0}, noduri: {len(net['noduri'])}, "
          f"tronsoane: {len(net['tronsoane'])} ({leg} cu ambele capete legate) -> {OUT}")


if __name__ == "__main__":
    main()
