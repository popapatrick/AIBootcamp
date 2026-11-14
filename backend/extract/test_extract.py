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
    for txt, det, asteptat in (
        ("Pe A-T-021 este montat conductor TYIR  3x50+54,6 OL-Al.", {}, "TYIR 3x50+54,6 OL-Al"),
        ("TYIR 3x50+54 ; TYIR 3x70+54.", {}, None),
        ("conductor TYIR 3x50+54", {"sectiune_noua": "X"}, "X"),
    ):
        ev = ex._sectiune({"detalii": dict(det), "campuri_lipsa": ["detalii.sectiune_noua"]}, txt)
        assert ev["detalii"].get("sectiune_noua") == asteptat, txt
        assert ("detalii.sectiune_noua" in ev["campuri_lipsa"]) == (asteptat in (None, "X")), txt  # neatins => rămâne
    for txt, det, asteptat in (
        ("Pe tronson s-a montat TYIR 3.5x50 + 54.6 ol-al nou.", {}, None),
        ("Cablul demontat era TYIR 3x35+54.", {}, None),
        ("Cablu vechi scos. Pe A-T-1 este montat NA2XSY 3x150.", {}, "NA2XSY 3x150"),
        ("Conductor TYIR 3x50 + 54.6 OL-AL.", {}, "TYIR 3x50 + 54.6 OL-AL"),
        ("Conductor TYIR 3x50", None, None),  # detalii nu e dict: nu crapă
    ):
        ev = ex._sectiune({"detalii": None if det is None else dict(det)}, txt)
        got = (ev["detalii"] or {}).get("sectiune_noua") if ev["detalii"] else None
        assert got == asteptat or (txt.startswith("Pe tronson") and got == "TYIR 3.5x50 + 54.6 ol-al"), (txt, got)
    ev = ex._sectiune({"detalii": {}, "campuri_lipsa": ["sectiune_cablu", "detalii.sectiune_noua", "sectiune_noua", "adresa"]},
                      "montat TYIR 3x50+54,6 OL-Al")
    assert ev["campuri_lipsa"] == ["adresa"], ev
    # cache hit cap-coadă cu fișier cache fals: completat + rescris pe disc
    with tempfile.TemporaryDirectory() as tmp:
        ex.CACHE_DIR = Path(tmp)
        t = "Pe A-T-021 este montat conductor TYIR 3x50+54,6 OL-Al."
        key = ex.hashlib.sha256(f"{ex.MODEL}{ex.SYSTEM}racordari2026-09-01{t}".encode("utf-8")).hexdigest()
        cached = dict(GOOD, event_id="EV-X", echipa_sursa="racordari", text_original=t, data="2026-09-01",
                      campuri_lipsa=["sectiune_cablu"], detalii={})
        (Path(tmp) / f"{key}.json").write_text(json.dumps(cached), encoding="utf-8")
        ex._call_api = lambda *a: (_ for _ in ()).throw(AssertionError("apel API pe cache hit"))
        ev = ex.extract_event(t, "racordari", "2026-09-01")
        assert ev["detalii"]["sectiune_noua"] == "TYIR 3x50+54,6 OL-Al" and ev["campuri_lipsa"] == []
        assert json.loads((Path(tmp) / f"{key}.json").read_text(encoding="utf-8")) == ev
    print("OK: validare schema, cache hit, reîncercare, eroare după reîncercare, sectiune_noua din regex (cache hit, variante, vechi)")


if __name__ == "__main__":
    main()
