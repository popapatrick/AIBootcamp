"""Generator de tură pentru tracking echipe (Sesiunea 4b, B1). Pur, determinist pe seed, fără rețea și fără AI."""
from __future__ import annotations

import hashlib
import math
import random
from datetime import datetime, timedelta

from backend.engine import osm
from backend.engine.network import dist_m
from backend.engine.scoring import banda
from backend.engine.zona import zona_ok
from backend.trace import _dist_strada

M = 111_320                  # metri per grad de latitudine
DIST_STRADA_MAX_M = 40.0     # un stâlp ales e la cel mult atât de o stradă OSM (contract)
DIST_STRADA_BUN_M = 25.0     # preferat intern: cobor din stradă spre stâlp rămâne scurt (mersul rămâne aproape de stradă)
SEPARARE_M = 60.0            # opririle diferite sunt la cel puțin atât una de alta (altfel gaseste_opriri le-ar putea lipi)
MARGINE_ZONA_M = 100.0       # punctele alese stau la cel puțin atât în interiorul zonei de 3 km (zgomotul GPS nu o depășește)
STALP_DURATA_MIN = (6.0, 10.0)
STALP_DECALAJ_M = (3.0, 8.0)
FARA_STALP_DURATA_MIN = 15.0
SCURTA_DURATA_MIN = (1.0, 2.0)
RAZE_TURA_M = (500, 800, 1300, 3000)   # cât de departe de primul stâlp se caută restul (se lărgește dacă nu ajung)
INCERCARI = 8


