"""Calibrare: rulează cele 28 de rapoarte ale lui A prin motor și arată deciziile.

    python -m backend.engine.calibrare            # folosește data/events/events.json dacă există, altfel „oracol"
    python -m backend.engine.calibrare --oracol   # forțează evenimentele „oracol"

„Oracol" = evenimente construite din rapoarte + `data/reports/index.json` (adevărul lui A), cu câmpurile
citite prin regex din text. NU e extracția Claude; verifică politica de scor presupunând extracție corectă
(A a măsurat pe extracția reală: tip corect 21/28, element_id corect 18/28). Date FICTIVE.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from backend.engine import osm
from backend.engine.model import GridModel

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "data" / "reports"
SECT = r"(TYIR\s*[\dx+,\s]*?OL-Al|TYIR[\dx+, ]+Al)"


def _coord(text: str):
    m = re.search(r"lat\s*([\d.]+)\s*,\s*lon\s*([\d.]+)", text)
    if m:
        return {"lat": float(m.group(1)), "lon": float(m.group(2))}
    m = re.search(r"(?<![\d.])(\d{2}\.\d{3,})\s*,\s*(\d{2}\.\d{3,})", text)
    if m:
        return {"lat": float(m.group(1)), "lon": float(m.group(2))}
    m = re.search(r"Coordonate:\s*(\d{6,})\s*,\s*(\d{6,})", text)
    if m:
        return {"lat": float(m.group(1)), "lon": float(m.group(2))}
    return None


def oracol() -> list[dict]:
    idx = json.loads((REPORTS / "index.json").read_text(encoding="utf-8"))
    out = []
    for i, r in enumerate(idx, 1):
        text = (REPORTS / r["fisier"]).read_text(encoding="utf-8")
        sursa, tip = r["sursa"], r["tip_asteptat"]
        forma = "campuri" if re.search(r"^(Cod element|Coordonate):", text, re.M) else "text_liber"
        low = text.lower()
        if sursa == "apel_client":
            status = "semnalat"
        else:
            m = re.search(r"(?:Status|Stare):\s*(\w+)", text)
            status = m.group(1).lower() if m else ("planificat" if "planificat" in low and "executat" not in low else "executat")
        if tip == "linie_planificata" and status == "executat" and ("fără defecte" in low or "fara defecte" in low):
            tip = "verificare"                       # A propune `verificare` pentru inspecții (acceptat de B)
        # element_id: adevărul lui A, dar doar unde textul îl conține (racorduri/apeluri: doar „Cod element:")
        eid = r["element_id_asteptat"]
        if tip in ("racord_nou",) or sursa == "apel_client":
            m = re.search(r"Cod element:\s*(?:nod\s*)?([A-Z]-T-\d+|\d{7}|T-\d+)", text)
            eid = m.group(1) if m else None
        det: dict = {}
        sec = re.search(SECT, text)
        if sec:
            nou = re.search(r"Secțiune nouă[^:]*:\s*" + SECT, text) or re.search(r"cel nou este\s*" + SECT, text)
            det["sectiune_noua" if (nou or "înlocuit" in low or "schimbat" in low) else "sectiune_observata"] = (nou or sec).group(1).strip()
        out.append({"event_id": f"OR-{i:02d}", "echipa_sursa": sursa, "tip": tip, "status": status, "data": r["data"],
                    "forma_sursa": forma, "incredere_extractie": 0.85 if forma == "campuri" else 0.65,
                    "text_original": text, "campuri_lipsa": [],
                    "referinta": {"element_id": eid, "coordonate": _coord(text) if sursa != "apel_client" or True else None,
                                  "adresa": None, "nr_cadastral": None},
                    "detalii": det, "_fisier": r["fisier"], "_scenariu": r["scenariu"]})
    return sorted(out, key=lambda e: (e["data"], e["event_id"]))


def main() -> None:
    cale = ROOT / "data" / "events" / "events.json"
    if "--oracol" not in sys.argv and cale.exists():
        ev, sursa = json.loads(cale.read_text(encoding="utf-8")), "events.json (extracție Claude)"
        ev.sort(key=lambda e: (e["data"], e["event_id"]))
    else:
        ev, sursa = oracol(), "oracol (adevărul lui A + regex)"
    print(f"Evenimente: {len(ev)}, sursa: {sursa}\n")
    m = GridModel()
    m.traseu_fn = osm.traseu_fn()
    rez = Counter()
    for e in ev:
        t = m.apply_event(e)
        pot = t["pasi"][1]["rezultat"]
        sc = t["pasi"][-1]["rezultat"]
        s = sc.get("scor_propunere") if sc.get("scor_propunere") is not None else sc.get("scor_nou")
        rez[t["decizie"]] += 1
        print(f"{e['data']} {(e.get('_fisier') or e['event_id'])[11:34]:<24} sc{str(e.get('_scenariu') or '-'):<4}"
              f"{e['tip']:<17}{e['forma_sursa'][:5]:<6}pot={pot['status'][:9]:<10}{(pot.get('element_id') or '-')[:12]:<13}"
              f"-> {t['decizie']:<16}{'' if s is None else round(s, 2)}")
    print("\nDecizii:", dict(rez))
    d0, d1 = m.start, m.ultima_data
    for d in (d0, "2026-09-15", d1):
        st = m.statistici(d)
        print(f"{d}: {st['procent']} scor mediu {st['scor_mediu']}, verificat recent {st['verificat_recent_pct']}%")


if __name__ == "__main__":
    main()
