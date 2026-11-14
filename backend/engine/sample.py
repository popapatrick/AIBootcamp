"""Eșantion FALS dar valid pentru C (UI/API), până apare motorul real (etapa 5).

Scoruri inventate după regula simplă: 0.6 pentru tot, câteva elemente cu alt nivel,
ca UI-ul să poată desena in_model / predictie / de_verificat. Valid față de contracts/state.schema.json.

    python -m backend.engine.sample
"""
import json
from pathlib import Path

from backend.engine.defects import build

OUT = Path(__file__).resolve().parents[2] / "data" / "model" / "sample"
DATE = ["2026-08-01", "2026-09-01", "2026-10-01"]


def _props(el: dict, nivel: str, scor: float, motiv: str, data: str) -> dict:
    p = {k: v for k, v in el.items() if k not in ("puncte", "lat", "lon")}
    p.update({"element_id": el["id"], "nivel": nivel, "scor": scor, "valid_de_la": data,
              "ultima_verificare": None,
              "motive": [{"text": motiv, "efect": 0.0, "eveniment": None, "data": data}]})
    return p


def main() -> None:
    r = build()
    d = r["defects"]
    model, real = r["model"], r["real"]
    OUT.mkdir(parents=True, exist_ok=True)
    verif = {d["scenariul_2_cablu_inlocuit"]["tronson"]}
    for i, data in enumerate(DATE):
        feats = []
        for n in model["noduri"].values():
            feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [n["lon"], n["lat"]]},
                          "properties": _props(n, "in_model", 0.6, "Element din model, neverificat recent", data)})
        for t in model["tronsoane"].values():
            nivel, scor = ("de_verificat", 0.35) if t["id"] in verif and i >= 1 else ("in_model", 0.6)
            feats.append({"type": "Feature",
                          "geometry": {"type": "LineString", "coordinates": [[o, a] for a, o in t["puncte"]]},
                          "properties": _props(t, nivel, scor, "Date fictive de exemplu", data)})
        if i == 2:  # predicție de exemplu pentru nodul lipsă: linia dreaptă între vecini
            a, b = (real["noduri"][x] for x in d["scenariul_1_nod_lipsa"]["noduri_vecine"])
            el = {"id": "PRED-1", "tip_element": "tronson", "categorie": "predictie"}
            p = _props(el, "predictie", 0.55, "Predicție: linie dreaptă între noduri vecine (exemplu)", data)
            p["predictie"] = {"metoda": "linie_dreapta", "urmeaza_strada": None}
            feats.append({"type": "Feature",
                          "geometry": {"type": "LineString",
                                       "coordinates": [[a["lon"], a["lat"]], [b["lon"], b["lat"]]]},
                          "properties": p})
        (OUT / f"{data}.geojson").write_text(json.dumps(
            {"type": "FeatureCollection", "name": f"EȘANTION FALS {data}", "features": feats},
            ensure_ascii=False), encoding="utf-8")
    timeline = [{"data": DATE[1], "event_id": "EV-SAMPLE-1", "rezumat": "Exemplu: cablu înlocuit, scor scăzut",
                 "elemente_atinse": list(verif)},
                {"data": DATE[2], "event_id": "EV-SAMPLE-2", "rezumat": "Exemplu: predicție nod lipsă",
                 "elemente_atinse": ["PRED-1"]}]
    (OUT / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"eșantion scris în {OUT}")


if __name__ == "__main__":
    main()
