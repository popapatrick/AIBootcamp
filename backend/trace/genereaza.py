"""Traseu GPS simulat pentru un raport (proprietar A). Pur, determinist pe seed, fără rețea."""
import hashlib
import math
import random
from datetime import datetime, timedelta

from backend.trace import _dist_segment

M = 111_320  # m per grad de latitudine
_VIT_M_S = 1.4  # mers
_BAZA = "2026-01-01T12:00:00"  # sfârșitul traseului când punctul nu are `t`



def _pe_linie(xy, s):
    """Punct la distanța s de-a lungul poliliniei; în afara capetelor extrapolează pe ultimul segment."""
    segs = [(xy[i], xy[i + 1], math.dist(xy[i], xy[i + 1])) for i in range(len(xy) - 1)]
    segs = [g for g in segs if g[2] > 0] or [((0, 0), (1, 0), 1)]
    if s < 0:
        a, b, L = segs[0]
        return a[0] + (b[0] - a[0]) / L * s, a[1] + (b[1] - a[1]) / L * s
    for a, b, L in segs:
        if s <= L:
            return a[0] + (b[0] - a[0]) / L * s, a[1] + (b[1] - a[1]) / L * s
        s -= L
    a, b, L = segs[-1]
    return b[0] + (b[0] - a[0]) / L * s, b[1] + (b[1] - a[1]) / L * s


def genereaza_traseu(punct: dict, strazi: list[dict], params: dict, seed: str) -> list[dict]:
    """Traseu simulat de 60 min: [{t ISO, lat, lon}], determinist pe `seed` (aceeași intrare = aceeași ieșire).
    `punct` = {lat, lon[, t]} (t = sfârșitul traseului). `params` = cfg["trace_generat"] (eventual suprascris):
    puncte, zgomot_m (sigma GPS), durata_oprire_min, acoperire (fracția păstrată), decalaj_m (oprirea față de punct).
    Mersul urmează cea mai apropiată stradă OSM înainte și după oprire; fără străzi, o linie dreaptă."""
    rng = random.Random(int.from_bytes(hashlib.sha256(str(seed).encode()).digest()[:8], "big"))
    n = max(2, int(params["puncte"]))
    dt = 3600 / (n - 1)  # secunde între puncte
    lat0, lon0 = punct["lat"], punct["lon"]
    k = math.cos(math.radians(lat0))

    # oprirea: decalaj în direcție aleatoare față de punct
    ang = rng.uniform(0, 2 * math.pi)
    dec = params.get("decalaj_m", 0)
    cx, cy = dec * math.cos(ang), dec * math.sin(ang)  # metri față de punct

    # cea mai apropiată stradă; mers = polilinie în metri față de punct
    best = min(((_dist_segment((lat0, lon0), w[i], w[i + 1]), w) for s in strazi
                for w in [[tuple(p) for p in s["puncte"]]] for i in range(len(w) - 1)), default=None, key=lambda x: x[0])
    if best:
        w = best[1]
        xy = [((p[1] - lon0) * M * k, (p[0] - lat0) * M) for p in w]
        # abscisa curbilinie a proiecției punctului (0,0) pe polilinie
        s0, acc, dmin = 0.0, 0.0, 1e18
        for a, b in zip(xy, xy[1:]):
            L = math.dist(a, b)
            if L == 0:
                continue
            t = max(0, min(1, -((a[0]) * (b[0] - a[0]) + a[1] * (b[1] - a[1])) / L ** 2))
            d = math.hypot(a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
            if d < dmin:
                dmin, s0 = d, acc + t * L
            acc += L
    else:
        xy, s0 = [(-100.0, 0.0), (100.0, 0.0)], 100.0

    m = round(params["durata_oprire_min"] * 60 / dt) + 1  # puncte în oprire
    i0 = max(0, min(n - m, round(n * 0.4)))  # oprirea începe la ~40% din oră
    pas = _VIT_M_S * dt  # ~85 m/punct >> raza de oprire: mersul nu face grup; la capete _pe_linie continuă drept
    # garanție: punctele din oprire la <= 0,4*rază de centru => la <= 0,8*rază de centroid (gaseste_opriri vede o singură oprire).
    # Doar când zgomotul sigma încape în rază; peste, oprirea poate fi pierdută intenționat (zgomot mare).
    raza = params.get("raza_oprire_m", 12)
    cap = 0.4 * raza if params["zgomot_m"] <= raza else 0
    base = datetime.fromisoformat(punct.get("t") or _BAZA) - timedelta(seconds=3600)
    out = []
    for i in range(n):
        if i < i0:
            x, y = _pe_linie(xy, s0 - pas * (i0 - i))
        elif i < i0 + m:
            x, y = cx, cy
        else:
            x, y = _pe_linie(xy, s0 + pas * (i - i0 - m + 1))
        gx, gy = rng.gauss(0, params["zgomot_m"]), rng.gauss(0, params["zgomot_m"])
        if i0 <= i < i0 + m and cap and math.hypot(gx, gy) > cap:  # în oprire zgomotul nu rupe grupul
            gx, gy = gx * cap / math.hypot(gx, gy), gy * cap / math.hypot(gx, gy)
        x += gx
        y += gy
        if rng.random() < params["acoperire"]:  # rng consumat mereu: ieșirea rămâne stabilă
            out.append({"t": (base + timedelta(seconds=round(i * dt))).isoformat(timespec="seconds"),
                        "lat": round(lat0 + y / M, 7), "lon": round(lon0 + x / (M * k), 7)})
    return out
