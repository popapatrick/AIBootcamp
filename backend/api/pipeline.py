"""Pipeline-ul pentru `POST /rapoarte` (proprietar C). Date FICTIVE.

text -> extracție -> potrivire -> (predicție) -> scor, întors ca StepTrace (contracts/interfaces.md).

- Extracție: `extract_event` al lui A dacă există; altfel extracție stub cu regex, care NU inventează:
  ce nu găsește intră în `campuri_lipsa`.
- Restul: `apply_event` al lui B dacă există; altfel `match_event` real (etapa 4) + scor PROVIZORIU
  calculat cu aceleași ponderi din contracts/weights.yaml, marcat clar „provizoriu".
"""
from __future__ import annotations

import os
import re
from datetime import date

import yaml

from backend.api import prezentare, sources
from backend.racordare import LocalizareEroare, locatie_operator_demo


def data_demo() -> str:
    """Data de rezervă (raport fără `data` și fără dată în text): `DEMO_DATA` din env, implicit 2026-11-15.
    Fixă, ca cheia de cache (text+echipă+dată) să se potrivească indiferent de ziua demo-ului."""
    return os.environ.get("DEMO_DATA") or "2026-11-15"

try:
    from backend.extract import CacheMiss
except Exception:  # extracția lui A lipsește: nu va fi ridicată oricum
    class CacheMiss(Exception):  # type: ignore[no-redef]
        pass

_live: list[dict] = []          # rapoarte procesate în sesiunea curentă (mod stub/parțial)
_counter = [0]
evente_live: dict[str, dict] = {}   # event_id -> Event (cu text_original) pentru GET /evenimente

RE_TRONSON = re.compile(r"\b([ARS]-T-\d{1,4})\b")
RE_TRONSON_SCURT = re.compile(r"(?<![A-Z]-)\b(T-\d{1,4})\b")
RE_NOD = re.compile(r"(?<![\d.,])(\d{7})(?![\d]|[.,]\d)")  # nu prinde cifre din coordonate
RE_COORD = re.compile(r"(-?\d{1,2}[.,]\d{3,})\s*[,;/ ]\s*(-?\d{1,2}[.,]\d{3,})")
RE_DATA = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b|\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b")
RE_CADASTRAL = re.compile(r"(?:nr\.?\s*)?cadastral\w*\s*[:\-]?\s*(\d{3,})", re.I)
RE_ADRESA = re.compile(r"\b((?:str\.|strada|șos\.|sos\.|bd\.|aleea)\s+(?:(?!\bnr\b|\bnum[ăa]rul\b)[^,.;\n])+(?:(?:nr\.?|num[ăa]rul)\s*\d+[A-Za-z]?)?)",
                       re.I)
RE_CERERE_RACORDARE = re.compile(r"^\s*cerere racordare\s*:", re.I)
RE_FIRE_MUTATE = re.compile(r"^\s*fire mutate\s*:\s*(?P<motiv>[^,]+?)\s*,\s*centru\b", re.I)
RE_TABLETA = re.compile(r"^\s*raport tablet[ăa]\s*:\s*(?:control pe|st[âa]lp nou necartat pe)\b", re.I)
RE_CLIENT = re.compile(r"\b(?:client|cod client|id client)\s*[:\-]?\s*([A-Z0-9-]{4,})", re.I)

