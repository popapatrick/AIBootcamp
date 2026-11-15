"""Geocodare din adresă, doar din cache-ul OSM local (`osm.strazi()`). Fără servicii externe, fără chei. Date FICTIVE.

`geocodeaza(referinta, strazi, cfg)` -> {status, lat, lon, precizie_m, metoda, acuratete, motiv}.
Ordine: potrivire deterministă a numelui (fără diacritice/prefixe) -> intersecție -> AI (cli_ai) care alege DOAR
dintre numele din cache (alegerea e păstrată în `data/cache/geo_ai.json`, commit-uit); răspuns în afara listei = necunoscut. Un `gasit` la peste `zona.raza_max_m` de centroidul
rețelei de start devine `in_afara_zonei` (`engine.zona.zona_ok`; lat/lon păstrate, metoda `in_afara_zonei`).
"""
import difflib
import json
import re
from pathlib import Path
import unicodedata

from backend.engine.network import dist_m, load_network
from backend.engine.zona import centru_retea, motiv_afara, zona_ok
from backend.extract import cli_ai
from backend.trace import _norm  # normalizare nume stradă (diacritice, prefixe), refolosită
from backend.geo import fereastra as _fer

_SEP = re.compile(r"\s*(?:&|\bcol[tț]\s+cu\b|\bintersec[tț]ia\s+cu\b|\bintersec[tț]ie\s+cu\b)\s*", re.I)
_NR = re.compile(r"\b(?:nr|numarul|numar|no)\.?\s*(\d+)|(?<=\s)(\d{1,3})\s*$", re.I)
_AI_CACHE: dict = {}  # cache în proces (peste cel de pe disc)
_AI_FILE = Path(__file__).resolve().parents[2] / "data/cache/geo_ai.json"  # cache persistent {cheie normalizată: nume|null}; suprascriibil în teste
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
    """{nume_normalizat: {"nume", "pct" (calea cea mai lungă), "lung" (total m), "cai" (toate căile)}}; fără străzile fără nume."""
    g: dict = {}
    for s in strazi:
        k = _norm(s.get("nume"))
        if not k or len(s["puncte"]) < 2:
            continue
        e = g.setdefault(k, {"nume": s["nume"], "pct": s["puncte"], "lung": 0.0, "cai": []})
        e["cai"].append(s["puncte"])
        l = _lung(s["puncte"])
        if l > _lung(e["pct"]):
            e["pct"] = s["puncte"]
        e["lung"] += l
    return g


_TIP = re.compile(r"\b(strada|str|calea|bulevardul|bd|bdul|soseaua|sos|aleea|intrarea)\b\.?\s*", re.I)
_TIPN = {"str": "strada", "bd": "bulevardul", "bdul": "bulevardul", "sos": "soseaua"}


def _tip(nume: str | None) -> str | None:
    m = _TIP.match(_fara_diac(nume or "").strip()) or _TIP.search(_fara_diac(nume or ""))
    return _TIPN.get(m.group(1).lower(), m.group(1).lower()) if m else None


