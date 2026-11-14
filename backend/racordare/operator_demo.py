"""Poziția GPS DUMMY a operatorului, generată din textul lui (funcție pură, determinist). Date FICTIVE.

Operatorul e la casă, cererea de racordare nu are coordonate. Din descrierea lui („strada X colț cu strada Y",
„strada X din cartierul Z") se află zona, iar punctul se alege DOAR în acea zonă, din datele OSM locale.
Parsare cu reguli simple (fără AI), tolerantă la diacritice, majuscule și prescurtări (str., bd., sos., cart.).
Nu inventează: dacă niciun indiciu nu se găsește în datele locale, ridică `LocalizareEroare`.
"""
from __future__ import annotations

import hashlib
import math
import random
import re
import unicodedata

from backend.engine.network import dist_m

TIPURI_STRADA = ("strada", "soseaua", "aleea", "intrarea", "bulevardul")
_STOP = {"colt", "cu", "din", "in", "la", "langa", "intersectia", "intersectie", "nr", "numarul", "cartier", "zona",
         "pe", "de", "si", "spre", "dupa", "vis", "aproape", "unde", "casa", "client", "dreptul", "fata", "sunt",
         "caut", "strada", "soseaua", "aleea", "intrarea", "bulevardul", "reper", "coltul"}
_MARCAJ_INTERSECTIE = re.compile(r"\b(colt cu|coltul|la colt|intersectia|intersectie|se intersecteaza)\b")
_PREF = {r"str": "strada", r"bd": "bulevardul", r"bld": "bulevardul", r"sos": "soseaua", r"intr": "intrarea",
         r"cart": "cartier", r"cartierul": "cartier", r"bulevard": "bulevardul"}
PRAG_INTERSECTIE_M = 25   # shortcut: două străzi se taie dacă punctele lor sunt la <= 25 m; nu calculăm intersecția exactă
MARGINE_ZONA_M = 30       # shortcut: cartierul = dreptunghiul străzilor cu `zona` respectivă + margine (nu există poligon OSM)
PAS_M = 5


class LocalizareEroare(Exception):
    """Textul nu se poate localiza în datele locale. `indicii` = ce s-a căutat (cu gasit: false)."""

    def __init__(self, mesaj: str, indicii: list[dict]):
        super().__init__(mesaj)
        self.indicii = indicii