TIPURI = [  # (cuvinte cheie, tip, status implicit)
    (("nu am curent", "fără curent", "fara curent", "avarie", "pană", "pana de"), "avarie_semnalata", "semnalat"),
    (("înlocuit", "inlocuit", "schimbat cablul", "înlocuire", "inlocuire"), "activ_inlocuit", "executat"),
    (("racord", "branșament", "bransament"), "racord_nou", "executat"),
    (("planificat", "se va", "proiect", "urmează", "urmeaza"), "linie_planificata", "planificat"),
    (("lipsă", "lipsa", "nu apare", "nu e în gis", "nu este in gis", "stâlp nou", "stalp nou"),
     "nod_lipsa", "executat"),
    (("verificat", "inspecție", "inspectie", "conform cu", "corespunde"), "verificare", "executat"),  # ultimul
]


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def extract_stub(text: str, sursa: str, data: str | None) -> dict:
    """Extracție de rezervă, fără Claude. Nu inventează; ce lipsește merge în campuri_lipsa.

    Exemplu: extract_stub("Am înlocuit cablul pe A-T-002", "investitii", "2026-10-01")
    -> {"tip": "activ_inlocuit", "referinta": {"element_id": "A-T-002", ...}, ...}
    """
    low = text.lower()
    lipsa: list[str] = []
    ref: dict = {"element_id": None, "coordonate": None, "adresa": None, "nr_cadastral": None,
                 "id_client": None}
    m = RE_TRONSON.search(text) or RE_TRONSON_SCURT.search(text) or RE_NOD.search(text)
    if m:
        ref["element_id"] = m.group(1)
    c = RE_COORD.search(text)
    if c:
        ref["coordonate"] = {"lat": _num(c.group(1)), "lon": _num(c.group(2))}
    a = RE_ADRESA.search(text)
    if a:
        ref["adresa"] = a.group(1).strip()
    k = RE_CADASTRAL.search(text)
    if k:
        ref["nr_cadastral"] = k.group(1)
    if sursa == "apel_client":
        cl = RE_CLIENT.search(text)
        ref["id_client"] = cl.group(1) if cl else None
    for camp in ("element_id", "coordonate", "adresa"):
        if ref[camp] is None:
            lipsa.append(f"referinta.{camp}")

    tip, status = None, None
    detalii: dict = {}
    fm = RE_FIRE_MUTATE.match(text)
    if RE_CERERE_RACORDARE.match(text):   # textele fixe ale butoanelor UI (C5-C7), fără AI
        tip, status = "cerere_racordare", "planificat"
    elif fm and ref["coordonate"]:
        tip, status = "mutare_fire", "executat"
        motiv = fm.group("motiv").strip()
        detalii = {"centru": ref["coordonate"],
                   "motiv_mutare": "sens_giratoriu" if "giratoriu" in motiv.lower() else motiv}
        lipsa.append("raza_m")   # textul nu o dă; motorul folosește raza implicită
    elif RE_TABLETA.match(text):   # localizarea vine din trace (detalii.trace), nu din text
        tip, status = "nod_lipsa", "executat"
        lipsa.append("coordonate")
    elif sursa == "apel_client":
        tip, status = "avarie_semnalata", "semnalat"
    else:
        for cuvinte, t, s in TIPURI:
            if any(w in low for w in cuvinte):
                tip, status = t, s
                break
    if tip is None:
        lipsa.append("tip")
        tip, status = "avarie_semnalata", "semnalat"   # cel mai slab efect; marcat lipsă mai sus

    if not data:
        d = RE_DATA.search(text)
        if d:
            data = d.group(1) or f"{d.group(4)}-{int(d.group(3)):02d}-{int(d.group(2)):02d}"
        else:
            lipsa.append("data")
            data = data_demo()

    sec = re.search(r"(TYIR\s*[\dx+,\s]+OL-Al|NA2XS?\w*\s*[\dx]+)", text)
    gasite = sum(ref[k] is not None for k in ("element_id", "coordonate", "adresa"))
    incredere = round(min(0.6, 0.2 + 0.15 * gasite + (0.1 if "tip" not in lipsa else 0)), 2)
    _counter[0] += 1
    return {
        "event_id": f"EV-LIVE-{_counter[0]:03d}",
        "echipa_sursa": sursa,
        "tip": tip,
        "referinta": ref,
        "status": status,
        "data": data,
        "forma_sursa": "text_liber",
        "tip_sursa_pondere": "apel_client" if sursa == "apel_client" else "text_liber",
        "text_original": text,
        "incredere_extractie": incredere,
        "campuri_lipsa": lipsa,
        "detalii": detalii or ({"sectiune_noua": sec.group(1).strip()} if sec else {}),
        "metoda_extractie": "stub_regex (fără Claude)",
    }


def _weights() -> dict:
    return yaml.safe_load((sources.ROOT / "contracts" / "weights.yaml").read_text(encoding="utf-8"))


