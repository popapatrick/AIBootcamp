"""Generează punctele turelor de tracking din scenariu (B3): completează `data/events/ture-tracking.json`.

    EXTRACT_CLI=0 .venv/bin/python scripts/genereaza_ture_tracking.py [--verifica]

Fișierul conține definițiile `{echipa, seed, data, ora_start}`; scriptul adaugă cheia `tura` (ieșirea lui `genereaza_tura`: puncte,
plan, lungime) ca scenariul să nu depindă de modificări viitoare ale generatorului. Pentru fiecare tură (în ordine cronologică)
construiește modelul din rapoartele de dinainte de data ei (+ turele anterioare) și alege stâlpii dintre cei cu scor efectiv la
acea dată (preferându-i pe cei ne-verzi). `--verifica` nu scrie nimic: aplică turile și tipărește validările (scor înainte -> după).
Seed-urile au fost alese prin încercări astfel încât fiecare tură să valideze 3–5 stâlpi ne-verzi și să presupună exact 1 stâlp.
Date FICTIVE.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("EXTRACT_CLI", "0")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.engine import osm  # noqa: E402
from backend.engine.model import GridModel  # noqa: E402
from backend.tracking import genereaza_tura  # noqa: E402
from scripts.genereaza_scenariu import genereaza  # noqa: E402

FISIER = ROOT / "data" / "events" / "ture-tracking.json"


def eveniment_tura(i: int, d: dict, tura: dict) -> dict:
    """Evenimentul `tracking_tura` `EV4-T<i>` pentru o definiție `d` și tura ei generată."""
    return {"event_id": f"EV4-T{i:02d}", "echipa_sursa": d["echipa"], "tip": "tracking_tura", "status": "executat",
            "data": d["data"], "tip_sursa_pondere": "tracking_gps", "incredere_extractie": 1.0, "forma_sursa": "campuri",
            "referinta": {}, "text_original": f"Tura de tracking a echipei {d['echipa']}",
            "detalii": {"tura": {"tura_id": tura["tura_id"], "seed": d["seed"], "echipa": d["echipa"], "puncte": tura["puncte"]}}}


def main() -> int:
    defs = json.loads(FISIER.read_text(encoding="utf-8"))
    rapoarte, _, lipsa = genereaza()
    if lipsa:
        print("LIPSĂ din cache:", *lipsa, sep="\n  ")
        return 1
    strazi = osm.strazi()
    ture_ev: list[dict] = []
    out = []
    for i, d in enumerate(sorted(defs, key=lambda x: x["data"]), 1):
        m = GridModel()
        m.traseu_fn = osm.traseu_fn()
        for e in sorted(rapoarte + ture_ev, key=lambda e: e["data"]):
            if e["data"] < d["data"]:
                m.apply_event(e)
        scoruri = {f["properties"]["element_id"]: f["properties"]["scor"] for f in m.snapshot(d["data"])["features"]}
        tura = genereaza_tura(m.net, strazi, m.w, d["echipa"], d["seed"], d["data"], scoruri=scoruri, ora_start=d.get("ora_start", "08:00:00"))
        ev = eveniment_tura(i, d, tura)
        tr = m.apply_event(ev)
        o = next(p for p in tr["pasi"] if p["nume"] == "opriri")["rezultat"]["opriri"]
        print(f"{ev['event_id']} {d['echipa']} {d['data']} seed={d['seed']}: {len(tura['puncte'])} puncte, {tura['durata_min']} min, "
              f"linie dreaptă {tura['linie_dreapta']}, decizie {tr['decizie']}")
        for x in o:
            if x["tip"] == "validare":
                print(f"    validare {x['element_id']}: {x['scor_inainte']} ({x['banda_inainte']}) -> {x['scor_dupa']} ({x['banda_dupa']})")
            elif x["tip"] == "stalp_presupus":
                print(f"    stâlp presupus {x['element_id']}: {x['scor_dupa']}")
        ture_ev.append(ev)
        out.append({**{k: d[k] for k in ("echipa", "seed", "data", "ora_start") if k in d}, "tura": tura})
    if "--verifica" not in sys.argv:
        FISIER.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"scris {FISIER.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
