"""Defecte introduse în model, ca să avem ce descoperi (scenariile 1 și 2 din plan).

`network.geojson` = realitatea (rețeaua completă din KMZ).
`network_model.geojson` = ce „crede" modelul GIS: fără nodul lipsă și tronsoanele lui,
și cu secțiunea veche la un tronson înlocuit în teren și nerecordat.
`defects.json` = adevărul despre defecte; îl citesc A (rapoarte dummy) și B (verificare).

    python -m backend.engine.defects
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from backend.engine.network import load_network, to_geojson, dist_m

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "model"
SECTIUNE_VECHE = "TYIR 3x35+54,6 OL-Al"   # ce știe modelul
SECTIUNE_NOUA = "TYIR 3x70+54,6 OL-Al"    # ce e în teren după înlocuire


def _bend_deg(net: dict, node_id: str, t1: dict, t2: dict) -> float:
    """Cât de mult se frânge traseul în nod (0 = drept, 180 = întoarcere)."""
    n = net["noduri"][node_id]
    c = (n["lat"], n["lon"])
    pts = []
    for t in (t1, t2):
        a, b = t["puncte"][0], t["puncte"][-1]
        pts.append(b if dist_m(a, c) < dist_m(b, c) else a)

    def ang(p):
        return math.atan2(p[0] - c[0], (p[1] - c[1]) * math.cos(math.radians(c[0])))

    d = abs(math.degrees(ang(pts[0]) - ang(pts[1]))) % 360
    d = 360 - d if d > 180 else d
    return 180 - d


def build() -> dict:
    net = load_network()
    inc: dict[str, list[dict]] = {}
    for t in net["tronsoane"].values():
        for n in t["capete"]:
            if n:
                inc.setdefault(n, []).append(t)

    # Scenariul 1: nod aerian de grad 2, cu cea mai mare frângere a traseului (stradă curbată).
    cand = [(n, ts) for n, ts in inc.items()
            if len(ts) == 2 and all(t["id"].startswith("A-") for t in ts)
            and net["noduri"][n]["serie"].startswith("Nod JT")]
    nod_lipsa, ts = max(cand, key=lambda x: _bend_deg(net, x[0], *x[1]))
    taie = {t["id"] for t in ts}
    vecini = sorted({c for t in ts for c in t["capete"] if c and c != nod_lipsa})

    # Scenariul 2: un tronson aerian, departe de cel de mai sus, cu secțiunea veche în model.
    t2 = next(t for t in net["tronsoane"].values()
              if t["id"].startswith("A-") and t["id"] not in taie and t["lungime_m"] > 30
              and not (set(t["capete"]) & set(vecini + [nod_lipsa])))

    defects = {
        "nota": "Date fictive. Adevărul despre defectele introduse în model.",
        "scenariul_1_nod_lipsa": {
            "nod_lipsa": nod_lipsa,
            "tronsoane_lipsa": sorted(taie),
            "noduri_vecine": vecini,
            "coordonate": {"lat": net["noduri"][nod_lipsa]["lat"], "lon": net["noduri"][nod_lipsa]["lon"]},
            "frangere_grade": round(_bend_deg(net, nod_lipsa, *ts), 1),
        },
        "scenariul_2_cablu_inlocuit": {
            "tronson": t2["id"],
            "sectiune_in_model": SECTIUNE_VECHE,
            "sectiune_reala": SECTIUNE_NOUA,
            "capete": list(t2["capete"]),
        },
    }

    # Modelul: fără nodul lipsă și tronsoanele lui; tronsonul înlocuit cu secțiunea veche.
    model = load_network()
    model["noduri"].pop(nod_lipsa)
    for tid in taie:
        model["tronsoane"].pop(tid)
    model["tronsoane"][t2["id"]]["sectiune"] = SECTIUNE_VECHE
    return {"real": net, "model": model, "defects": defects}


def main() -> None:
    r = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "network_model.geojson").write_text(
        json.dumps(to_geojson(r["model"]), ensure_ascii=False), encoding="utf-8")
    (OUT_DIR / "defects.json").write_text(
        json.dumps(r["defects"], ensure_ascii=False, indent=2), encoding="utf-8")
    m = r["model"]
    print(f"model: {len(m['noduri'])} noduri, {len(m['tronsoane'])} tronsoane")
    print(json.dumps(r["defects"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
