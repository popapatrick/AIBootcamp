"""Fire mutate descrise doar în text (Sesiunea 4, V4): ce străzi și ce intersecție numește documentul.

Funcții pure, deterministe, fără AI și fără rețea. Extracția (AI) pune de obicei `detalii.intersectie {strada_1, strada_2}`
și `detalii.strada_noua`; dacă lipsesc, aici e rezerva cu regex pe `text_original`, `detalii.observatii` și adresă
(„intersecția X cu Y", „colț cu Y", „mutat(ă) pe Strada Z"). Nu inventează nimic: fără stradă în text, întoarce `None`.
Date FICTIVE; străzile sunt cele din cache-ul OSM local (`osm.strazi()`).
"""
from __future__ import annotations

import re
import unicodedata

_TIP = r"(?:Strada|Str\.|Șoseaua|Soseaua|Aleea|Intrarea|Calea|Bulevardul|Bd\.)"
_NUME = _TIP + r"(?:\s+(?!" + _TIP + r")[A-ZĂÂÎȘȚ0-9][\w\-]*){1,3}"
_RE_INTERSECTIE = re.compile(r"(?i:intersec[tț]i[ae]|col[tț])\s+(?i:dintre\s+)?(?P<a>" + _NUME + r")\s+(?i:cu|[sș]i)\s+(?P<b>" + _NUME + ")")
_RE_COLT_CU = re.compile(r"(?i:col[tț]\s+cu|intersec[tț]i[ae]\s+cu)\s+(?P<b>" + _NUME + ")")
_RE_ADRESA_DUBLA = re.compile(r"^\s*(?P<a>" + _NUME + r")\s+(?i:cu|[sș]i|&|col[tț]\s+cu)\s+(?P<b>" + _NUME + r")\s*$")
_RE_STRADA_NOUA = re.compile(r"(?i:mut(?:at|ate|ată|ata|ați))\s+(?i:pe|spre)\s+(?P<s>" + _NUME + ")")
_CEDILA = str.maketrans("şţŞŢ", "șțȘȚ")


def norm(s: str | None) -> str:
    """Nume de stradă pentru comparare: fără diacritice, litere mici, spații simple (și `Str.` = `Strada`)."""
    t = unicodedata.normalize("NFKD", (s or "").translate(_CEDILA))
    t = "".join(c for c in t if not unicodedata.combining(c)).casefold()
    t = re.sub(r"\bstr\.", "strada", t)
    return re.sub(r"\s+", " ", t).strip(" .,;")


def nume_canonic(txt: str | None, strazi: list[dict]) -> str | None:
    """Numele străzii din cache-ul OSM (`strazi` = `osm.strazi()`) care coincide cu `txt` (fără diacritice/majuscule); None dacă nu există."""
    n = norm(txt)
    if not n:
        return None
    for s in strazi:
        if s.get("nume") and norm(s["nume"]) == n:
            return s["nume"]
    return None


def _text(event: dict) -> str:
    det, ref = event.get("detalii") or {}, event.get("referinta") or {}
    return " | ".join(str(x) for x in (event.get("text_original"), det.get("observatii"), ref.get("adresa")) if x).translate(_CEDILA)


def _strada_ref(event: dict) -> str | None:
    """Strada din adresa structurată (sau adresa brută), dacă începe cu un tip de stradă; altfel None."""
    ref = event.get("referinta") or {}
    ad = ref.get("adresa_structurata") or {}
    s = (ad.get("strada") or (ref.get("adresa") or "").split(",")[0]).strip().translate(_CEDILA)
    return s or None


def intersectie_din_eveniment(event: dict) -> dict | None:
    """`{strada_1, strada_2, sursa}` (sursa: `extractie` | `regex`) sau None.

    Ordinea: `detalii.intersectie` (extracția) > indiciul `colt` din adresa structurată > regex în text („intersecția X cu Y",
    „colț cu Y" cu strada 1 din adresă) > adresa de forma „X cu Y"."""
    det, ref = event.get("detalii") or {}, event.get("referinta") or {}
    ix = det.get("intersectie") or {}
    if ix.get("strada_1") and ix.get("strada_2"):
        return {"strada_1": ix["strada_1"], "strada_2": ix["strada_2"], "sursa": "extractie"}
    ad = ref.get("adresa_structurata") or {}
    ind = ad.get("indiciu") or {}
    if ind.get("tip") == "colt" and ad.get("strada") and ind.get("strada_2"):
        return {"strada_1": ad["strada"], "strada_2": ind["strada_2"], "sursa": "extractie"}
    text = _text(event)
    m = _RE_INTERSECTIE.search(text)
    if m:
        return {"strada_1": m["a"], "strada_2": m["b"], "sursa": "regex"}
    s1, m = _strada_ref(event), _RE_COLT_CU.search(text)
    if m and s1:
        return {"strada_1": s1, "strada_2": m["b"], "sursa": "regex"}
    m = _RE_ADRESA_DUBLA.match((ref.get("adresa") or "").translate(_CEDILA))
    if m:
        return {"strada_1": m["a"], "strada_2": m["b"], "sursa": "regex"}
    return None


def strada_noua_din_eveniment(event: dict) -> tuple[str | None, str | None]:
    """(strada pe care au fost mutate firele, sursa `extractie` | `regex`) sau (None, None)."""
    s = (event.get("detalii") or {}).get("strada_noua")
    if s:
        return s, "extractie"
    m = _RE_STRADA_NOUA.search(_text(event))
    return (m["s"], "regex") if m else (None, None)


def strada_din_eveniment(event: dict) -> str | None:
    """Strada numită ca loc al lucrării (fără intersecție): `detalii.strada`, adresa structurată sau adresa brută; None dacă nu e niciuna."""
    s = (event.get("detalii") or {}).get("strada") or _strada_ref(event)
    return s or None
