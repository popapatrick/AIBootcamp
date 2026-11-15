"""Fereastra de căutare pe stradă (Sesiunea 4, V6, `cautare_strada` din weights.yaml). Date FICTIVE.

Modul pur și determinist: geometrie pe calea unei străzi + deducerea indiciului din text. Nu apelează AI și nu
citește fișiere; rezolvarea numelui străzii (cu AI) și safeguardul de zonă sunt în `backend.geo.fereastra_strada`.

Convenții (documentate și în docs/etapa-31-cautare-strada.md):
- Distanțele (`de_la_m`, `pana_la_m`) se măsoară de-a lungul celei mai lungi căi a străzii, de la capătul de START.
- Capătul de start = capătul căii cel mai apropiat de Șoseaua Principală (dacă e la < 300 m); pentru Șoseaua
  Principală sau o stradă fără capăt la < 300 m de ea: capătul cel mai apropiat de centrul rețelei.
- Numerele cresc de la start spre celălalt capăt; ~`metri_per_numar` m de stradă pentru fiecare număr.
- Pare = stânga, impare = dreapta (privind în sensul de creștere a numerelor), la `decalaj_paritate_m` de ax.
"""
from __future__ import annotations

import math
import re
import unicodedata

from backend.engine.network import dist_m

TIPURI = ("numar", "langa", "vizavi", "intre", "dupa", "inainte", "capat", "inceput", "colt", "element", "parte")
CHEI_INDICIU = ("tip", "numar", "numar_2", "strada_2", "element_id", "distanta_stalpi", "paritate")
PRAG_SOSEA_M = 300.0   # capătul „de start” se alege față de Șoseaua Principală doar dacă e la mai puțin de atât
METRI_STALP = 40.0     # distanța medie dintre doi stâlpi (plan V6: „element: ±(distanță × 40 m)”)
PRECIZIE_MIN_INTRE_M = 20.0
LATERAL_MAX_ELEMENT_M = 150.0  # un element mai departe de axul străzii nu e „pe stradă”


def fara_diac(s: str) -> str:
    """Text fără diacritice, litere mici."""
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


# ---------------------------------------------------------------- indiciul din text (fallback regex)
_NRX = r"(?:nr\.?|numarul|numerele|numar|no\.?)?\s*"
_ID = r"(\d{5,}|[a-z]{1,4}\d*(?:-[a-z0-9]+)+)"
_RX = [  # (tip, regex pe text fără diacritice, litere mici); ordinea contează (specific înainte de general)
    ("element", re.compile(r"(\d+)\s+stalpi\s+de\s+(?:stalpul\s+|nodul\s+|postul\s+)?" + _ID)),
    ("element", re.compile(r"\b(?:langa|in dreptul|la|aproape de)\s+(?:stalpul|stalp|nodul|postul)\s+(?:nr\.?\s*)?" + _ID)),
    ("colt", re.compile(r"\b(?:colt|intersectia|intersectie)\s+cu\s+([^,;.\d]+)")),
    ("intre", re.compile(r"\bintre\s+" + _NRX + r"(\d+)\s*(?:si|-|–)\s*" + _NRX + r"(\d+)")),
    ("vizavi", re.compile(r"\bvizavi(?:\s+de)?\s+" + _NRX + r"(\d+)")),
    ("dupa", re.compile(r"\bdupa\s+" + _NRX + r"(\d+)")),
    ("inainte", re.compile(r"\binainte\s+de\s+" + _NRX + r"(\d+)")),
    ("langa", re.compile(r"\b(?:langa|in dreptul|in apropiere de|aproape de)\s+" + _NRX + r"(\d{1,4})\b")),
    ("capat", re.compile(r"\b(?:la\s+)?capatul\s+(?:strazii|str)\b|\bla\s+capat\b|\bcapatul\s+strazii")),
    ("inceput", re.compile(r"\bla\s+intrarea\s+pe\s+strada|\b(?:la\s+)?inceputul\s+strazii|\bintrarea\s+pe\s+strada")),
    ("numar", re.compile(r"\b(?:nr\.?|numarul|numar|no\.?)\s*(\d+)")),
    ("parte", re.compile(r"\bpartea\s+(?:cu\s+)?(?:numere(?:le)?\s+)?(pare|impare)|\bnumere(?:le)?\s+(pare|impare)")),
]
_NUMAR_FINAL = re.compile(r"(?<![\w-])(\d{1,3})\s*$")
_SPRE_CAPAT = re.compile(r"\bspre\s+(?:capat|capatul)|\bcatre\s+capat")
_SPRE_INCEPUT = re.compile(r"\bspre\s+(?:inceput|inceputul|intrare|intrarea)|\bcatre\s+(?:inceput|intrare)")


