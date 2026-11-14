"""Test offline etapa 3: python -m backend.extract.test_extract (fără API, fără rețea)."""
import json
import tempfile
from datetime import date
from pathlib import Path

from backend.extract import extract as ex

TEXT = "Fișă mentenanță. Nod 6925190 înlocuit cablu, 14.09.2026. Lungime 120 m."
GOOD = {
    "event_id": "", "echipa_sursa": "mentenanta", "tip": "activ_inlocuit",
    "referinta": {"element_id": "6925190", "coordonate": None, "adresa": None,
                  "nr_cadastral": None, "id_client": None},
    "status": "executat", "data": "2026-09-14", "forma_sursa": "text_liber",
    "tip_sursa_pondere": "text_liber", "text_original": "", "incredere_extractie": 0.8,
    "campuri_lipsa": ["adresa", "nr_cadastral"], "detalii": {"lungime_m": 120},
}


def main() -> None:
    calls = []
    ex._call_api = lambda text, sursa, data: (calls.append(1), json.loads(json.dumps(GOOD)))[1]
    with tempfile.TemporaryDirectory() as tmp:
        ex.CACHE_DIR = Path(tmp)

        ev = ex.extract_event(TEXT, "mentenanta", "2026-09-14")
        assert ev["text_original"] == TEXT and ev["echipa_sursa"] == "mentenanta"
        assert ev["event_id"] and ev["referinta"]["element_id"] == "6925190"
        assert len(calls) == 1

        assert ex.extract_event(TEXT, "mentenanta", "2026-09-14") == ev  # cache hit
        assert len(calls) == 1, "cache miss"

        seq = [dict(GOOD, tip="inventat"), json.loads(json.dumps(GOOD))]  # 1: invalid, 2: ok
        ex._call_api = lambda *a: seq.pop(0)
        assert ex.extract_event("alt text", "mentenanta", "2026-09-14")["tip"] == "activ_inlocuit"
        assert not seq

        ex._call_api = lambda *a: dict(GOOD, tip="inventat")  # mereu invalid
        try:
            ex.extract_event("al treilea text", "mentenanta", "2026-09-14")
            raise AssertionError("trebuia ValueError")
        except ValueError:
            pass
        for bad in ("(din text)", None, "14.09.2026", "2026-13-40"):  # data invalidă de la model
            ex._call_api = lambda *a, bad=bad: dict(GOOD, data=bad, campuri_lipsa=[])
            ev = ex.extract_event(f"fără dată {bad}", "investitii", None)
            assert ev["data"] == date.today().isoformat() and "data" in ev["campuri_lipsa"], bad
        ex._call_api = lambda *a: dict(GOOD, data="2026-08-05", campuri_lipsa=[])
        ev = ex.extract_event("dată în text", "investitii", None)
        assert ev["data"] == "2026-08-05" and "data" not in ev["campuri_lipsa"]
    print("OK: validare schema, cache hit, reîncercare, eroare după reîncercare")


if __name__ == "__main__":
    main()