def _scor_provizoriu(ev: dict, pot: dict) -> dict:
    """Scor PROVIZORIU, până la etapa 5 a lui B. Folosește aceleași ponderi și praguri din weights.yaml."""
    w = _weights()
    fiab = w["fiabilitate_sursa"].get(ev.get("tip_sursa_pondere", "text_liber"), 0.55)
    inc = ev.get("incredere_extractie", 0.5)
    cal = pot.get("calitate", 0.0) if pot else 0.0
    motive = []
    if pot and pot.get("status") == "potrivit":
        baza = w["scor"]["initial_element_kmz"]
        efect = (w["scor"]["confirmare_teren"] if ev["status"] == "executat" and ev["tip"] != "avarie_semnalata"
                 else w["scor"]["contradictie"]) * fiab
        scor = baza + efect
        motive.append({"text": f"Element {pot['element_id']} din model, scor inițial {baza}", "efect": 0.0})
        motive.append({"text": ("Confirmare din teren" if efect > 0 else "Semnal contradictoriu / avarie")
                               + f" × fiabilitate sursă {fiab}", "efect": round(efect, 3)})
    else:
        p = w["predictie"]
        tot = p["pondere_incredere_extractie"] + p["pondere_calitate_potrivire"]
        cal_eff = cal if pot and pot.get("status") == "absent_din_model" else cal * 0.5
        scor = (p["pondere_incredere_extractie"] * inc + p["pondere_calitate_potrivire"] * max(cal_eff, fiab)) / tot
        motive.append({"text": f"Element nou propus: încredere extracție {inc}, calitate potrivire {cal}, "
                               f"fiabilitate sursă {fiab}", "efect": round(scor, 3)})
    scor = max(w["scor"]["minim"], min(w["scor"]["maxim"], scor))
    pr = w["praguri"]
    nivel = "in_model" if scor >= pr["aplicat"] else ("predictie" if scor >= pr["predictie"] else "de_verificat")
    motive.append({"text": f"Prag aplicare {pr['aplicat']}, prag predicție {pr['predictie']} → {nivel}",
                   "efect": 0.0})
    motive.append({"text": "Scor PROVIZORIU calculat de API (stub), până la motorul de scor al lui B",
                   "efect": 0.0})
    return {"scor_nou": round(scor, 3), "nivel": nivel, "motive": motive}


def locatie_operator(text: str, lat: float | None = None, lon: float | None = None) -> dict:
    """Poziția simulată a operatorului din textul lui (backend.racordare). Ridică LocalizareEroare dacă nu se localizează."""
    from backend.engine import osm
    net = sources.model_net()
    if net is None:
        raise LocalizareEroare("Modelul rețelei nu e disponibil.", [])
    return locatie_operator_demo(text, net, osm.strazi(), _weights(), lat, lon)


