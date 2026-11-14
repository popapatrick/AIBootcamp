"""Test offline etapa 3: python -m backend.extract.test_extract (fără API, fără rețea)."""
import json
import os
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
    os.environ.pop("EXTRACT_ALLOW_API", None)
    os.environ["EXTRACT_CLI"] = "0"  # fără Claude headless real în teste (laptopul poate fi autentificat)
    with tempfile.TemporaryDirectory() as tmp:  # implicit: cache miss -> CacheMiss, fără apel API
        ex.CACHE_DIR = Path(tmp)
        ex._call_api = lambda *a: (_ for _ in ()).throw(AssertionError("apel API fără EXTRACT_ALLOW_API"))
        try:
            ex.extract_event(TEXT, "mentenanta", "2026-09-14")
            raise AssertionError("trebuia CacheMiss")
        except ex.CacheMiss:
            pass
    assert ex.cache_key("t", "s", "d") == ex.hashlib.sha256(f"{ex.CACHE_TAG}{ex.SYSTEM}sdt".encode()).hexdigest()
    m = ex.MODEL
    ex.MODEL = "altul"
    assert ex.cache_key("t", "s", "d") == ex.hashlib.sha256(f"agent-haiku{ex.SYSTEM}sdt".encode()).hexdigest()  # fără MODEL
    ex.MODEL = m
    os.environ["EXTRACT_ALLOW_API"] = "1"  # restul testelor: calea de producție cu API mock
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

        # metoda_cod: API la miss, cache la hit (event identic, fără metoda în el)
        ev1, m1 = ex.extract_event_cu_metoda("text metoda", "mentenanta", "2026-09-14")
        ev2, m2 = ex.extract_event_cu_metoda("text metoda", "mentenanta", "2026-09-14")
        assert (m1, m2) == ("ai_api", "ai_cache") and ev1 == ev2 and "metoda" not in ev1 and len(calls) == 2

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
        ev = ex.extract_event("dată în text 05.08.2026", "investitii", None)
        assert ev["data"] == "2026-08-05" and "data" not in ev["campuri_lipsa"]
    # data inventată de model: păstrată doar dacă apare în text; data apelantului neatinsă
    with tempfile.TemporaryDirectory() as tmp:
        ex.CACHE_DIR = Path(tmp)
        azi = date.today().isoformat()
        ex._call_api = lambda *a: dict(GOOD, data="2025-01-01", campuri_lipsa=[])
        ev = ex.extract_event("Am înlocuit cablul pe A-T-002.", "mentenanta", None)
        assert ev["data"] == azi and "data" in ev["campuri_lipsa"], ev["data"]
        ev = ex.extract_event("Am înlocuit cablul pe A-T-002.", "mentenanta", None)  # cache hit
        assert ev["data"] == azi and "data" in ev["campuri_lipsa"]
        ex._call_api = lambda *a: dict(GOOD, data="2026-09-14", campuri_lipsa=[])
        for t in ("Lucrare din 14.09.2026.", "Lucrare din 14 septembrie 2026.", "Lucrare 14/9/2026."):
            ev = ex.extract_event(t, "mentenanta", None)
            assert ev["data"] == "2026-09-14" and "data" not in ev["campuri_lipsa"], t
        ex._call_api = lambda *a: dict(GOOD, data="2025-01-01", campuri_lipsa=[])
        assert ex.extract_event("fără dată apelant", "mentenanta", "2026-03-03")["data"] == "2026-03-03"
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
        key = ex.cache_key(t, "racordari", "2026-09-01")
        cached = dict(GOOD, event_id="EV-X", echipa_sursa="racordari", text_original=t, data="2026-09-01",
                      campuri_lipsa=["sectiune_cablu"], detalii={})
        (Path(tmp) / f"{key}.json").write_text(json.dumps(cached), encoding="utf-8")
        ex._call_api = lambda *a: (_ for _ in ()).throw(AssertionError("apel API pe cache hit"))
        ev = ex.extract_event(t, "racordari", "2026-09-01")
        assert ev["detalii"]["sectiune_noua"] == "TYIR 3x50+54,6 OL-Al" and ev["campuri_lipsa"] == []
        assert json.loads((Path(tmp) / f"{key}.json").read_text(encoding="utf-8")) == ev
    assert "necartat" in ex.SYSTEM and "racord_nou = doar" in ex.SYSTEM  # regula nod_lipsa vs racord_nou
    # tipuri sesiunea 2: ieșiri schema-valide trec; invalide (decizie/enum) cad
    NOU = dict(GOOD, detalii={}, campuri_lipsa=[])
    cazuri = {
        "mutare_fire": dict(NOU, tip="mutare_fire", referinta={"element_id": None, "coordonate": {"lat": 44.2799, "lon": 26.0594}},
                            detalii={"centru": {"lat": 44.2799, "lon": 26.0594}, "raza_m": 60, "motiv_mutare": "sens_giratoriu"}),
        "mutare_fire fără raza": dict(NOU, tip="mutare_fire", detalii={"centru": {"lat": 44.2853, "lon": 26.0712}, "raza_m": None, "motiv_mutare": "sens_giratoriu"}, campuri_lipsa=["raza_m"]),
        "cerere_racordare": dict(NOU, tip="cerere_racordare", status="planificat", referinta={"element_id": None, "coordonate": {"lat": 44.281, "lon": 26.0618}}),
        "apel_client": dict(NOU, echipa_sursa="apel_client", tip="avarie_semnalata", status="semnalat", tip_sursa_pondere="apel_client",
                            referinta={"element_id": None, "coordonate": None, "id_client": "CL-51001", "adresa": "Strada Orhideelor"}),
        "decizie om": dict(NOU, echipa_sursa="om_teren", tip="verificare", tip_sursa_pondere="om_teren", referinta={"element_id": "NOU-0001"},
                           detalii={"decizie": {"tinta_id": "NOU-0001", "decizie": "accepta", "motiv": "stâlp văzut"}}),
    }
    with tempfile.TemporaryDirectory() as tmp:
        ex.CACHE_DIR = Path(tmp)
        for nume, out in cazuri.items():
            ex._call_api = lambda *a, out=out: json.loads(json.dumps(out))
            ev = ex.extract_event(f"text {nume}", out["echipa_sursa"], "2026-11-14")
            assert ev["tip"] == out["tip"] and ev["echipa_sursa"] == out["echipa_sursa"], nume
        assert ev["detalii"]["decizie"]["tinta_id"] == "NOU-0001"
        ex._call_api = lambda *a: dict(NOU, tip="mutare_fire", detalii={"centru": {"lat": 1}})  # centru fără lon
        try:
            ex.extract_event("centru incomplet", "mentenanta", "2026-11-14")
            raise AssertionError("trebuia ValueError")
        except ValueError:
            pass
        ex._call_api = lambda *a: dict(NOU, echipa_sursa="om_teren", detalii={"decizie": {"tinta_id": "NOU-1", "decizie": "poate"}})
        try:
            ex.extract_event("decizie invalidă", "om_teren", "2026-11-14")
            raise AssertionError("trebuia ValueError")
        except ValueError:
            pass
    # fill_cache --import: dus-întors în cache temporar, apoi extract_event fără API
    from backend.extract import fill_cache as fc
    os.environ.pop("EXTRACT_ALLOW_API", None)
    with tempfile.TemporaryDirectory() as tmp:
        ex.CACHE_DIR = Path(tmp)
        items = [{"text": TEXT, "sursa": "mentenanta", "data": "2026-09-14", "event": json.loads(json.dumps(GOOD))},
                 {"text": "rău", "sursa": "mentenanta", "data": "2026-09-14", "event": dict(GOOD, tip="inventat")}]
        assert fc.importa(items) == (1, 1)
        ev = ex.extract_event(TEXT, "mentenanta", "2026-09-14")  # din cache, fără API
        assert ev["text_original"] == TEXT and ev["event_id"].startswith("EV-")
        try:
            ex.extract_event("rău", "mentenanta", "2026-09-14")
            raise AssertionError("trebuia CacheMiss")
        except ex.CacheMiss:
            pass
        assert "Sursa: mentenanta" in ex.user_message(TEXT, "mentenanta", None) and ex.tool_schema()["type"] == "object"
    # adresa_structurata: schema o acceptă (tool schema) și respinge chei de alt tip
    assert "adresa_structurata" in ex.tool_schema()["properties"]["referinta"]["properties"]
    ev_a = json.loads(json.dumps(GOOD))
    ev_a["referinta"].update(element_id=None, adresa="Strada Liviu Rebreanu nr. 12",
                             adresa_structurata={"strada": "Strada Liviu Rebreanu", "numar": "12", "localitate": None, "reper": None})
    assert not list(ex._validator.iter_errors(ev_a))
    ev_a["referinta"]["adresa_structurata"]["numar"] = 12
    assert list(ex._validator.iter_errors(ev_a))
    assert "adresa_structurata" in ex.SYSTEM and "incredere_extractie după" in ex.SYSTEM
    geo = json.loads((ex.ROOT / "data" / "reports" / "geo-test.json").read_text(encoding="utf-8"))["adrese"]
    assert len(geo) >= 10 and all({"id", "text", "sursa", "data", "asteptat"} <= set(x) for x in geo)
    # forma exemple-dummy.json
    dummy = json.loads((ex.ROOT / "data" / "reports" / "exemple-dummy.json").read_text(encoding="utf-8"))
    assert {"mentenanta", "investitii", "racordari", "apel_client", "om_teren"} <= set(dummy)
    ids = set()
    for sursa, lista in dummy.items():
        assert sursa in ("om_teren",) or len(lista) >= 4, sursa
        for x in lista:
            assert set(x) == {"id", "titlu", "text", "data", "asteptat"} and set(x["asteptat"]) == {"tip", "element_id", "nota"}, x["id"]
            assert x["id"] not in ids and date.fromisoformat(x["data"]); ids.add(x["id"])
    print("OK: validare schema, cache hit, reîncercare, eroare după reîncercare, sectiune_noua din regex (cache hit, variante, vechi)")


if __name__ == "__main__":
    main()
