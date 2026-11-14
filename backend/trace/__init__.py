"""Locația din traseul tabletei: opriri + potrivire cu strada din adresă (proprietar A).

Funcții pure, fără rețea. Contract: contracts/interfaces.md, "Module noi ale lui A".
"""
import math
import re
import unicodedata
from datetime import datetime

from backend.engine.network import dist_m

__all__ = ["gaseste_opriri", "localizeaza"]

_PREFIXE = r"(strada|str|bulevardul|bd|bdul|soseaua|sos|aleea|intrarea|calea|piata)"


def _t(p: dict) -> datetime:
    return datetime.fromisoformat(p["t"])


def gaseste_opriri(puncte: list[dict], cfg: dict) -> list[dict]:
    """puncte = [{t: ISO datetime, lat, lon}]. Întoarce opriri cronologice:
    [{lat, lon, durata_min, inceput, sfarsit, n_puncte}].
    Oprire = puncte consecutive la cel mult `raza_oprire_m` de centroidul grupului, cu durată >= `durata_min_min`."""
    c = cfg["trace"]
    pts = sorted(puncte, key=_t)
    out, i = [], 0
    while i < len(pts):
        j, la, lo = i, pts[i]["lat"], pts[i]["lon"]
        while j + 1 < len(pts):
            n = j - i + 1
            ca, co = la / n, lo / n  # centroid curent
            nxt = pts[j + 1]
            if dist_m((ca, co), (nxt["lat"], nxt["lon"])) > c["raza_oprire_m"]:
                break
            j += 1
            la += nxt["lat"]
            lo += nxt["lon"]
        n = j - i + 1
        durata = (_t(pts[j]) - _t(pts[i])).total_seconds() / 60
        if durata >= c["durata_min_min"]:
            out.append({"lat": la / n, "lon": lo / n, "durata_min": round(durata, 2),
                        "inceput": pts[i]["t"], "sfarsit": pts[j]["t"], "n_puncte": n})
            i = j + 1
        else:
            i += 1
    return out


def _norm(s: str | None) -> str:
    """Fără diacritice, litere mici, fără prefix de tip stradă, fără punctuație."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(rf"\b{_PREFIXE}\b", " ", s)
    return " ".join(s.split())


def _dist_segment(p, a, b) -> float:
    """Distanță în m de la p la segmentul a-b (lat, lon), proiecție locală plană."""
    k = math.cos(math.radians(p[0]))
    f = lambda q: ((q[1] - p[1]) * 111_320 * k, (q[0] - p[0]) * 111_320)
    (ax, ay), (bx, by) = f(a), f(b)
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
    return math.hypot(ax + t * dx, ay + t * dy)


def _dist_strada(p, ways) -> float:
    return min(_dist_segment(p, w[i], w[i + 1]) for w in ways for i in range(len(w) - 1))


def _noduri(net: dict) -> list[dict]:
    els = list(net.get("noduri", {}).values())
    if net.get("post"):
        els.append(net["post"])
    return els


def _cel_mai_aproape(p, els):
    best = min(((dist_m(p, (e["lat"], e["lon"])), e["id"]) for e in els), default=(None, None))
    return best[1], best[0]


def localizeaza(trace: list[dict], adresa: str | None, net: dict, strazi: list[dict], cfg: dict) -> dict:
    """Întoarce {status: gasit|ambiguu|fara_opriri, opriri, strada: {nume, distanta_m}|None,
    alegere: {lat, lon, durata_min, element_id|None, distanta_element_m}|None,
    vizitate: [{element_id, durata_min}], ambiguitate: bool, calitate: 0-1, motiv}.
    `net` = rezultatul `load_network()` (cheile `noduri`, opțional `post`).
    Adresa dă strada (nume normalizat, conținut în adresă), traseul dă locul: oprirea cea mai lungă
    la cel mult `distanta_strada_m` de stradă. Fără stradă potrivită: cea mai lungă oprire, calitate * factor_fara_strada."""
    c = cfg["trace"]
    opriri = gaseste_opriri(trace, cfg)
    rez = {"status": "fara_opriri", "opriri": opriri, "strada": None, "alegere": None, "vizitate": [],
           "ambiguitate": False, "calitate": 0.0, "motiv": "Traseul nu conține nicio oprire."}
    if not opriri:
        return rez
    els = _noduri(net)
    for o in opriri:
        eid, d = _cel_mai_aproape((o["lat"], o["lon"]), els)
        if d is not None and d <= c["raza_oprire_m"]:
            rez["vizitate"].append({"element_id": eid, "durata_min": o["durata_min"]})

    a = _norm(adresa)
    nume = {}  # nume normalizat -> poligoane, doar numele conținute în adresă
    for s in strazi:
        n = _norm(s["nume"])
        if n and a and re.search(rf"\b{re.escape(n)}\b", a):
            nume.setdefault(n, {"nume": s["nume"], "ways": []})["ways"].append([tuple(p) for p in s["puncte"]])
    str_ = max(nume.values(), key=lambda v: len(_norm(v["nume"])), default=None)

    cand, strada, calitate = [], None, 0.9
    if str_:
        for o in opriri:
            d = _dist_strada((o["lat"], o["lon"]), str_["ways"])
            if d <= c["distanta_strada_m"]:
                cand.append((o, d))
    if cand:
        cand.sort(key=lambda x: -x[0]["durata_min"])
        strada = {"nume": str_["nume"], "distanta_m": round(cand[0][1], 1)}
        motiv = f"Oprirea cea mai lungă ({cand[0][0]['durata_min']} min) lângă {str_['nume']}."
    else:
        cand = [(o, None) for o in sorted(opriri, key=lambda o: -o["durata_min"])]
        calitate *= c["factor_fara_strada"]
        motiv = ("Adresa nu s-a potrivit cu o stradă" if not str_ else f"Nicio oprire la {c['distanta_strada_m']} m de {str_['nume']}") \
            + "; s-a luat cea mai lungă oprire din traseu."
    amb = len(cand) > 1 and cand[0][0]["durata_min"] - cand[1][0]["durata_min"] < c["prag_ambiguitate_min"]
    if amb:
        calitate *= c["factor_ambiguitate"]
        motiv += f" Ambiguu: a doua oprire are {cand[1][0]['durata_min']} min."
    o = cand[0][0]
    eid, d = _cel_mai_aproape((o["lat"], o["lon"]), els)
    ok = d is not None and d <= c["raza_oprire_m"]
    rez.update(status="ambiguu" if amb else "gasit", strada=strada, ambiguitate=amb, calitate=round(calitate, 3), motiv=motiv,
               alegere={"lat": o["lat"], "lon": o["lon"], "durata_min": o["durata_min"],
                        "element_id": eid if ok else None, "distanta_element_m": round(d, 1) if d is not None else None})
    return rez