def deduce_indiciu(text: str, numar_adresa: str | None = None) -> dict | None:
    """Indiciul de loc dedus determinist din `text` (română, cu sau fără diacritice) sau None.

    Întoarce {tip, numar, numar_2, strada_2, element_id, distanta_stalpi, paritate} (cheile nefolosite None).
    `numar_adresa` (câmpul structurat `numar`) dă tipul `numar` când textul nu spune altceva. Fără număr și fără
    formulare recunoscută: None. Exemple: „lângă nr 15” -> langa/15; „între nr 10 și 20” -> intre/10/20;
    „la 2 stâlpi de 7101969” -> element/7101969/2; „colț cu Strada Soarelui” -> colt/„strada soarelui”."""
    t = fara_diac(text)
    for tip, rx in _RX:
        m = rx.search(t)
        if not m:
            continue
        ind = dict.fromkeys(CHEI_INDICIU)
        ind["tip"] = tip
        if tip == "element":
            if m.re.pattern.startswith(r"(\d+)"):
                ind["distanta_stalpi"], ind["element_id"] = int(m.group(1)), m.group(2).upper()
            else:
                ind["element_id"] = m.group(1).upper()
        elif tip == "colt":
            ind["strada_2"] = " ".join(m.group(1).split())
        elif tip == "intre":
            ind["numar"], ind["numar_2"] = m.group(1), m.group(2)
        elif tip == "parte":
            ind["paritate"] = "par" if (m.group(1) or m.group(2)) == "pare" else "impar"
        elif tip in ("langa", "vizavi", "dupa", "inainte", "numar"):
            ind["numar"] = m.group(1)
        return ind
    m = _NUMAR_FINAL.search(t.strip())
    nr = (m.group(1) if m else None) or (str(numar_adresa).strip() if numar_adresa and str(numar_adresa).strip().isdigit() else None)
    if nr:
        return {**dict.fromkeys(CHEI_INDICIU), "tip": "numar", "numar": nr}
    return None


def normalizeaza_indiciu(ind: dict | None, numar_adresa: str | None = None) -> dict | None:
    """Indiciul extras (din eveniment) adus la forma completă; tip invalid sau gol = None. Numărul lipsă se ia din `numar_adresa`."""
    if not isinstance(ind, dict) or ind.get("tip") not in TIPURI:
        return None
    out = {k: ind.get(k) for k in CHEI_INDICIU}
    for k in ("numar", "numar_2"):
        if out[k] is not None:
            out[k] = str(out[k]).strip() or None
    if out["paritate"] is not None:
        out["paritate"] = {"par": "par", "pare": "par", "impar": "impar", "impare": "impar"}.get(fara_diac(str(out["paritate"])))
    if out["tip"] in ("numar", "langa", "vizavi", "intre", "dupa", "inainte") and not out["numar"] and numar_adresa:
        out["numar"] = str(numar_adresa).strip()
    if out["tip"] in ("numar", "langa", "vizavi", "intre", "dupa", "inainte") and not (out["numar"] or "").isdigit():
        return None  # fără număr valid, indiciul nu poate fi folosit
    return out