def proceseaza(text: str, sursa: str, data: str | None = None, locatie: dict | None = None,
               locatie_operator: dict | None = None) -> dict:
    """Rulează pipeline-ul pe un raport nou; întoarce StepTrace.

    Câmpurile sesiunii 3 produse de motor (`detalii.geocodare`, `trace_sursa`, `origine`, `predictie.slaba/treapta`,
    `eronat_prototip`, `adresa_structurata`) trec neatinse; dacă Event-ul are `detalii.geocodare`, se adaugă pasul „geocodare".
    `locatie_operator` {lat, lon, precizie_m, simulata} (poziție simulată) intră în `detalii.locatie_operator`.
    `locatie` {lat, lon} (clic pe hartă, doar pentru teste) intră în `detalii.locatie`/`detalii.centru` și completează
    `referinta.coordonate` doar dacă extracția nu a găsit coordonate. Răspunsul are mereu `schimbari` (listă; goală
    dacă motorul nu le dă), plus `standardizare` și `focus` (sesiunea 4, vezi `backend/api/prezentare.py`).

    Exemplu: proceseaza("Stâlp nou la 44.2847, 26.0606", "mentenanta")
    -> {"event_id": "EV-LIVE-001", "pasi": [...4 pași...], "modificari": [...], "mod": {...}}
    """
    ext = sources.extract_func()
    cod, motiv = "regex", None
    if ext:
        try:
            data_primirii = False
            data_ext = data
            if not data_ext:
                m = RE_DATA.search(text)
                if m:
                    data_ext = m.group(1) or f"{m.group(4)}-{int(m.group(3)):02d}-{int(m.group(2)):02d}"
                else:  # extract_event cere dată: folosim data primirii raportului
                    data_ext = data_demo()
                    data_primirii = True
            try:   # metoda_cod vine de la extracție: ai_cache | ai_cli (Claude Code din abonament) | ai_api
                from backend.extract import extract_event_cu_metoda
                ev, cod = extract_event_cu_metoda(text, sursa, data_ext)
                ev = dict(ev)  # copie: nu atingem cache-ul din memorie
            except ImportError:
                hit = sources.cache_hit(text, sursa, data_ext)
                ev = dict(ext(text, sursa, data_ext))
                cod = "ai_cache" if hit else "ai_api"
            _counter[0] += 1
            if ev.get("event_id") != f"EV-LIVE-{_counter[0]:03d}":
                ev["event_id_extractie"] = ev.get("event_id")
            ev["event_id"] = f"EV-LIVE-{_counter[0]:03d}"  # ID unic de sesiune
            metoda_ext = "claude (A)"
            if data_primirii:
                metoda_ext = "claude (A), data = data primirii"
                lipsa = ev.setdefault("campuri_lipsa", [])
                if not any(str(x).startswith("data (") for x in lipsa):
                    lipsa.append("data (folosită data primirii raportului)")
        except CacheMiss:  # text nou, fără cache și fără API permis
            ev = extract_stub(text, sursa, data)
            metoda_ext = "stub_regex (text nou, fără cache)"
            motiv = "text nou, fără cache: extracție simplificată (regex)"
            ev["metoda_extractie"] = metoda_ext
            cod = "regex"
        except Exception as e:  # cheie lipsă, rețea, ValueError: demo-ul nu pică
            ev = extract_stub(text, sursa, data)
            metoda_ext = f"stub_regex (rezervă: {type(e).__name__})"
            motiv = f"extracția AI a eșuat ({type(e).__name__}): extracție simplificată (regex)"
            ev["metoda_extractie"] = metoda_ext
            cod = "regex"
    else:
        ev = extract_stub(text, sursa, data)
        metoda_ext = ev.get("metoda_extractie")

    if locatie_operator:   # doar indiciu: NU intră în referinta.coordonate (motorul îl pune ultimul și îl marchează simulat)
        ev.setdefault("detalii", {})["locatie_operator"] = locatie_operator
    if locatie:
        det = ev.setdefault("detalii", {})
        det["locatie"] = det["centru"] = locatie
        ref = ev.setdefault("referinta", {})
        if not ref.get("coordonate"):
            ref["coordonate"] = locatie

    out = _ruleaza(ev, metoda_ext)
    _pas_geocodare(ev, out)
    pas = next((p for p in out["pasi"] if p.get("nume") == "extractie"), None)
    if pas is not None:
        pas["metoda_cod"] = cod
        if motiv:
            pas["motiv"] = motiv
    out.setdefault("schimbari", [])   # nu inventăm: [] dacă motorul nu le dă (B3)
    out.setdefault("ultima_actualizare", sources.ultima_actualizare(ev["data"]))
    evente_live[ev["event_id"]] = ev
    out["standardizare"] = prezentare.standardizare(ev, out, cod)
    out["focus"] = prezentare.focus(ev, out)
    return out


def _pas_geocodare(ev: dict, out: dict) -> None:
    """Adaugă pasul „geocodare” (după extracție) dacă Event-ul sau pasul de extracție poartă `detalii.geocodare`.
    Nu inventează: fără `detalii.geocodare` (motorul nu a geocodat) nu se adaugă nimic."""
    pasi = out.get("pasi", [])
    if any(p.get("nume") == "geocodare" for p in pasi):
        return
    pe = next((p for p in pasi if p.get("nume") == "extractie"), None)
    surse = [ev] + ([pe["rezultat"]] if pe and isinstance(pe.get("rezultat"), dict) else [])
    geo = next((g for e in surse if isinstance((g := (e.get("detalii") or {}).get("geocodare")), dict)), None)
    if geo is None:
        return
    i = pasi.index(pe) + 1 if pe in pasi else 0
    pasi.insert(i, {"nume": "geocodare", "rezultat": geo, "incredere": geo.get("acuratete")})