def _rng(*parti) -> random.Random:
    h = hashlib.sha256("|".join(str(p) for p in parti).encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


def _xy(p, o, k):
    """(lat, lon) -> metri față de originea `o`."""
    return ((p[1] - o[1]) * M * k, (p[0] - o[0]) * M)


def _latlon(xy, o, k):
    return (o[0] + xy[1] / M, o[1] + xy[0] / (M * k))


def _lung(xys) -> float:
    return sum(math.dist(a, b) for a, b in zip(xys, xys[1:]))


def _pe_linie(xys, s):
    """Punct la distanța `s` de la începutul poliliniei (limitat la capete)."""
    for a, b in zip(xys, xys[1:]):
        L = math.dist(a, b)
        if L > 0 and s <= L:
            return (a[0] + (b[0] - a[0]) * s / L, a[1] + (b[1] - a[1]) * s / L)
        s -= L
    return xys[-1]


def _taie(xys, s):
    """Împarte polilinia în două la distanța `s`: (prima parte, a doua parte), ambele cu punctul de tăiere."""
    c = _pe_linie(xys, s)
    acc, i = 0.0, 0
    for i, (a, b) in enumerate(zip(xys, xys[1:])):
        L = math.dist(a, b)
        if s <= acc + L:
            break
        acc += L
    else:
        i = len(xys) - 2
    return xys[:i + 1] + [c], [c] + xys[i + 1:]


def _puncte_pe_strazi(strazi, pas_m=10.0):
    """Puncte (lat, lon) din 10 în 10 m de-a lungul străzilor (candidate pentru locul fără stâlp)."""
    out = []
    for s in strazi:
        w = [tuple(p) for p in s["puncte"]]
        for a, b in zip(w, w[1:]):
            L = dist_m(a, b)
            for j in range(max(1, int(L // pas_m))):
                f = j * pas_m / L if L else 0
                out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def _legatura(a, b):
    """Drum pe străzi de la a la b (lat, lon): (puncte, pe_strada). Fără drum: linie dreaptă, pe_strada=False."""
    r = osm.traseu(a, b)
    if r and len(r["puncte"]) >= 2:
        return [tuple(p) for p in r["puncte"]], True
    return [a, b], False


def _alege(net, strazi, cfg, scoruri, rng, n):
    """Alege n stâlpi existenți + locul fără stâlp. Întoarce (stalpi [(id, lat, lon)], loc (lat, lon)) sau None."""
    t = cfg["tracking"]
    raza_zona = float((cfg.get("zona") or {}).get("raza_max_m", 3000.0)) - MARGINE_ZONA_M
    ways = [[tuple(p) for p in s["puncte"]] for s in strazi]
    c = _centru(net)

    def in_zona(lat, lon):
        return dist_m(c, (lat, lon)) <= raza_zona

    cand = []
    for nid in sorted(net["noduri"]):
        nd = net["noduri"][nid]
        if str(nid).endswith("-casa") or nd.get("tip_element") not in (None, "nod") or not in_zona(nd["lat"], nd["lon"]):
            continue
        d = _dist_strada((nd["lat"], nd["lon"]), ways) if ways else 0.0
        if d <= DIST_STRADA_MAX_M:
            cand.append((nid, nd["lat"], nd["lon"], d))
    if len(cand) < n:
        return None
    verde = lambda nid: scoruri is None or nid not in scoruri or banda(scoruri[nid], cfg) == "verde"
    preferat = lambda e: scoruri is not None and not verde(e[0])
    buni = [e for e in cand if e[3] <= DIST_STRADA_BUN_M]
    baza = buni if len(buni) >= n else cand

    # ancora: preferat un stâlp care nu e verde
    ancora_pool = [e for e in baza if preferat(e)] or baza
    ancora = rng.choice(ancora_pool)
    alesi = None
    for raza in RAZE_TURA_M:
        pool = [e for e in baza if dist_m((ancora[1], ancora[2]), (e[1], e[2])) <= raza]
        rng.shuffle(pool)
        pool.sort(key=lambda e: 0 if preferat(e) else 1)     # sort stabil: nu-verzii primii, ordinea din shuffle
        sel = [ancora]
        for e in pool:
            if len(sel) == n:
                break
            if e not in sel and all(dist_m((e[1], e[2]), (s[1], s[2])) >= SEPARARE_M for s in sel):
                sel.append(e)
        if len(sel) == n:
            alesi = sel
            break
    if not alesi:
        return None

    # locul fără stâlp: pe o stradă, la >= raza_fara_stalp_m + 10 m de orice nod, aproape de stâlpii aleși
    prag = t["raza_fara_stalp_m"] + 10.0
    noduri = [(v["lat"], v["lon"]) for v in net["noduri"].values()]
    if net.get("post"):
        noduri.append((net["post"]["lat"], net["post"]["lon"]))
    cm = (sum(e[1] for e in alesi) / n, sum(e[2] for e in alesi) / n)
    pct = [p for p in _puncte_pe_strazi(strazi) if in_zona(*p)]
    for raza in RAZE_TURA_M:
        loc = [p for p in pct if dist_m(cm, p) <= raza
               and all(dist_m(p, q) >= prag for q in noduri)
               and all(dist_m(p, (e[1], e[2])) >= SEPARARE_M for e in alesi)]
        if loc:
            return [(e[0], e[1], e[2]) for e in alesi], rng.choice(loc)
    return None


def _centru(net):
    from backend.engine.zona import centru_retea
    return centru_retea(net)


def _ordoneaza(puncte):
    """Cel mai apropiat următor, pornind de la capătul cel mai îndepărtat de centroidul punctelor."""
    cm = (sum(p["lat"] for p in puncte) / len(puncte), sum(p["lon"] for p in puncte) / len(puncte))
    rest = sorted(puncte, key=lambda p: -dist_m(cm, (p["lat"], p["lon"])))
    cur = rest.pop(0)
    out = [cur]
    while rest:
        j = min(range(len(rest)), key=lambda i: dist_m((cur["lat"], cur["lon"]), (rest[i]["lat"], rest[i]["lon"])))
        cur = rest.pop(j)
        out.append(cur)
    return out


def genereaza_tura(net: dict, strazi: list[dict], cfg: dict, echipa: str, seed: str, data: str,
                   scoruri: dict | None = None, ora_start: str = "08:00:00") -> dict:
    """Tură simulată a tabletei unei echipe, determinist pe (echipa, data, seed): aceleași intrări = aceeași ieșire.

    Parametri:
      net      rețeaua motorului ({noduri, post?, ...}); stâlpii existenți = `net["noduri"]` (fără `*-casa`, fără predicții,
               care nu sunt în `net`). Pentru rețeaua completă de start: `load_network()` + `incarca_puncte_simulare(net)`.
      strazi   `backend.engine.osm.strazi()`; drumurile între puncte merg pe graful OSM local (`osm.traseu`), cu linie dreaptă
               doar când nu există drum (numărate în `linie_dreapta`; se reîncearcă alte alegeri înainte să se accepte o linie dreaptă).
      cfg      weights.yaml încărcat: `tracking` (stalpi_min/max, raza_fara_stalp_m, viteza_m_s, pas_s, zgomot_m, ...),
               `trace.raza_oprire_m` (zgomotul din opriri nu rupe grupul), `culori`, `zona`.
      echipa   mentenanta | investitii | racordari. seed: text; data: `YYYY-MM-DD`; ora_start: `HH:MM:SS` (implicit 08:00:00).
      scoruri  opțional {element_id: scor curent}, dat de cine apelează; stâlpii cu bandă galben/portocaliu/roșu sunt preferați
               ca validarea să se vadă. Fără `scoruri`, se aleg stâlpi oarecare (determinist).

    Ce face: alege `stalpi_min`..`stalpi_max` stâlpi existenți din zona de 3 km (la <= 40 m de o stradă, la >= 60 m unul de altul,
    grupați într-o zonă restrânsă) și un loc fără stâlp pe o stradă, la >= `raza_fara_stalp_m` + 10 m de orice nod; îi ordonează
    „cel mai apropiat următor” de la un capăt; adaugă 1–2 opriri scurte (1–2 min) pe drum; mers cu `viteza_m_s`, un punct la
    `pas_s` secunde, zgomot gaussian `zgomot_m` (în opriri zgomotul e plafonat la 0,4 × `trace.raza_oprire_m`, ca opririle
    să rămână detectabile). Opriri: stâlp 6–10 min la 3–8 m de stâlp; loc fără stâlp 15 min.

    Întoarce {tura_id, echipa, data, seed, puncte: [{t, lat, lon}], plan: [{lat, lon, durata_min, tip_plan: stalp|fara_stalp|scurta,
    element_id?}] (cronologic; doar pentru depanare și teste, motorul NU îl folosește), lungime_m, durata_min,
    linie_dreapta: câte legături nu au drum pe străzi}. `tura_id` e stabil (echipă + dată + seed).
    Ridică ValueError dacă nu se poate alcătui o tură (prea puțini stâlpi în zonă sau fără străzi)."""
    t = cfg["tracking"]
    h = hashlib.sha256(f"{echipa}|{data}|{seed}".encode()).hexdigest()[:8]
    tura_id = f"TURA-{echipa}-{data.replace('-', '')}-{h}"
    rng = _rng("tura", echipa, data, seed)
    zg = _rng("zgomot", echipa, data, seed)
    cap = 0.4 * cfg["trace"]["raza_oprire_m"] if t["zgomot_m"] <= cfg["trace"]["raza_oprire_m"] else 0.0
    if not strazi:
        raise ValueError("fără străzi OSM: nu se poate genera o tură")

    rezerva = None   # prima tură în zonă, dar cu legături în linie dreaptă (folosită dacă nicio încercare nu are drumuri pe străzi)
    for _ in range(INCERCARI):
        n = rng.randint(int(t["stalpi_min"]), int(t["stalpi_max"]))
        alegere = _alege(net, strazi, cfg, scoruri, rng, n)
        if not alegere:
            continue
        stalpi, loc = alegere
        puncte = []
        for nid, la, lo in stalpi:
            ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(*STALP_DECALAJ_M)
            k = math.cos(math.radians(la))
            c = (la + r * math.sin(ang) / M, lo + r * math.cos(ang) / (M * k))
            puncte.append({"lat": c[0], "lon": c[1], "durata_min": round(rng.uniform(*STALP_DURATA_MIN), 1),
                           "tip_plan": "stalp", "element_id": nid})
        puncte.append({"lat": loc[0], "lon": loc[1], "durata_min": FARA_STALP_DURATA_MIN, "tip_plan": "fara_stalp"})
        ordine = _ordoneaza(puncte)

        o = (ordine[0]["lat"], ordine[0]["lon"])
        k = math.cos(math.radians(o[0]))
        # legături pe străzi între opriri consecutive, în metri față de origine
        legaturi, drept = [], 0
        for a, b in zip(ordine, ordine[1:]):
            drum, pe_strada = _legatura((a["lat"], a["lon"]), (b["lat"], b["lon"]))
            drept += 0 if pe_strada else 1
            legaturi.append([_xy(p, o, k) for p in drum])

        # opriri scurte (1–2) la mijlocul unor legături lungi, la distanță de celelalte opriri
        centre = [_xy((p["lat"], p["lon"]), o, k) for p in ordine]
        scurte = {}   # index legătură -> (fracție, durată)
        lungi = [i for i, L in enumerate(legaturi) if _lung(L) >= 150]
        rng.shuffle(lungi)
        for i in lungi[:rng.randint(1, 2)]:
            scurte[i] = (rng.uniform(0.35, 0.65), round(rng.uniform(*SCURTA_DURATA_MIN), 1))

        # cronologia: segmente (t0, t1, "mers", polilinie) / (t0, t1, "sta", centru)
        seg, tt, plan, lungime = [], 0.0, [], 0.0
        v = t["viteza_m_s"]

        def sta(centru, durata_min):
            nonlocal tt
            seg.append((tt, tt + durata_min * 60, "sta", centru))
            tt += durata_min * 60

        def mers(poli):
            nonlocal tt, lungime
            L = _lung(poli)
            if L > 0:
                seg.append((tt, tt + L / v, "mers", poli))
                tt += L / v
                lungime += L

        for i, p in enumerate(ordine):
            sta(centre[i], p["durata_min"])
            plan.append({"lat": round(p["lat"], 7), "lon": round(p["lon"], 7), "durata_min": p["durata_min"],
                         "tip_plan": p["tip_plan"], **({"element_id": p["element_id"]} if "element_id" in p else {})})
            if i < len(legaturi):
                L = legaturi[i]
                if i in scurte:
                    f, dur = scurte[i]
                    a, b = _taie(L, _lung(L) * f)
                    mers(a)
                    c = a[-1]
                    sta(c, dur)
                    ll = _latlon(c, o, k)
                    plan.append({"lat": round(ll[0], 7), "lon": round(ll[1], 7), "durata_min": dur, "tip_plan": "scurta"})
                    mers(b)
                else:
                    mers(L)

        # puncte GPS la `pas_s`, cu zgomot
        pas = t["pas_s"]
        start = datetime.fromisoformat(f"{data}T{ora_start}")
        pts, j = [], 0
        for kk in range(int(tt // pas) + 1):
            ts = kk * pas
            while j < len(seg) - 1 and ts > seg[j][1]:
                j += 1
            t0, t1, tip, d = seg[j]
            if tip == "sta":
                x, y = d
            else:
                x, y = _pe_linie(d, max(0.0, (ts - t0) * v))
            gx, gy = zg.gauss(0, t["zgomot_m"]), zg.gauss(0, t["zgomot_m"])
            if tip == "sta" and cap and math.hypot(gx, gy) > cap:
                f = cap / math.hypot(gx, gy)
                gx, gy = gx * f, gy * f
            la, lo = _latlon((x + gx, y + gy), o, k)
            pts.append({"t": (start + timedelta(seconds=ts)).isoformat(timespec="seconds"),
                        "lat": round(la, 7), "lon": round(lo, 7)})
        if all(zona_ok(p["lat"], p["lon"], net, cfg)["ok"] for p in pts):
            tura = {"tura_id": tura_id, "echipa": echipa, "data": data, "seed": str(seed), "puncte": pts, "plan": plan,
                    "lungime_m": round(lungime, 1), "durata_min": round(tt / 60, 1), "linie_dreapta": drept}
            if drept == 0:
                return tura
            rezerva = rezerva or tura
    if rezerva:
        return rezerva
    raise ValueError("nu s-a putut genera o tură în zona prototipului")