def _fara_diac(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def _segment(text: str) -> tuple[str, str | None]:
    """Dacă textul are un cuvânt de tip stradă (strada/calea/...), doar numele de după el, până la prima cifră/virgulă,
    poate fi potrivit (un oraș după număr, ex. „București”, nu e stradă). Fără tip: textul întreg."""
    t = _fara_diac(text)
    m = _TIP.search(t)
    if not m:
        return text, None
    return re.split(r"[,\d]", t[m.end():], 1)[0], _TIPN.get(m.group(1).lower(), m.group(1).lower())


def _potrivire(text: str, g: dict) -> str | None:
    """Cheia străzii al cărei nume (toate cuvintele) apare în text; la mai multe, cea mai lungă.
    Cu tip de stradă în text: doar numele de după el și doar străzi de același tip („Calea X” nu potrivește „Strada Y”)."""
    seg, tip = _segment(text)
    tok = set(_norm(seg).split())
    c = [k for k in g if set(k.split()) <= tok and (not tip or _tip(g[k]["nume"]) in (None, tip))]
    return max(c, key=lambda k: len(k.split())) if c else None


def _alta(text: str, g: dict, exclus: str) -> str | None:
    """Altă stradă din cache (diferită de `exclus`) numită determinist în text; None dacă nu e niciuna."""
    tok = set(_norm(text).split())
    c = [k for k in g if k != exclus and set(k.split()) <= tok]
    return max(c, key=lambda k: len(k.split())) if c else None


def _lista(g: dict) -> list[str]:
    return sorted(e["nume"] for e in g.values())


def _citeste() -> dict:
    try:
        return json.loads(_AI_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _scrie(cheie: str, nume: str | None) -> None:
    d = _citeste()
    d[cheie] = nume
    _AI_FILE.parent.mkdir(parents=True, exist_ok=True)
    _AI_FILE.write_text(json.dumps(d, ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8")


def cerere_ai(text_strada: str, strazi: list[dict]) -> dict:
    """{cheie, candidati}: cheia din `geo_ai.json` pentru textul de stradă + cele mai apropiate 5 nume din listă (difflib)."""
    cheie, g = _norm(text_strada), _grupe(strazi)
    apropiate = difflib.get_close_matches(cheie, list(g), n=5, cutoff=0.0)
    return {"cheie": cheie, "candidati": [g[k]["nume"] for k in apropiate]}


def scrie_ai(cheie: str, nume: str | None, strazi: list[dict] | None = None) -> None:
    """Scrie în `geo_ai.json` alegerea pentru `cheie` (nume exact din lista de străzi sau None). Nume în afara listei = ValueError."""
    if nume is not None and nume not in _lista(_grupe(strazi if strazi is not None else _strazi())):
        raise ValueError(f"nume în afara listei: {nume!r}")
    _scrie(cheie, nume)


def _strazi():
    from backend.engine.osm import strazi
    return strazi()


def _ai(text: str, g: dict, cfg: dict) -> str | None:
    """Alege un nume din lista din cache sau None. Ordine: cache persistent `geo_ai.json` (valoare invalidă = ignorată) -> CLI AI
    (rezultat scris în cache). Fără CLI și fără intrare = None."""
    nume, cheie = _lista(g), _norm(text)
    d = _citeste()
    if cheie in d and (d[cheie] is None or d[cheie] in nume):
        ales = d[cheie]
    else:
        k = (cheie, tuple(nume))
        if k not in _AI_CACHE:
            r = cli_ai.call_cli(
                "Alegi strada din listă care corespunde cel mai probabil textului (ortografie diferită, formulare vagă). "
                "Alege EXACT un nume din listă sau „necunoscuta” dacă niciunul nu se potrivește. Nu inventa nume.",
                {"type": "object", "properties": {"strada": {"type": "string"}}, "required": ["strada"]},
                f"Text: {text}\nStrăzi: {json.dumps(nume, ensure_ascii=False)}")
            _AI_CACHE[k] = r.get("strada") if isinstance(r, dict) else None
            if isinstance(r, dict):  # răspuns real (nu CLI oprit): îl păstrăm și pe disc
                _scrie(cheie, _AI_CACHE[k] if _AI_CACHE[k] in nume else None)
        ales = _AI_CACHE[k]
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


def _net_implicit(net: dict | None) -> dict:
    """`net` dat, sau rețeaua de start încărcată o dată în modul."""
    return net if net is not None else (_NET or _NET.update(load_network()) or _NET)


def geocodeaza(referinta: dict, strazi: list[dict], cfg: dict, net: dict | None = None, ancore: list[dict] | None = None) -> dict:
    """Locație aproximativă din `referinta.adresa_structurata {strada, numar, localitate, reper}` sau `referinta.adresa`.

    Întoarce {status: gasit|necunoscut|in_afara_zonei, lat, lon, precizie_m, metoda: osm_cache|ai_estimare|in_afara_zonei, acuratete 0-1, motiv,
    fereastra}. `fereastra` = rezultatul complet al `fereastra_strada` (doar la gasit/in_afara_zonei), cheie aditivă.
    Acuratețe = cfg.geocodare.acuratete[intersectie|strada_numar|strada|reper] (x factor_ai_fuzzy dacă a ales AI).
    Dacă `reper` numește o a doua stradă din cache, rezultatul e intersecția celor două (spec: „intersecție = punctul comun").
    `id`/`coordonate` explicite nu trec pe aici (spec: geocodarea nu se apelează; le tratează motorul), deci `necunoscut`.
    Cu număr (V6): poziția vine din `fereastra_strada` (ancore dacă `ancore` are adrese pe aceeași stradă, altfel convenția de
    numerotare: ~12 m la 2 numere de la capătul de start, par/impar pe părți opuse; precizie/acuratețe din `cautare_strada`).
    Strada singură = mijlocul căii, precizie = lungime/2 în [min, max] din cfg.
    `net` = rețeaua de start pentru safeguardul de zonă; None = `load_network()` (reținută în modul)."""
    net = _net_implicit(net)
    r = _geocodeaza(referinta, strazi, cfg, net, ancore)
    if r["status"] != "gasit":
        return r
    z = zona_ok(r["lat"], r["lon"], net, cfg)
    if not z["ok"]:
        r = {**r, "status": "in_afara_zonei", "metoda": "in_afara_zonei", "motiv": motiv_afara(z)}
    if "fereastra" not in r:
        r["fereastra"] = fereastra_strada(referinta, strazi, cfg, ancore, net)
    return r


def _geocodeaza(referinta: dict, strazi: list[dict], cfg: dict, net: dict, ancore: list[dict] | None = None) -> dict:
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
    if len(gasite) == 1 and loc == "strada":  # a doua stradă numită în reper („intersecția cu X”, „aproape de X”)
        k2 = _alta(reper, g, gasite[0][0])
        if k2:
            gasite.append((k2, False))
    ai = any(a for _, a in gasite)
    metoda, f = ("ai_estimare", c["factor_ai_fuzzy"]) if ai else ("osm_cache", 1.0)
    how = "ales de AI dintre străzile din cache" if ai else "potrivire exactă a numelui"
    e1 = g[gasite[0][0]]
    if len(gasite) == 2 and gasite[0][0] != gasite[1][0]:
        e2 = g[gasite[1][0]]
        d, a, b = min((_ax(a, b), a, b) for c1 in e1["cai"] for c2 in e2["cai"] for a in c1 for b in c2)
        if d <= 2 * c["precizie_intersectie_m"] + 30:  # vârfurile cele mai apropiate; mai departe = nu se intersectează
            return _rez("gasit", f"intersecția {e1['nume']} cu {e2['nume']} ({how}); capete la {d:.0f} m",
                        round((a[0] + b[0]) / 2, 6), round((a[1] + b[1]) / 2, 6), c["precizie_intersectie_m"],
                        metoda, c["acuratete"]["intersectie"] * f)
    if nr.isdigit() and loc == "strada":
        w = fereastra_strada(referinta, strazi, cfg, ancore, net)  # V6: ancore sau convenție (nu mai fracția N/100)
        if w["status"] != "necunoscut" and w["punct"]:
            return {**_rez("gasit", f"{w['motiv']} ({how})", w["punct"]["lat"], w["punct"]["lon"], w["precizie_m"], metoda,
                           w["acuratete"]), "fereastra": w}
    p = _la(e1["pct"], 0.5)
    pr = c["precizie_reper_m"] if loc == "reper" else min(max(e1["lung"] / 2, c["precizie_strada_min_m"]),
                                                          c["precizie_strada_max_m"])
    return _rez("gasit", f"{'reper pe ' if loc == 'reper' else 'mijlocul străzii '}{e1['nume']} ({how})",
                round(p[0], 6), round(p[1], 6), pr, metoda, c["acuratete"][loc] * f)


_FRAZA_STRADA = re.compile(r"\b(?:la\s+)?(?:intrarea\s+pe|inceputul|capatul)\s+(?:strada|strazii|str)\b\.?")
_SOSEA = _norm("Șoseaua Principală")  # cheia în `_grupe`: reperul pentru capătul de start al numerotării


def _fara_fereastra(motiv: str, ind: dict | None = None) -> dict:
    return {"status": "necunoscut", "strada": None, "de_la_m": None, "pana_la_m": None, "punct": None, "precizie_m": None,
            "metoda": None, "indiciu": ind, "ancore_folosite": [], "latura": None, "acuratete": 0.0, "motiv": motiv, "linie": []}


def fereastra_strada(referinta: dict, strazi: list[dict], cfg: dict, ancore: list[dict] | None = None,
                     net: dict | None = None) -> dict:
    """Fereastra de căutare pe stradă pentru o adresă parțială (V6, D11): „stâlp căzut pe Strada Viilor, lângă nr. 15”.

    Intrare: `referinta.adresa_structurata {strada, numar, reper, indiciu}` sau `referinta.adresa` (text liber). Dacă
    `indiciu` lipsește, se deduce determinist din text (regex, `fereastra.deduce_indiciu`). `strazi` = `osm.strazi()`;
    `cfg` = weights.yaml (secțiunile `cautare_strada`, `geocodare`, `zona`); `ancore` = adrese deja cunoscute
    `[{strada, numar, lat, lon}]` (le dă motorul; doar cele de pe aceeași stradă contează); `net` = rețeaua de start
    (centru pentru zonă și noduri pentru indiciul `element`; None = încărcată o dată în modul).

    Ieșire: {status: gasit|necunoscut|in_afara_zonei, strada, de_la_m, pana_la_m (distanțe de-a lungul căii, de la capătul de
    start al numerotării), punct {lat, lon}, precizie_m, metoda: ancore|conventie|indiciu, indiciu {tip, numar, numar_2,
    strada_2, element_id, distanta_stalpi, paritate, sursa: extractie|regex} | None, ancore_folosite [{strada, numar, lat,
    lon, pozitie_m}], latura: par|impar|None, acuratete, motiv (română), linie [[lat, lon], ...] (porțiunea din fereastră)}.
    Doar strada, fără indiciu: toată strada e fereastra (metoda `indiciu`, acuratețea `geocodare.acuratete.strada`).
    Determinist, fără AI aici (numele străzii se alege ca în `geocodeaza`: potrivire exactă, apoi cache/CLI AI din listă);
    punct în afara zonei de `zona.raza_max_m` = `in_afara_zonei`. Stradă negăsită = `necunoscut` (nu inventează nimic)."""
    ad = referinta.get("adresa_structurata") or {}
    strada, reper, adresa = ad.get("strada") or "", ad.get("reper") or "", referinta.get("adresa") or ""
    if not strada and not reper:
        strada = adresa
    din_reper = not strada
    if din_reper:
        strada = reper
    if not strada.strip():
        return _fara_fereastra("adresa nu conține stradă sau reper")
    g = _grupe(strazi)
    if not g:
        return _fara_fereastra("cache OSM de străzi indisponibil")
    parti = [p for p in _SEP.split(strada) if p.strip()][:2]
    curat = _FRAZA_STRADA.sub(" ", _fara_diac(parti[0]))  # „la intrarea pe stradă” nu e numele unei străzi
    k1, ai = _gaseste(curat if curat.strip() != _fara_diac(parti[0]).strip() and _norm(curat) else parti[0], g, cfg)
    if k1 is None:
        return _fara_fereastra(f"nicio stradă din cache nu se potrivește cu „{strada}”")
    ind = _fer.normalizeaza_indiciu(ad.get("indiciu"), ad.get("numar"))
    sursa = "extractie"
    text = " ".join(dict.fromkeys(x for x in (strada, reper, adresa) if x))  # părți distincte (strada poate fi chiar `adresa`)
    if ind is None:
        ind, sursa = _fer.deduce_indiciu(text, ad.get("numar")), "regex"
    k2_text = (ind or {}).get("strada_2") if (ind or {}).get("tip") == "colt" else None
    if (ind is None or (ind["tip"] == "colt" and not k2_text)) and len(parti) == 2:  # „X colț cu Y” în câmpul strada
        ind, k2_text = {**dict.fromkeys(_fer.CHEI_INDICIU), "tip": "colt", "strada_2": parti[1]}, parti[1]
    k2 = None
    if k2_text:
        k2 = _gaseste(k2_text, g, cfg)[0]
    elif ind is None and not din_reper:  # reperul numește a doua stradă din cache: intersecție (ca în geocodeaza)
        k2 = _alta(reper, g, k1)
        if k2:
            ind, sursa = {**dict.fromkeys(_fer.CHEI_INDICIU), "tip": "colt", "strada_2": g[k2]["nume"]}, "regex"
    if k2 == k1:
        k2 = None
    if ind is not None:
        ind = {**ind, "sursa": sursa}
    net = _net_implicit(net)
    e1 = g[k1]
    cale, _ = _fer.orienteaza(e1["pct"], g[_SOSEA]["cai"] if _SOSEA in g else None, centru_retea(net), k1 == _SOSEA)
    anc = [a for a in ancore or [] if _norm(a.get("strada")) == k1]
    r = _fer.calculeaza(e1, ind, cfg, cale, anc, net, g[k2] if k2 else None, _fer.sens_din_text(text), din_reper)
    if ai:  # numele străzii ales de AI: aceeași penalizare ca în geocodeaza
        r["acuratete"] = round(r["acuratete"] * cfg["geocodare"]["factor_ai_fuzzy"], 3)
        r["motiv"] += " Strada a fost aleasă de AI dintre cele din cache."
    z = zona_ok(r["punct"]["lat"], r["punct"]["lon"], net, cfg)
    status, motiv = ("gasit", r["motiv"]) if z["ok"] else ("in_afara_zonei", motiv_afara(z))
    return {"status": status, **{**r, "motiv": motiv}}
