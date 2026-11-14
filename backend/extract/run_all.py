"""Extrage toate rapoartele din data/reports/ în data/events/events.json.

Numele fișierului: YYYY-MM-DD_<sursa>_<nn>.txt (ex. 2026-09-14_mentenanta_03.txt).
Folosire: python -m backend.extract.run_all
"""
import json
import re
from pathlib import Path

from backend.extract.extract import extract_event

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "data" / "reports"
OUT = ROOT / "data" / "events" / "events.json"
NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})_([a-z_]+)_\d+\.txt$")


def main() -> None:
    jobs = []
    for f in REPORTS.glob("*.txt"):
        m = NAME.match(f.name)
        if not m:
            print(f"SKIP {f.name}: nume nerecunoscut")
            continue
        jobs.append((m.group(1), m.group(2), f))
    jobs.sort(key=lambda j: (j[0], j[2].name))

    events = []
    for i, (data, sursa, f) in enumerate(jobs, 1):
        ev = extract_event(f.read_text(encoding="utf-8"), sursa, data)
        ev["event_id"] = f"EV-{i:03d}"
        events.append(ev)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {len(events)} evenimente -> {OUT}")


if __name__ == "__main__":
    main()