def sens_din_text(text: str) -> int:
    """+1 dacă textul zice „spre capăt”, -1 pentru „spre început/intrare”, 0 altfel (folosit la indiciul `element`)."""
    t = fara_diac(text)
    return 1 if _SPRE_CAPAT.search(t) else -1 if _SPRE_INCEPUT.search(t) else 0


# ---------------------------------------------------------------- geometrie pe calea străzii
def _m(a, b):  # (lat, lon) -> metri est/nord ai lui b față de a (plan local)
    return (b[1] - a[1]) * 111_320 * math.cos(math.radians(a[0])), (b[0] - a[0]) * 111_320


def _proiect_seg(p, u, v):
    """(t în [0,1], distanță_m) a proiecției lui p pe segmentul u-v."""
    ax, ay = _m(p, u)
    bx, by = _m(p, v)
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / l2))
    return t, math.hypot(ax + t * dx, ay + t * dy)


class Cale:
    """Calea unei străzi orientată de la capătul de start: poziții în metri de-a lungul ei."""

    def __init__(self, pct):
        self.p = [tuple(x) for x in pct]
        self.cum = [0.0]
        for a, b in zip(self.p, self.p[1:]):
            self.cum.append(self.cum[-1] + dist_m(a, b))
        self.L = self.cum[-1]

    def clamp(self, s: float) -> float:
        return max(0.0, min(self.L, s))

    def la(self, s: float) -> tuple[float, float]:
        """Punctul (lat, lon) la `s` m de start."""
        s = self.clamp(s)
        for i in range(len(self.p) - 1):
            if self.cum[i + 1] >= s and self.cum[i + 1] > self.cum[i]:
                t = (s - self.cum[i]) / (self.cum[i + 1] - self.cum[i])
                a, b = self.p[i], self.p[i + 1]
                return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        return self.p[-1]

    def proiecteaza(self, p) -> tuple[float, float]:
        """(s, distanță laterală m) a proiecției lui p pe cale."""
        best = (float("inf"), 0.0)
        for i in range(len(self.p) - 1):
            t, d = _proiect_seg(p, self.p[i], self.p[i + 1])
            if d < best[0]:
                best = (d, self.cum[i] + t * (self.cum[i + 1] - self.cum[i]))
        return best[1], best[0]

    def lateral(self, s: float, m: float) -> tuple[float, float]:
        """Punctul de la `s` decalat cu `m` metri la STÂNGA axei (m negativ = dreapta), privind spre numere mari."""
        s = self.clamp(s)
        p = self.la(s)
        i = max(0, min(len(self.p) - 2, next((j for j in range(len(self.p) - 1) if self.cum[j + 1] >= s), len(self.p) - 2)))
        dx, dy = _m(self.p[i], self.p[i + 1])
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n, dx / n  # normala stângă
        return p[0] + ny * m / 111_320, p[1] + nx * m / (111_320 * math.cos(math.radians(p[0])))

    def linie(self, s0: float, s1: float) -> list[list[float]]:
        """Porțiunea căii între `s0` și `s1`, ca [[lat, lon], ...] rotunjit (pentru UI)."""
        s0, s1 = self.clamp(min(s0, s1)), self.clamp(max(s0, s1))
        pts = [self.la(s0)] + [self.p[i] for i in range(len(self.p)) if s0 < self.cum[i] < s1] + [self.la(s1)]
        return [[round(a, 6), round(b, 6)] for a, b in pts]


def _dist_la_cai(p, cai) -> float:
    return min((_proiect_seg(p, c[i], c[i + 1])[1] for c in cai for i in range(len(c) - 1)), default=float("inf"))


