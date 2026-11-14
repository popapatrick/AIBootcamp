"""Geocodare din adresă, doar din cache-ul OSM local (`osm.strazi()`). Fără servicii externe, fără chei. Date FICTIVE.

`geocodeaza(referinta, strazi, cfg)` -> {status, lat, lon, precizie_m, metoda, acuratete, motiv}.
Ordine: potrivire deterministă a numelui (fără diacritice/prefixe) -> intersecție -> AI (cli_ai) care alege DOAR
dintre numele din cache; răspuns în afara listei = necunoscut. Un `gasit` la peste `zona.raza_max_m` de centroidul
rețelei de start devine `in_afara_zonei` (`engine.zona.zona_ok`; lat/lon păstrate, metoda `in_afara_zonei`).
"""
import json
import re

from backend.engine.network import dist_m, load_network
from backend.engine.zona import motiv_afara, zona_ok
from backend.extract import cli_ai
from backend.trace import _norm  # normalizare nume stradă (diacritice, prefixe), refolosită

_SEP = re.compile(r"\s*(?:&|\bcol[tț]\s+cu\b|\bintersec[tț]ia\s+cu\b|\bintersec[tț]ie\s+cu\b)\s*", re.I)
_NR = re.compile(r"\b(?:nr|numarul|numar|no)\.?\s*(\d+)|(?<=\s)(\d{1,3})\s*$", re.I)
_AI_CACHE: dict = {}
_NET: dict = {}  # rețeaua de start, încărcată o dată (doar pentru centroidul zonei)


def _ax(a, b):  # puncte (lat, lon)
    return dist_m(tuple(a), tuple(b))


def _lung(pct) -> float:
    return sum(_ax(a, b) for a, b in zip(pct, pct[1:]))


def _la(pct, frac: float) -> tuple[float, float]:
    """Punctul la `frac` (0-1) din lungimea liniei, pe segmente."""
    tinta, acc = _lung(pct) * frac, 0.0
    for a, b in zip(pct, pct[1:]):
        d = _ax(a, b)
        if d and acc + d >= tinta:
            t = (tinta - acc) / d
            return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        acc += d
    return tuple(pct[-1])


def _grupe(strazi) -> dict:
    """{nume_normalizat: {"nume", "pct" (calea cea mai lungă), "lung" (total m)}}; fără străzile fără nume."""
    g: dict = {}
    for s in strazi:
        k = _norm(s.get("nume"))
        if not k or len(s["puncte"]) < 2:
            continue
        e = g.setdefault(k, {"nume": s["nume"], "pct": s["puncte"], "lung": 0.0})
        l = _lung(s["puncte"])
        if l > _lung(e["pct"]):
            e["pct"] = s["puncte"]
        e["lung"] += l
    return g


def _potrivire(text: str, g: dict) -> str | None:
    """Cheia străzii al cărei nume (toate cuvintele) apare în text; la mai multe, cea mai lungă."""
    tok = set(_norm(text).split())
    c = [k for k in g if set(k.split()) <= tok]
    return max(c, key=lambda k: len(k.split())) if c else None


def _ai(text: str, g: dict, cfg: dict) -> str | None:
    """AI alege un nume din lista din cache sau „necunoscută". Validat: în afara listei = None. Cache în proces pe text."""
    nume = sorted(e["nume"] for e in g.values())
    cheie = (_norm(text), tuple(nume))
    if cheie not in _AI_CACHE:
        r = cli_ai.call_cli(
            "Alegi strada din listă care corespunde cel mai probabil textului (ortografie diferită, formulare vagă). "
            "Alege EXACT un nume din listă sau „necunoscuta” dacă niciunul nu se potrivește. Nu inventa nume.",
            {"type": "object", "properties": {"strada": {"type": "string"}}, "required": ["strada"]},
            f"Text: {text}\nStrăzi: {json.dumps(nume, ensure_ascii=False)}")
        _AI_CACHE[cheie] = r.get("strada") if isinstance(r, dict) else None
    ales = _AI_CACHE[cheie]
    return next((k for k, e in g.items() if e["nume"] == ales), None)


def _rez(status, motiv, lat=None, lon=None, precizie=None, metoda=None, acur=0.0):
    return {"status": status, "lat": lat, "lon": lon, "precizie_m": precizie, "metoda": metoda,
            "acuratete": round(acur, 3), "motiv": motiv}


def _gaseste(text: str, g: dict, cfg: dict):
    """(cheie, ai?) pentru un text de stradă: determinist, apoi AI."""
    k = _potrivire(text, g)
    if k:
        return k, False
    return _ai(text, g, cfg), True