def _ruleaza(ev: dict, metoda_ext: str) -> dict:
    """Aplică Event-ul: motorul real dacă există, altfel potrivire + scor provizoriu."""
    apply = sources.engine_func("apply_event")
    if apply:
        trace = apply(ev)
        # Ecranul procesului arată Event-ul complet (B întoarce doar un rezumat al extracției).
        pas_ext = {"nume": "extractie", "rezultat": ev, "incredere": ev.get("incredere_extractie"),
                   "metoda": metoda_ext}
        trace["pasi"] = [pas_ext] + [p for p in trace.get("pasi", []) if p.get("nume") != "extractie"]
        trace["mod"] = {**sources.mod(), "extractie_metoda": metoda_ext}
        return trace

    pasi = [{"nume": "extractie", "rezultat": ev, "incredere": ev.get("incredere_extractie"),
             "metoda": metoda_ext}]
    match = sources.engine_func("match_event")
    net = sources.model_net()
    pot = match(ev, net) if match and net else None
    pasi.append({"nume": "potrivire", "rezultat": pot or {"status": "nepotrivit", "motiv": "motor indisponibil"},
                 "incredere": pot.get("calitate") if pot else 0.0})

    pred = None
    if pot and pot["status"] == "absent_din_model" and pot.get("coordonate_folosite"):
        pred = {"metoda": "punct_raportat", "urmeaza_strada": None,
                "nota": "Traseul (OSM / linie dreaptă) îl calculează motorul lui B; aici doar punctul raportat."}
        pasi.append({"nume": "predictie", "rezultat": pred, "incredere": None})

    sc = _scor_provizoriu(ev, pot)
    pasi.append({"nume": "scor", "rezultat": {"scor_nou": sc["scor_nou"], "nivel": sc["nivel"]},
                 "motive": [m["text"] for m in sc["motive"]]})

    modificari = []
    eid = pot.get("element_id") if pot and pot.get("status") == "potrivit" else f"PRED-{ev['event_id']}"
    tip_el = ("tronson" if "-T-" in eid else "post_transformare" if eid.startswith("DX") else "nod")
    stare = {"element_id": eid, "tip_element": tip_el,
             "nivel": sc["nivel"], "scor": sc["scor_nou"], "valid_de_la": ev["data"], "ultima_verificare":
             ev["data"] if ev["status"] == "executat" else None,
             "motive": [{**m, "eveniment": ev["event_id"], "data": ev["data"]} for m in reversed(sc["motive"])],
             "predictie": pred if sc["nivel"] == "predictie" else None}
    modificari.append(stare)

    coords = pot.get("coordonate_folosite") if pot else None
    _live.append({"event": ev, "stare": stare, "coordonate": coords})
    return {"event_id": ev["event_id"], "pasi": pasi, "modificari": modificari,
            "mod": {**sources.mod(), "extractie_metoda": metoda_ext}}


def live_evenimente() -> list[dict]:
    """Rapoartele procesate în sesiune, în formatul timeline-ului."""
    return [{"data": x["event"]["data"], "event_id": x["event"]["event_id"],
             "rezumat": f"[live] {x['event']['tip']}: {x['event']['text_original'][:60]}",
             "elemente_atinse": [x["stare"]["element_id"]], "live": True} for x in _live]


def live_overlay(fc: dict, data: str | None) -> dict:
    """Suprapune pe GeoJSON rapoartele live (doar în mod stub/parțial; motorul real le aplică singur)."""
    if not _live or sources.engine_func("apply_event"):
        return fc
    feats = list(fc.get("features", []))
    index = {(f.get("properties", {}).get("element_id") or f.get("properties", {}).get("id")): i
             for i, f in enumerate(feats)}
    for x in _live:
        if data and x["event"]["data"] > data:
            continue
        st = x["stare"]
        if st["element_id"] in index:
            i = index[st["element_id"]]
            f = feats[i]
            pr = {**f["properties"], **{k: st[k] for k in ("nivel", "scor", "valid_de_la", "ultima_verificare")}}
            pr["motive"] = st["motive"] + f["properties"].get("motive", [])
            feats[i] = {**f, "properties": pr}
        elif x["coordonate"]:
            c = x["coordonate"]
            feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [c["lon"], c["lat"]]},
                          "properties": {**st, "id": st["element_id"], "live": True}})
    return {**fc, "features": feats}


def live_element(element_id: str) -> dict | None:
    for x in reversed(_live):
        if x["stare"]["element_id"] == element_id:
            c = x["coordonate"]
            return {**x["stare"], "geometry": {"type": "Point", "coordinates": [c["lon"], c["lat"]]} if c else None,
                    "istoric": [{"data": x["event"]["data"], "nivel": x["stare"]["nivel"],
                                 "scor": x["stare"]["scor"], "motive": x["stare"]["motive"]}]}
    return None


_dec_counter = [0]


class DecizieEroare(Exception):
    """Motorul a refuzat decizia; `cod` = trace.eroare.cod (deja_decis | necunoscut | decizie_invalida)."""

    def __init__(self, cod: str, mesaj: str):
        super().__init__(mesaj)
        self.cod = cod


