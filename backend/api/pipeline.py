"""Pipeline-ul pentru `POST /rapoarte` (proprietar C). Date FICTIVE.

text -> extracție -> potrivire -> (predicție) -> scor, întors ca StepTrace (contracts/interfaces.md).

- Extracție: `extract_event` al lui A dacă există; altfel extracție stub cu regex, care NU inventează:
  ce nu găsește intră în `campuri_lipsa`.
- Restul: `apply_event` al lui B dacă există; altfel `match_event` real (etapa 4) + scor PROVIZORIU
  calculat cu aceleași ponderi din contracts/weights.yaml, marcat clar „provizoriu".
"""
from __future__ import annotations

import re
from datetime import date

import yaml

from backend.api import sources

_live: list[dict] = []          # rapoarte procesate în sesiunea curentă (mod stub/parțial)
_counter = [0]

RE_TRONSON = re.compile(r"\b([ARS]-T-\d{1,4})\b")
RE_TRONSON_SCURT = re.compile(r"(?<![A-Z]-)\b(T-\d{1,4})\b")
RE_NOD = re.compile(r"(?<![\d.,])(\d{7})(?![\d]|[.,]\d)")  # nu prinde cifre din coordonate
RE_COORD = re.compile(r"(-?\d{1,2}[.,]\d{3,})\s*[,;/ ]\s*(-?\d{1,2}[.,]\d{3,})")
RE_DATA = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b|\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b")
RE_CADASTRAL = re.compile(r"(?:nr\.?\s*)?cadastral\w*\s*[:\-]?\s*(\d{3,})", re.I)
RE_ADRESA = re.compile(r"\b((?:str\.|strada|șos\.|sos\.|bd\.|aleea)\s+[^,.;\n]+(?:\s*,?\s*nr\.?\s*\d+\w?)?)",
                       re.I)
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
    if sursa == "apel_client":
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
            data = date.today().isoformat()

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
        "detalii": {"sectiune_noua": sec.group(1).strip()} if sec else {},
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


def proceseaza(text: str, sursa: str, data: str | None = None) -> dict:
    """Rulează pipeline-ul pe un raport nou; întoarce StepTrace.

    Exemplu: proceseaza("Stâlp nou la 44.2847, 26.0606", "mentenanta")
    -> {"event_id": "EV-LIVE-001", "pasi": [...4 pași...], "modificari": [...], "mod": {...}}
    """
    ext = sources.extract_func()
    if ext:
        try:
            ev = ext(text, sursa, data)
            metoda_ext = "claude (A)"
        except Exception as e:  # cheie lipsă, rețea, ValueError: demo-ul nu pică
            ev = extract_stub(text, sursa, data)
            metoda_ext = f"stub_regex (rezervă: {type(e).__name__})"
            ev["metoda_extractie"] = metoda_ext
    else:
        ev = extract_stub(text, sursa, data)
        metoda_ext = ev.get("metoda_extractie")

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