def normalizeaza(t: str) -> str:
    """Litere mici, fără diacritice, prescurtări expandate (str. -> strada, bd. -> bulevardul, cart. -> cartier)."""
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    for pre, full in _PREF.items():
        t = re.sub(rf"\b{pre}\b\.?(?=\s|$)", full, t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _core(nume: str) -> str:
    n = normalizeaza(nume).split()
    return " ".join(n[1:] if n and n[0] in TIPURI_STRADA else n)


def _frază(t: str, start: int, maxt: int) -> tuple[str, int]:
    """Cuvintele de după `start` până la un cuvânt de oprire (max maxt)."""
    cuv, i = [], start
    toks = t[start:].split()
    for w in toks[:maxt]:
        if w in _STOP:
            break
        cuv.append(w)
    return " ".join(cuv), start


def _densifica(puncte: list, pas: float = PAS_M) -> list[tuple]:
    out = []
    for a, b in zip(puncte, puncte[1:]):
        a, b = tuple(a), tuple(b)
        n = max(1, int(dist_m(a, b) // pas))
        out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
    if puncte:
        out.append(tuple(puncte[-1]))
    return out


def _lungime(puncte: list) -> float:
    return sum(dist_m(tuple(a), tuple(b)) for a, b in zip(puncte, puncte[1:]))


def _mentiuni(t: str, strazi: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """(străzi, cartiere, repere) menționate în textul normalizat `t`, în ordinea apariției.
    Fiecare: {valoare, gasit, nume|zona, poz}."""
    nume_cunoscute = {}
    for s in strazi:
        if s.get("nume"):
            nume_cunoscute.setdefault(_core(s["nume"]), s["nume"])
    zone = {normalizeaza(s["zona"]): s["zona"] for s in strazi if s.get("zona")}
    ocupat: list[tuple[int, int]] = []

    def liber(a, b):
        return not any(a < y and x < b for x, y in ocupat)

    st, ca, re_ = [], [], []
    for m in re.finditer(r"\b(" + "|".join(TIPURI_STRADA) + r")\s+", t):
        fr, _ = _frază(t, m.end(), 4)
        if not fr:
            continue
        gasit = next((c for c in sorted(nume_cunoscute, key=len, reverse=True) if fr == c or fr.startswith(c + " ")), None)
        sfarsit = m.end() + len(gasit if gasit else fr)
        ocupat.append((m.start(), sfarsit))
        st.append({"valoare": nume_cunoscute[gasit] if gasit else f"{m.group(1).capitalize()} {fr.title()}",
                   "gasit": bool(gasit), "nume": nume_cunoscute.get(gasit), "poz": m.start()})
    for c in sorted(nume_cunoscute, key=len, reverse=True):   # nume de stradă fără „strada" în față
        if any(ch.isdigit() for ch in c):
            continue
        for m in re.finditer(rf"\b{re.escape(c)}\b", t):
            if liber(m.start(), m.end()):
                ocupat.append((m.start(), m.end()))
                st.append({"valoare": nume_cunoscute[c], "gasit": True, "nume": nume_cunoscute[c], "poz": m.start()})
    st.sort(key=lambda x: x["poz"])
    for m in re.finditer(r"\bcartier\s+", t):
        fr, _ = _frază(t, m.end(), 3)
        if not fr:
            continue
        gasit = next((z for z in sorted(zone, key=len, reverse=True) if fr == z or fr.startswith(z + " ")), None)
        ocupat.append((m.start(), m.end() + len(gasit or fr)))
        ca.append({"valoare": zone[gasit] if gasit else fr.title(), "gasit": bool(gasit), "zona": zone.get(gasit), "poz": m.start()})
    for z in zone:
        for m in re.finditer(rf"\b{re.escape(z)}\b", t):
            if liber(m.start(), m.end()) and not any(c["zona"] == zone[z] for c in ca):
                ocupat.append((m.start(), m.end()))
                ca.append({"valoare": zone[z], "gasit": True, "zona": zone[z], "poz": m.start()})
    for m in re.finditer(r"\b(?:langa|aproape de|in dreptul|vis a vis de|in fata)\s+|\breper\s+", t):
        if t[m.end():].split()[:1] and t[m.end():].split()[0] in _STOP:
            continue
        fr, _ = _frază(t, m.end(), 4)
        if fr and liber(m.end(), m.end() + len(fr)):
            re_.append({"valoare": fr, "gasit": False, "poz": m.start()})   # fără repere în datele OSM locale (doar străzi)
    return st, ca, re_


def _in_zona(p, bbox) -> bool:
    return bbox[0] <= p[0] <= bbox[2] and bbox[1] <= p[1] <= bbox[3]


def _bbox_zona(strazi: list[dict], zona: str) -> tuple:
    pts = [tuple(p) for s in strazi if s.get("zona") == zona for p in s["puncte"]]
    la, lo = [p[0] for p in pts], [p[1] for p in pts]
    mlat = MARGINE_ZONA_M / 111_320
    mlon = MARGINE_ZONA_M / (111_320 * math.cos(math.radians(sum(la) / len(la))))
    return min(la) - mlat, min(lo) - mlon, max(la) + mlat, max(lo) + mlon


def locatie_operator_demo(text: str, net: dict, strazi: list[dict], cfg: dict,
                          lat: float | None = None, lon: float | None = None) -> dict:
    """Poziție GPS dummy a operatorului, din descrierea lui `text`, în zona descrisă. Pură și deterministă.

    Indicii recunoscute: stradă („strada X"), intersecție („X colț cu Y", „intersecția X cu Y"), cartier („cartierul Z",
    sau o zonă OSM `is_in` pomenită), reper („lângă ...", mereu negăsit: nu avem repere în datele locale).
    Constrângerile se combină prin intersecție (strada X din cartierul Z). `lat`/`lon` (opționale) aleg dintre punctele
    posibile pe cel mai apropiat de indiciu. Punctul e la cel puțin `racordare.operator_distanta_min_m` și, dacă se poate,
    la cel mult `raza_nod_m` de un nod (altfel lanțul nu pornește), apoi primește zgomot GPS (<= jumătate din precizie).

    net: network.geojson sau dict-ul motorului; strazi: `osm.strazi()` (cu `zona`); cfg: weights.yaml.
    Întoarce {lat, lon, precizie_m, simulata: True, strada, motiv, indicii: [{tip, valoare, gasit}], zona}.
    Ridică LocalizareEroare dacă niciun indiciu nu se găsește în datele locale (nu inventează un punct).
    """
    from backend.racordare import _elemente
    c = cfg["racordare"]
    t = normalizeaza(text)
    st, ca, repere = _mentiuni(t, strazi)
    marcaj = bool(_MARCAJ_INTERSECTIE.search(t))
    indicii = [{"tip": "strada", "valoare": s["valoare"], "gasit": s["gasit"]} for s in st]
    # intersecție: marcaj sau cel puțin două străzi pomenite
    inter = None
    if len(st) >= 2 or (marcaj and st):
        a, b = st[0], (st[1] if len(st) > 1 else None)
        val = f"{a['valoare']} / {b['valoare']}" if b else f"{a['valoare']} / (a doua stradă lipsește)"
        ok = None
        if b and a["gasit"] and b["gasit"] and a["nume"] != b["nume"]:
            pa = [q for s in strazi if s.get("nume") == a["nume"] for q in _densifica(s["puncte"])]
            pb = [q for s in strazi if s.get("nume") == b["nume"] for q in _densifica(s["puncte"])]
            d, p, q = min(((dist_m(x, y), x, y) for x in pa for y in pb), default=(1e9, None, None))
            if d <= PRAG_INTERSECTIE_M:
                ok = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        inter = ok
        indicii.append({"tip": "intersectie", "valoare": val, "gasit": ok is not None})
    for z in ca:
        indicii.append({"tip": "cartier", "valoare": z["valoare"], "gasit": z["gasit"]})
    for r in repere:
        indicii.append({"tip": "reper", "valoare": r["valoare"], "gasit": False})

    zona_ok = next((z["zona"] for z in ca if z["gasit"]), None)
    bbox = _bbox_zona(strazi, zona_ok) if zona_ok else None
    strada_ok = next((s for s in st if s["gasit"]), None)
    if inter:
        cand, tip, descr = [inter], "intersectie", f"intersecția {indicii[len(st)]['valoare']}"
        prec = c["precizie_intersectie_m"]
        strada = strada_ok["nume"]
    elif strada_ok:
        pct = [s["puncte"] for s in strazi if s.get("nume") == strada_ok["nume"]]
        cand = [q for p in pct for q in _densifica(p)]
        lung = sum(_lungime(p) for p in pct)
        tip, descr, strada = "strada", strada_ok["nume"], strada_ok["nume"]
        prec = min(c["precizie_strada_max_m"], max(c["precizie_strada_min_m"], lung / 20))
    elif zona_ok:
        cand = [q for s in strazi if s.get("zona") == zona_ok for q in _densifica(s["puncte"], 20)]
        tip, descr, strada = "cartier", f"cartierul {zona_ok}", None
        prec = c["precizie_cartier_m"]
    else:
        gl = ", ".join(f"{i['tip']} „{i['valoare']}”" for i in indicii) or "niciun indiciu (stradă, intersecție, cartier)"
        raise LocalizareEroare(f"Textul nu se poate localiza în datele locale ({gl}). Dă clic pe hartă.", indicii)
    if bbox:
        cand = [q for q in cand if _in_zona(q, bbox)]
        descr += "" if tip == "cartier" else f", în cartierul {zona_ok}"
        if not cand:
            raise LocalizareEroare(f"{descr}: indiciile se contrazic (zona nu conține locul descris). Dă clic pe hartă.", indicii)
    prec = round(prec)

    noduri = [p for _, p in _elemente(net)[0]]
    dn = lambda p: min(dist_m(p, q) for q in noduri)
    cu_d = [(dn(q), q) for q in cand]
    bun = [(d, q) for d, q in cu_d if c["operator_distanta_min_m"] <= d <= c["raza_nod_m"] - prec]
    nota = ""
    seed = int.from_bytes(hashlib.sha256(t.encode()).digest()[:8], "big")
    if not bun:
        d, q = min(cu_d) if min(cu_d)[0] > c["raza_nod_m"] - prec else max(cu_d)
        nota = (f" Atenție: locul descris e la {d:.0f} m de rețea, în afara intervalului util pentru lanț "
                f"({c['operator_distanta_min_m']}-{c['raza_nod_m'] - prec:.0f} m).")
        bun = [(d, q)]
    if lat is not None and lon is not None:
        d, q = min(bun, key=lambda x: dist_m(x[1], (lat, lon)))
    elif tip == "cartier":
        d, q = sorted(bun, key=lambda x: x[1])[seed % len(bun)]
    else:
        d, q = max(bun, key=lambda x: (x[0], x[1]))   # capătul cel mai depărtat de rețea
    rng = random.Random(seed)
    r, ang = prec * 0.5 * math.sqrt(rng.random()), rng.random() * 2 * math.pi
    la = q[0] + r * math.cos(ang) / 111_320
    lo = q[1] + r * math.sin(ang) / (111_320 * math.cos(math.radians(q[0])))
    lipsa = [f"{i['tip']} „{i['valoare']}”" for i in indicii if not i["gasit"]]
    motiv = (f"Poziție SIMULATĂ (nu GPS real), generată determinist din textul operatorului: {descr}, "
             f"la ~{d:.0f} m de cel mai apropiat nod, precizie ±{prec} m."
             + (f" Indicii negăsiți în datele locale: {', '.join(lipsa)}." if lipsa else "") + nota)
    return {"lat": round(la, 7), "lon": round(lo, 7), "precizie_m": prec, "simulata": True, "strada": strada,
            "motiv": motiv, "indicii": indicii, "zona": descr}