def decizie(tinta_id: str, decizie: str, motiv: str | None, data: str | None) -> dict:
    """Decizia omului asupra unei predicții: Event `verificare`/`om_teren` dat lui `apply_event` (B4).

    Întoarce StepTrace-ul (cu `schimbari`). Ridică DecizieEroare dacă motorul pune `trace.eroare`;
    NotImplementedError dacă motorul nu e disponibil (stub).
    """
    apply = sources.engine_func("apply_event")
    if not apply:
        raise NotImplementedError("decizia cere motorul real (apply_event)")
    _dec_counter[0] += 1
    ev = {"event_id": f"EV-DEC-{_dec_counter[0]:03d}", "echipa_sursa": "om_teren", "tip": "verificare",
          "referinta": {}, "status": "executat", "data": data or date.today().isoformat(),
          "forma_sursa": "campuri", "tip_sursa_pondere": "om_teren",
          "text_original": f"Decizie om: {decizie} {tinta_id}", "incredere_extractie": 1.0,
          "campuri_lipsa": [], "detalii": {"decizie": {"tinta_id": tinta_id, "decizie": decizie, "motiv": motiv}}}
    out = apply(ev)
    err = out.get("eroare")
    if err:
        raise DecizieEroare(err["cod"], err.get("mesaj", ""))
    out["mod"] = sources.mod()
    out.setdefault("schimbari", [])
    return out


class ElementLipsa(Exception):
    """Elementul cerut nu există (-> 404)."""


class FaraSuport(NotImplementedError):
    """Motorul nu știe încă evenimentul cerut (-> 501)."""


def _motorul_stie_verificare_om() -> bool:
    """True dacă codul motorului tratează `verificare_om` (V5). Căutare în sursele din backend/engine."""
    return any("verificare_om" in p.read_text(encoding="utf-8") for p in (sources.ROOT / "backend" / "engine").glob("*.py")
               if not p.name.startswith(("smoke", "test", "verifica")))


def verificare(element_id: str, motiv: str | None = None, data: str | None = None) -> dict:
    """Marchează un element verificat de om: Event `verificare_om` (om_teren) dat lui `apply_event`. Întoarce StepTrace.

    Ridică ElementLipsa (404) dacă elementul nu există; FaraSuport (501) dacă motorul nu are încă `verificare_om`.
    """
    if live_element(element_id) is None and sources.element(element_id) is None:
        raise ElementLipsa(f"element necunoscut: {element_id}")
    apply = sources.engine_func("apply_event")
    if not apply or not _motorul_stie_verificare_om():
        raise FaraSuport("verificare_om nu e încă în motor (V5, Victor)")
    _dec_counter[0] += 1
    ev = {"event_id": f"EV-VER-{_dec_counter[0]:03d}", "echipa_sursa": "om_teren", "tip": "verificare_om",
          "referinta": {"element_id": element_id}, "status": "executat", "data": data or date.today().isoformat(),
          "forma_sursa": "campuri", "tip_sursa_pondere": "om_teren", "incredere_extractie": 1.0,
          "text_original": f"Verificat de om: {element_id}" + (f" ({motiv})" if motiv else ""), "campuri_lipsa": [],
          "detalii": {"tinta_id": element_id, "motiv": motiv}}
    out = apply(ev)
    out["mod"] = sources.mod()
    out.setdefault("schimbari", [])
    evente_live[ev["event_id"]] = ev
    out["standardizare"] = prezentare.standardizare(ev, out, None)
    out["focus"] = prezentare.focus(ev, out)
    return out


class StergereEroare(Exception):
    """Motorul a refuzat ștergerea; `cod` = trace.eroare.cod (nu_se_sterge_retea_start | deja_sters | necunoscut)."""

    def __init__(self, cod: str, mesaj: str):
        super().__init__(mesaj)
        self.cod = cod