def orienteaza(pct, cai_sosea: list | None, centru: tuple[float, float], e_sosea: bool) -> tuple[Cale, str]:
    """Calea străzii (`pct`) orientată de la capătul de start; întoarce (Cale, motivul alegerii capătului).

    Regula: capătul cel mai apropiat de Șoseaua Principală (`cai_sosea`) dacă e la < 300 m; altfel (sau pentru
    Șoseaua Principală, `e_sosea`) capătul cel mai apropiat de `centru` (centrul rețelei)."""
    a, b = tuple(pct[0]), tuple(pct[-1])
    if not e_sosea and cai_sosea:
        da, db = _dist_la_cai(a, cai_sosea), _dist_la_cai(b, cai_sosea)
        if min(da, db) < PRAG_SOSEA_M:
            return (Cale(pct) if da <= db else Cale(pct[::-1])), "capătul dinspre Șoseaua Principală"
    ca, cb = dist_m(a, centru), dist_m(b, centru)
    return (Cale(pct) if ca <= cb else Cale(pct[::-1])), "capătul dinspre centrul rețelei"


# ---------------------------------------------------------------- poziția numerelor
def _cifra(x) -> int | None:
    return int(x) if x is not None and str(x).strip().isdigit() else None


def _par(n: int) -> str:
    return "par" if n % 2 == 0 else "impar"


def ancore_pe_cale(cale: Cale, ancore: list[dict]) -> list[dict]:
    """Ancorele {strada, numar, lat, lon} cu număr valid, proiectate pe cale: [{numar:int, s, strada, lat, lon}] sortat după număr
    (la același număr rămâne prima)."""
    out: dict[int, dict] = {}
    for a in ancore or []:
        n = _cifra(a.get("numar"))
        if n is None or a.get("lat") is None or a.get("lon") is None:
            continue
        s, _ = cale.proiecteaza((float(a["lat"]), float(a["lon"])))
        out.setdefault(n, {"numar": n, "s": s, "strada": a.get("strada"), "lat": float(a["lat"]), "lon": float(a["lon"])})
    return [out[k] for k in sorted(out)]


