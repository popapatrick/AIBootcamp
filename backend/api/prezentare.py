"""Câmpuri de prezentare pentru UI (sesiunea 4, C2/C3): `standardizare`, `focus`, `legenda`, etichete în română.

Totul se construiește din ce a produs motorul; ce lipsește rămâne null (nu se inventează). Date FICTIVE.
"""
from __future__ import annotations

from backend.api import sources

ECHIPE = {"mentenanta": "Mentenanță", "investitii": "Investiții", "racordari": "Racordări",
          "apel_client": "Apel client", "om_teren": "Om din teren"}
METODE = {"ai_cache": "AI (cache)", "ai_cli": "AI (live)", "ai_api": "AI (live)", "regex": "Regex (simplificat)"}
DECIZII = {"aplicat": "Aplicat în rețea", "scor_actualizat": "Scor actualizat", "predictie": "Propunere (neaplicată)",
           "neaplicat": "Neaplicat", "fara_efect": "Fără efect", "verificare": "Verificat", "conflict": "Conflict marcat",
           "de_verificat": "De verificat"}
BANDE = {"verde": "Sigur", "galben": "Probabil", "portocaliu": "Nesigur", "rosu": "Foarte nesigur"}
_COLORI = {"verde": "#2e9e4f", "galben": "#e6c229", "portocaliu": "#f08a24", "rosu": "#d64545"}
_CAMPURI = [("tip", "Tip eveniment"), ("status", "Stare lucrare"), ("element_id", "Element (ID)"),
            ("adresa", "Adresă"), ("coordonate", "Coordonate"), ("nr_cadastral", "Nr. cadastral"),
            ("id_client", "ID client")]
_SURSE_LOC = {"coordonate": "coordonate din text", "id": "ID element", "adresa_numar": "stradă și număr",
              "intersectie": "intersecție", "strada": "doar strada", "analiza_harta": "analiza hărții", "reper": "reper"}


def eticheta_echipa(echipa: str | None) -> str | None:
    """Eticheta română a echipei sursă (None dacă necunoscută)."""
    return ECHIPE.get(echipa) if echipa else None


def eticheta_origine(origine: str | None) -> str | None:
    """`retea_start` -> „GIS”, `generat_model` -> „Din raport”, altfel None."""
    return {"retea_start": "GIS", "generat_model": "Din raport"}.get(origine)


def _pas(out: dict, nume: str) -> dict:
    return next((p.get("rezultat") or {} for p in out.get("pasi", []) if p.get("nume") == nume), {})


def standardizare(ev: dict, out: dict, cod: str | None = None) -> dict:
    """Panoul „Ce a înțeles AI-ul”: câmpuri (cu `din` text|dedus|lipsa), lipsuri, localizare, decizie.

    `cod` = metoda de extracție (ai_cache|ai_cli|ai_api|regex) dacă o știm (rapoarte live); altfel null.
    `localizare` e null dacă motorul nu a dat niciun pas de localizare (cautare_strada/geocodare) și textul n-are coordonate.
    """
    ref = ev.get("referinta") or {}
    geo = _pas(out, "geocodare")
    campuri = []
    for k, et in _CAMPURI:
        v = ev.get(k) if k in ("tip", "status") else ref.get(k)
        if v is None and k == "coordonate" and geo.get("lat") is not None:
            campuri.append({"camp": k, "valoare": {"lat": geo["lat"], "lon": geo["lon"]}, "eticheta": et, "din": "dedus"})
        elif v is None and k not in ("tip", "status", "adresa", "coordonate", "element_id"):
            continue   # nr. cadastral / id client lipsă nu se afișează
        else:
            campuri.append({"camp": k, "valoare": v, "eticheta": et, "din": "text" if v is not None else "lipsa"})
    lipsa = [str(x).removeprefix("referinta.") for x in ev.get("campuri_lipsa") or []]
    # localizare: pasul cautare_strada (V6) > geocodare (B2) > coordonate din text
    cs, w = _pas(out, "cautare_strada"), sources_weights()
    mod = (out.get("modificari") or [{}])[0]
    sursa = mod.get("sursa_locatie") or (_pas(out, "predictie").get("sursa_locatie"))
    loc = None
    if cs:
        ind = cs.get("indiciu") or {}
        loc = {"sursa": sursa or "adresa_numar", "precizie_m": cs.get("precizie_m"), "metoda": cs.get("metoda"),
               "indiciu": ind.get("text") if isinstance(ind, dict) else ind,
               "text": f"{cs.get('strada')}: fereastră de {round((cs.get('pana_la_m') or 0) - (cs.get('de_la_m') or 0))} m, "
                       f"{len(cs.get('candidati') or [])} găsiți" + (", ales cel mai apropiat" if cs.get("ales") else "")}
    elif geo:
        loc = {"sursa": sursa, "precizie_m": geo.get("precizie_m"), "metoda": geo.get("metoda"), "indiciu": None,
               "text": f"Locație din adresă, ±{geo.get('precizie_m')} m" if geo.get("precizie_m") is not None else "Locație din adresă"}
    elif ref.get("coordonate"):
        loc = {"sursa": sursa or "coordonate", "precizie_m": None, "metoda": "text", "indiciu": None,
               "text": "Coordonate date în text"}
    if loc:
        loc["plafon"] = (w.get("plafon_locatie") or {}).get(loc["sursa"])
    scor = _pas(out, "scor").get("scor_nou", mod.get("scor"))
    dec = out.get("decizie")
    return {"metoda": cod, "metoda_eticheta": METODE.get(cod), "campuri": campuri, "lipsa": lipsa, "localizare": loc,
            "decizie": {"cod": dec, "text": DECIZII.get(dec, dec), "scor": scor, "banda": mod.get("banda")}}