def stergere(element_id: str, motiv: str | None = None, data: str | None = None) -> dict:
    """Un om șterge un element adăugat de sistem: Event `stergere_om` (om_teren) dat lui `apply_event`. Întoarce StepTrace
    (`decizie: sters`, `stergere {tinta_id, elemente[], n, motiv}`). Ridică StergereEroare dacă motorul refuză (-> 409/404);
    FaraSuport dacă motorul real lipsește (-> 501)."""
    apply = sources.engine_func("apply_event")
    if not apply:
        raise FaraSuport("ștergerea cere motorul real (apply_event)")
    _dec_counter[0] += 1
    ev = {"event_id": f"EV-STG-{_dec_counter[0]:03d}", "tip": "stergere_om", "echipa_sursa": "om_teren",
          "data": data or date.today().isoformat(), "text_original": f"Șters de om: {element_id}" + (f" ({motiv})" if motiv else ""),
          "detalii": {"tinta_id": element_id, "motiv": motiv}}
    out = apply(ev)
    err = out.get("eroare")
    if err:
        raise StergereEroare(err["cod"], err.get("mesaj", ""))
    out["mod"] = sources.mod()
    out.setdefault("schimbari", [])
    evente_live[ev["event_id"]] = ev
    return out


# --- Tracking echipe (sesiunea 4b): turele generate în sesiune, în memorie; `reset()` le șterge ---
_ture: dict[str, dict] = {}        # tura_id -> {tura, aplicata}
ECHIPE_TRACKING = ("mentenanta", "investitii", "racordari")


class TuraLipsa(Exception):
    """tura_id necunoscut (-> 404)."""


def _ture_scenariu() -> dict[str, dict]:
    """Turele din data/events/ture-tracking.json (deja aplicate de scenariu), fără puncte în listă."""
    d = sources.ROOT / "data" / "events" / "ture-tracking.json"
    if not d.exists():
        return {}
    import json
    return {t["tura"]["tura_id"]: t["tura"] for t in json.loads(d.read_text(encoding="utf-8"))}


def _rezumat_tura(t: dict, aplicata: bool) -> dict:
    return {"tura_id": t["tura_id"], "echipa": t["echipa"], "echipa_eticheta": prezentare.eticheta_echipa(t["echipa"]),
            "data": t["data"], "seed": t["seed"], "aplicata": aplicata, "durata_min": t["durata_min"],
            "lungime_m": t["lungime_m"], "n_puncte": len(t["puncte"])}


def tracking_genereaza(echipa: str, seed: str | None = None, data: str | None = None) -> dict:
    """Generează (fără să schimbe modelul) o tură simulată cu `backend.tracking.genereaza_tura`, cu scorurile curente
    ale modelului (stâlpi nu-verzi preferați), și o ține în memorie. Ridică ValueError (-> 422) la echipă/dată invalide
    sau tură imposibilă; FaraSuport (-> 501) fără motor real."""
    if echipa not in ECHIPE_TRACKING:
        raise ValueError(f"echipă necunoscută: {echipa}")
    data = data or date.today().isoformat()
    date.fromisoformat(data)
    if sources.engine_func("apply_event") is None:
        raise FaraSuport("tracking cere motorul real")
    from backend.engine import engine as eng, osm
    from backend.tracking import genereaza_tura
    m = eng.get_model()
    scoruri = {k: v[-1]["scor"] for k, v in m.istoric.items() if v}
    t = genereaza_tura(m.net, osm.strazi(), m.w, echipa, seed or f"{echipa}-{data}", data, scoruri=scoruri)
    t["echipa_eticheta"] = prezentare.eticheta_echipa(echipa)
    _ture[t["tura_id"]] = {"tura": t, "aplicata": False}
    return t


def tracking_ture() -> list[dict]:
    """Turele din sesiune (generate la cerere) și din scenariu, fără puncte: `{tura_id, echipa, data, seed, aplicata, ...}`."""
    sc = _ture_scenariu()
    out = [_rezumat_tura(t, True) for i, t in sc.items() if i not in _ture]
    out += [_rezumat_tura(x["tura"], x["aplicata"]) for x in _ture.values()]
    return sorted(out, key=lambda r: (r["data"], r["tura_id"]))


def _t_sec(tura: dict, iso: str | None) -> int | None:
    from datetime import datetime
    if not iso or not tura.get("puncte"):
        return None
    return round((datetime.fromisoformat(iso) - datetime.fromisoformat(tura["puncte"][0]["t"])).total_seconds())


