"""Generează `data/events/events.json` din cele 55 de rapoarte ale scenariului (Sesiunea 4, plan 7.3). Determinist, fără AI.

    EXTRACT_CLI=0 .venv/bin/python scripts/genereaza_scenariu.py [--out cale] [--dry]

Pași: citește `data/reports/index.json` și fișierele `.txt`; pentru fiecare ia evenimentul extras de Haiku din
`data/cache/` (`extract_event_cu_metoda(text, sursa, data)`); dacă lipsește din cache, se oprește cu eroare (nu cade pe
regex). Evenimentele extrase NU se corectează: se adaugă doar `event_id` stabil `EV4-001`… (ordinea: data, apoi numele
fișierului) și `text_original`. Scrie lista sortată cronologic. Tipărește unde `tip` extras diferă de `tip_asteptat`.
Date FICTIVE.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("EXTRACT_CLI", "0")
os.environ.pop("EXTRACT_ALLOW_API", None)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.extract import extract as ex  # noqa: E402


def genereaza() -> tuple[list[dict], list[str], list[str]]:
    """(evenimente, diferențe tip, lipsă din cache)."""
    idx = json.loads((ROOT / "data" / "reports" / "index.json").read_text(encoding="utf-8"))
    idx.sort(key=lambda r: (r["data"], r["fisier"]))
    evs, dif, lipsa = [], [], []
    for i, r in enumerate(idx, 1):
        text = (ROOT / "data" / "reports" / r["fisier"]).read_text(encoding="utf-8")
        try:
            ev, metoda = ex.extract_event_cu_metoda(text, r["sursa"], r["data"])
        except Exception as e:  # CacheMiss sau altă eroare: nu cădem pe regex
            lipsa.append(f"{r['fisier']}: {type(e).__name__}")
            continue
        if metoda != "ai_cache":
            lipsa.append(f"{r['fisier']}: metoda {metoda}")
            continue
        ev = dict(ev)
        ev["event_id"] = f"EV4-{i:03d}"
        ev["text_original"] = text
        evs.append(ev)
        asteptat = r.get("tip_asteptat")
        if asteptat and ev.get("tip") != asteptat:
            dif.append(f"{r['fisier']}: extras {ev.get('tip')}, așteptat {asteptat}")
    return evs, dif, lipsa


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data" / "events" / "events.json"))
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    evs, dif, lipsa = genereaza()
    if lipsa:
        print("LIPSĂ din cache (oprit):", *lipsa, sep="\n  ")
        return 1
    if not a.dry:
        Path(a.out).write_text(json.dumps(evs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(evs)} evenimente{'' if a.dry else ' scrise în ' + a.out}")
    print("Tip extras diferit de tip_asteptat:", *(dif or ["(niciunul)"]), sep="\n  ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