def sources_weights() -> dict:
    """weights.yaml ca dict (cache simplu în pipeline._weights)."""
    from backend.api import pipeline
    return pipeline._weights()


def _coords(geom: dict | None):
    """Toate perechile (lat, lon) dintr-o geometrie GeoJSON (Point/LineString/Multi*)."""
    def rec(c):
        if c and isinstance(c[0], (int, float)):
            yield (c[1], c[0])
        else:
            for x in c or []:
                yield from rec(x)
    return list(rec((geom or {}).get("coordinates")))


def _index_pozitii() -> dict[str, list]:
    """{element_id: [(lat, lon), ...]} din cel mai recent instantaneu."""
    fc = sources.retea(None)
    return {f["properties"].get("element_id"): _coords(f.get("geometry")) for f in fc.get("features", [])}


def focus(ev: dict, out: dict, index: dict | None = None) -> dict | None:
    """Unde să zoomeze harta: bbox-ul elementelor din `schimbari` (+30 m), altfel punctul localizat; None dacă nu avem nimic.

    `{lat, lon, zoom, bbox: {lat_min, lon_min, lat_max, lon_max}}`; zoom 17 (16 la `mutare_fire`).
    Pozițiile vin din instantaneul cel mai recent (un element mutat ulterior apare la poziția nouă).
    """
    index = index if index is not None else _index_pozitii()
    pts = [p for s in out.get("schimbari") or [] for p in index.get(s.get("element_id"), [])]
    if not pts:
        geo = _pas(out, "geocodare")
        c = geo if geo.get("lat") is not None else (ev.get("referinta") or {}).get("coordonate")
        if c and c.get("lat") is not None:
            pts = [(c["lat"], c["lon"])]
    if not pts:
        return None
    d_lat, d_lon = 30 / 111_000, 30 / 80_000   # ~30 m la lat. 44°
    b = {"lat_min": min(p[0] for p in pts) - d_lat, "lat_max": max(p[0] for p in pts) + d_lat,
         "lon_min": min(p[1] for p in pts) - d_lon, "lon_max": max(p[1] for p in pts) + d_lon}
    b = {k: round(v, 6) for k, v in b.items()}
    return {"lat": round((b["lat_min"] + b["lat_max"]) / 2, 6), "lon": round((b["lon_min"] + b["lon_max"]) / 2, 6),
            "zoom": 16 if ev.get("tip") == "mutare_fire" else 17, "bbox": b}


def legenda() -> dict:
    """Legenda hărții: benzile din weights.culori (de_la, culoare, text), stilurile de linie, insignele. Texte în română."""
    c = sources_weights()["culori"]
    benzi = [{"banda": b, "de_la": v, "culoare": _COLORI[b], "text": BANDE[b]}
             for b, v in (("verde", c["verde"]), ("galben", c["galben"]), ("portocaliu", c["portocaliu"]), ("rosu", 0.0))]
    for b, nxt in zip(benzi, [None] + benzi[:-1]):
        b["pana_la"] = nxt["de_la"] if nxt else 1.0
    return {"benzi": benzi,
            "linii": [{"stil": "plina", "text": "În rețea"}, {"stil": "punctata", "text": "Predicție (neaplicată)"},
                      {"stil": "gri_punctat", "text": "Probabil demontat"}],
            "insigne": [{"cod": "gis", "text": "GIS"}, {"cod": "din_raport", "text": "Din raport"},
                        {"cod": "verificat_om", "text": "Verificat de om"}]}