def geocodeaza(referinta: dict, strazi: list[dict], cfg: dict, net: dict | None = None) -> dict:
    """Locație aproximativă din `referinta.adresa_structurata {strada, numar, localitate, reper}` sau `referinta.adresa`.

    Întoarce {status: gasit|necunoscut|in_afara_zonei, lat, lon, precizie_m, metoda: osm_cache|ai_estimare|in_afara_zonei, acuratete 0-1, motiv}.
    Acuratețe = cfg.geocodare.acuratete[intersectie|strada_numar|strada|reper] (x factor_ai_fuzzy dacă a ales AI).
    Ipoteză (fără numere reale în OSM): numărul N se pune la fracția clamp(N/100, 0.1, 0.9) din cea mai lungă cale
    a străzii (fără par/impar); strada singură = mijlocul căii, precizie = lungime/2 în [min, max] din cfg.
    `net` = rețeaua de start pentru safeguardul de zonă; None = `load_network()` (reținută în modul)."""
    r = _geocodeaza(referinta, strazi, cfg)
    if r["status"] != "gasit":
        return r
    if net is None:
        net = _NET or _NET.update(load_network()) or _NET
    z = zona_ok(r["lat"], r["lon"], net, cfg)
    return r if z["ok"] else {**r, "status": "in_afara_zonei", "metoda": "in_afara_zonei", "motiv": motiv_afara(z)}


def _geocodeaza(referinta: dict, strazi: list[dict], cfg: dict) -> dict:
    c = cfg["geocodare"]
    ad = referinta.get("adresa_structurata") or {}
    strada, reper = ad.get("strada") or "", ad.get("reper") or ""
    nr = str(ad.get("numar") or "").strip()
    if not strada and not reper:
        strada = referinta.get("adresa") or ""
    if not nr:  # număr din text liber
        m = _NR.search(strada)
        nr = (m.group(1) or m.group(2)) if m else ""
    g = _grupe(strazi)
    if not g:
        return _rez("necunoscut", "cache OSM de străzi indisponibil")
    loc = "strada"
    if not strada:
        strada, loc = reper, "reper"
    if not strada.strip():
        return _rez("necunoscut", "adresa nu conține stradă sau reper")

    parti = [p for p in _SEP.split(strada) if p.strip()][:2]
    gasite = [_gaseste(p, g, cfg) for p in parti]
    if any(k is None for k, _ in gasite):
        return _rez("necunoscut", f"nicio stradă din cache nu se potrivește cu „{strada}”")
    ai = any(a for _, a in gasite)
    metoda, f = ("ai_estimare", c["factor_ai_fuzzy"]) if ai else ("osm_cache", 1.0)
    how = "ales de AI dintre străzile din cache" if ai else "potrivire exactă a numelui"
    e1 = g[gasite[0][0]]
    if len(gasite) == 2 and gasite[0][0] != gasite[1][0]:
        e2 = g[gasite[1][0]]
        d, a, b = min((_ax(a, b), a, b) for a in e1["pct"] for b in e2["pct"])
        if d <= 2 * c["precizie_intersectie_m"] + 30:  # vârfurile cele mai apropiate; mai departe = nu se intersectează
            return _rez("gasit", f"intersecția {e1['nume']} cu {e2['nume']} ({how}); capete la {d:.0f} m",
                        round((a[0] + b[0]) / 2, 6), round((a[1] + b[1]) / 2, 6), c["precizie_intersectie_m"],
                        metoda, c["acuratete"]["intersectie"] * f)
    if nr.isdigit() and loc == "strada":
        p = _la(e1["pct"], min(max(int(nr) / 100, 0.1), 0.9))
        return _rez("gasit", f"{e1['nume']} nr. {nr}, interpolat pe stradă ({how})", round(p[0], 6), round(p[1], 6),
                    c["precizie_numar_m"], metoda, c["acuratete"]["strada_numar"] * f)
    p = _la(e1["pct"], 0.5)
    pr = c["precizie_reper_m"] if loc == "reper" else min(max(e1["lung"] / 2, c["precizie_strada_min_m"]),
                                                          c["precizie_strada_max_m"])
    return _rez("gasit", f"{'reper pe ' if loc == 'reper' else 'mijlocul străzii '}{e1['nume']} ({how})",
                round(p[0], 6), round(p[1], 6), pr, metoda, c["acuratete"][loc] * f)