def pozitie_numar(n: int, cale: Cale, anc: list[dict], cfg_c: dict) -> tuple[float, str, list[dict]]:
    """(s, metoda, ancore_folosite) pentru numărul `n`: cu ancore interpolare/extrapolare, altfel convenția
    s = (n // 2) * 2 * metri_per_numar (plafonat la lungimea străzii)."""
    mpn = float(cfg_c["metri_per_numar"])
    if not anc:
        return cale.clamp((n // 2) * 2 * mpn), "conventie", []
    exact = next((a for a in anc if a["numar"] == n), None)
    if exact:
        return cale.clamp(exact["s"]), "ancore", [exact]
    lo = max((a for a in anc if a["numar"] < n), key=lambda a: a["numar"], default=None)
    hi = min((a for a in anc if a["numar"] > n), key=lambda a: a["numar"], default=None)
    if lo and hi:
        s = lo["s"] + (n - lo["numar"]) * (hi["s"] - lo["s"]) / (hi["numar"] - lo["numar"])
        return cale.clamp(s), "ancore", [lo, hi]
    if lo:
        return cale.clamp(lo["s"] + (n - lo["numar"]) * mpn), "ancore", [lo]
    return cale.clamp(hi["s"] - (hi["numar"] - n) * mpn), "ancore", [hi]


def _ancora_out(a: dict) -> dict:
    return {"strada": a["strada"], "numar": a["numar"], "lat": a["lat"], "lon": a["lon"], "pozitie_m": round(a["s"], 1)}


# ---------------------------------------------------------------- fereastra
def calculeaza(e1: dict, ind: dict | None, cfg: dict, cale: Cale, ancore: list[dict] | None = None,
               net: dict | None = None, e2: dict | None = None, sens: int = 0, din_reper: bool = False) -> dict:
    """Fereastra pe strada `e1` (intrare din `_grupe`) pentru indiciul `ind` (forma completă, sau None = doar strada).

    `cale` = calea orientată de la start (`orienteaza`); `ancore` = adrese cunoscute pe această stradă;
    `e2` = a doua stradă (pentru `colt`); `net` = rețeaua (pentru `element`); `sens` = +1/-1/0 pentru `element`.
    Întoarce {strada, de_la_m, pana_la_m, punct{lat,lon}, precizie_m, metoda, indiciu, ancore_folosite, latura, acuratete,
    motiv, linie}; statusul și safeguardul de zonă se pun în `backend.geo.fereastra_strada`."""
    c, g = cfg["cautare_strada"], cfg["geocodare"]
    dec, A = float(c["decalaj_paritate_m"]), g["acuratete"]
    nume, L = e1["nume"], cale.L
    anc = ancore_pe_cale(cale, ancore or [])
    tip = (ind or {}).get("tip")
    n, n2 = _cifra((ind or {}).get("numar")), _cifra((ind or {}).get("numar_2"))

    def rez(s0, s1, s_punct, precizie, metoda, acur, motiv, latura=None, folosite=(), punct=None):
        s0, s1 = cale.clamp(s0), cale.clamp(s1)
        if punct is None:
            sg = {"par": 1, "impar": -1}.get(latura, 0)
            punct = cale.lateral(s_punct, sg * dec) if sg else cale.la(s_punct)
        return {"strada": nume, "de_la_m": round(s0, 1), "pana_la_m": round(s1, 1),
                "punct": {"lat": round(punct[0], 6), "lon": round(punct[1], 6)}, "precizie_m": round(float(precizie), 1),
                "metoda": metoda, "indiciu": ind, "ancore_folosite": [_ancora_out(a) for a in folosite], "latura": latura,
                "acuratete": round(acur, 3), "motiv": motiv, "linie": cale.linie(s0, s1)}

    def acur_nr(metoda):
        return g["acuratete"]["strada_numar"] * (1.0 if metoda == "ancore" else float(c["factor_numere_conventie"]))

    def prec_nr(metoda):
        return float(c["precizie_ancore_m"] if metoda == "ancore" else c["precizie_conventie_m"])

    def sursa(metoda, folosite):
        return (f"din {len(folosite)} ancor{'ă' if len(folosite) == 1 else 'e'} de pe stradă" if metoda == "ancore"
                else "după convenția de numerotare (~12 m la 2 numere de la capătul de start)")

    def toata(prefix=""):
        loc = "reper" if din_reper and tip is None else "strada"
        return rez(0, L, L / 2, L / 2, "indiciu", A[loc],
                   f"{prefix}Nu există un indiciu de loc folosibil pe {nume}: toată strada ({L:.0f} m) e fereastra.")

    if tip in ("numar", "langa", "vizavi") and n is not None:
        s, metoda, fol = pozitie_numar(n, cale, anc, c)
        p = prec_nr(metoda)
        latura = _par(n) if tip != "vizavi" else _par(n + 1)
        eticheta = {"numar": f"nr. {n}", "langa": f"lângă nr. {n}", "vizavi": f"vizavi de nr. {n} (partea {latura})"}[tip]
        return rez(s - p, s + p, s, p, metoda, acur_nr(metoda), f"{nume}, {eticheta}: la {s:.0f} m de capătul de start, {sursa(metoda, fol)}; "
                   f"fereastră ±{p:.0f} m.", latura, fol)
    if tip == "intre" and n is not None:
        n2 = n2 if n2 is not None else n
        s1, m1, f1 = pozitie_numar(n, cale, anc, c)
        s2, m2, f2 = pozitie_numar(n2, cale, anc, c)
        metoda = "ancore" if "ancore" in (m1, m2) else "conventie"
        mij, p = (s1 + s2) / 2, max(abs(s2 - s1) / 2, PRECIZIE_MIN_INTRE_M)
        fol = list({id(a): a for a in f1 + f2}.values())
        return rez(mij - p, mij + p, mij, p, metoda, acur_nr(metoda), f"{nume}, între nr. {n} și {n2}: mijlocul la {mij:.0f} m de start, "
                   f"{sursa(metoda, fol)}; fereastră ±{p:.0f} m.", None, fol)
    if tip in ("dupa", "inainte") and n is not None:
        s, metoda, fol = pozitie_numar(n, cale, anc, c)
        w = float(c["fereastra_dupa_m"])
        s0, s1 = (s, s + w) if tip == "dupa" else (s - w, s)
        return rez(s0, s1, (cale.clamp(s0) + cale.clamp(s1)) / 2, (cale.clamp(s1) - cale.clamp(s0)) / 2, metoda, acur_nr(metoda),
                   f"{nume}, {'după' if tip == 'dupa' else 'înainte de'} nr. {n}: fereastră de {w:.0f} m, {sursa(metoda, fol)}.", None, fol)
    if tip in ("capat", "inceput"):
        pr = float(c["precizie_capat_m"])
        s = L if tip == "capat" else 0.0
        s0, s1 = (L - pr, L) if tip == "capat" else (0.0, pr)
        return rez(s0, s1, s, pr, "indiciu", A["strada_numar"] * float(c["factor_numere_conventie"]),
                   f"{nume}, la {'capătul străzii (la capătul opus startului)' if tip == 'capat' else 'începutul străzii (capătul de start)'}: "
                   f"fereastră de {pr:.0f} m la acel capăt.")
    if tip == "colt":
        if e2 is None:
            return toata(f"A doua stradă ({(ind or {}).get('strada_2')}) nu e în cache. ")
        pi = float(g["precizie_intersectie_m"])
        d, a, b = min((dist_m(a, b), a, b) for c1 in e1["cai"] for c2 in e2["cai"] for a in c1 for b in c2)
        if d > 2 * pi + 30:
            return toata(f"{nume} nu se intersectează cu {e2['nume']} (capete la {d:.0f} m). ")
        pc = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        s, _ = cale.proiecteaza(pc)
        return rez(s - pi, s + pi, s, pi, "indiciu", A["intersectie"], f"Intersecția {nume} cu {e2['nume']}: punctul comun la {s:.0f} m "
                   f"de start; fereastră ±{pi:.0f} m.", None, (), pc)
    if tip == "element":
        el = ((net or {}).get("noduri") or {}).get(str((ind or {}).get("element_id")))
        if el:
            s, lat = cale.proiecteaza((el["lat"], el["lon"]))
            if lat <= LATERAL_MAX_ELEMENT_M:
                ns = _cifra((ind or {}).get("distanta_stalpi")) or 1
                d = ns * METRI_STALP
                if sens:
                    s0, s1 = (s, s + d) if sens > 0 else (s - d, s)
                    s_p, p = s + sens * d / 2, d / 2
                    unde = f"spre {'capăt' if sens > 0 else 'început'}"
                else:
                    s0, s1, s_p, p = s - d, s + d, s, d
                    unde = "în ambele sensuri"
                return rez(s0, s1, s_p, p, "indiciu", A["strada_numar"], f"{nume}, la {ns} stâlp{'i' if ns > 1 else ''} de elementul "
                           f"{el['id']} (la {s:.0f} m de start, {lat:.0f} m de axul străzii), {unde}: fereastră de {d:.0f} m.")
            return toata(f"Elementul {el['id']} e la {lat:.0f} m de axul străzii. ")
        return toata(f"Elementul {(ind or {}).get('element_id')} nu e în rețea. ")
    if tip == "parte":
        latura = (ind or {}).get("paritate")
        latura = latura if latura in ("par", "impar") else None
        r = toata()
        if latura:
            r["latura"] = latura
            r["punct"] = dict(zip(("lat", "lon"), (round(x, 6) for x in cale.lateral(L / 2, dec if latura == "par" else -dec))))
            r["motiv"] = f"{nume}, partea cu numere {latura}e: toată strada ({L:.0f} m) e fereastra (fără număr)."
        return r
    return toata()