def tracking_aplica(tura_id: str | None, tura: dict | None, data: str | None = None) -> dict:
    """Aplică o tură în model: Event `tracking_tura` (`tracking_gps`) dat lui `apply_event`. Întoarce StepTrace plus
    `tracking[]` (opririle, cu `t_ajungere` în secunde de la începutul turei și `eticheta`) și `focus` (bbox-ul turei).
    Ridică TuraLipsa (-> 404) la tura_id necunoscut, ValueError (-> 422) fără tura_id și fără tura, FaraSuport (-> 501)."""
    if tura is None:
        if not tura_id:
            raise ValueError("trimite `tura_id` sau `tura`")
        tura = (_ture.get(tura_id) or {}).get("tura") or _ture_scenariu().get(tura_id)
        if tura is None:
            raise TuraLipsa(f"tură necunoscută: {tura_id}")
    apply = sources.engine_func("apply_event")
    if not apply:
        raise FaraSuport("tracking cere motorul real (apply_event)")
    _dec_counter[0] += 1
    ev = {"event_id": f"EV-TRK-{_dec_counter[0]:03d}", "tip": "tracking_tura", "echipa_sursa": tura["echipa"],
          "tip_sursa_pondere": "tracking_gps", "data": data or tura["data"],
          "text_original": f"Tura de tracking a echipei {tura['echipa']}", "detalii": {"tura": tura}}
    out = apply(ev)
    out["mod"] = sources.mod()
    out.setdefault("schimbari", [])
    pas = next((p for p in out.get("pasi", []) if p.get("nume") == "opriri"), {})
    out["tracking"] = [{**o, "t_ajungere": _t_sec(tura, o.get("inceput")),
                        "eticheta": TIP_OPRIRE.get(o.get("tip"))}
                       for o in (pas.get("rezultat") or {}).get("opriri", [])]
    pts = [(p["lat"], p["lon"]) for p in tura["puncte"]]
    if pts:
        d_lat, d_lon = 30 / 111_000, 30 / 80_000
        b = {"lat_min": min(p[0] for p in pts) - d_lat, "lat_max": max(p[0] for p in pts) + d_lat,
             "lon_min": min(p[1] for p in pts) - d_lon, "lon_max": max(p[1] for p in pts) + d_lon}
        b = {k: round(v, 6) for k, v in b.items()}
        out["focus"] = {"lat": round((b["lat_min"] + b["lat_max"]) / 2, 6), "lon": round((b["lon_min"] + b["lon_max"]) / 2, 6),
                        "zoom": 16, "bbox": b}
    if tura["tura_id"] in _ture and out.get("decizie") != "fara_efect":
        _ture[tura["tura_id"]]["aplicata"] = True
    evente_live[ev["event_id"]] = ev
    return out


TIP_OPRIRE = {"validare": "Stâlp confirmat", "stalp_presupus": "Stâlp presupus", "scurta": "Oprire scurtă",
              "neclara": "Oprire neclară"}


def reset() -> int:
    """Reface modelul la starea de start (motorul reîncarcă evenimentele) și șterge rapoartele live. Întoarce nr. de evenimente."""
    f = sources.engine_func("reset")
    if f is None:
        raise FaraSuport("reset cere motorul real")
    f()
    _live.clear()
    evente_live.clear()
    _ture.clear()
    return len(sources.evenimente())


def imbogateste_evenimente(items: list[dict]) -> list[dict]:
    """Adaugă pe intrările timeline-ului: `text_original`, `echipa`, `standardizare`, `focus`, `banda_inainte`, `banda_dupa`.
    Ce dă deja motorul rămâne neatins; ce nu știm rămâne null."""
    surse = dict(evente_live)
    try:
        from backend.engine import engine as eng
        surse = {**{e["event_id"]: e for e in eng._incarca_evenimente()}, **surse}
    except Exception:
        pass
    idx = prezentare._index_pozitii()
    out = []
    for it in items:
        ev = surse.get(it.get("event_id")) or {}
        e = dict(it)
        e.setdefault("text_original", ev.get("text_original"))
        e.setdefault("echipa", prezentare.eticheta_echipa(ev.get("echipa_sursa")))
        e.setdefault("eticheta_text", prezentare.ETICHETE_TIMELINE.get(e.get("eticheta")))
        sch = e.get("schimbari") or []
        e.setdefault("banda_inainte", (sch[0].get("banda_inainte") if sch else None))
        e.setdefault("banda_dupa", (sch[0].get("banda_dupa") if sch else None))
        if ev:
            o = {"pasi": e.get("pasi") or [], "schimbari": sch, "decizie": e.get("decizie"), "modificari": []}
            e.setdefault("standardizare", prezentare.standardizare(ev, o, None))
            e.setdefault("focus", prezentare.focus(ev, o, idx))
        else:
            e.setdefault("standardizare", None)
            e.setdefault("focus", None)
        out.append(e)
    return out
