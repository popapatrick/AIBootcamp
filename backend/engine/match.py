"""Etapa 4: potrivirea unui eveniment pe un element al rețelei.

Ordine: ID (cod nod/tronson) -> coordonate (element apropiat) -> adresă.
Niciun eveniment nu rămâne fără rezultat: element, ambiguu, absent din model sau nepotrivit, cu motiv.

Rezultatul (dict):
  status      potrivit | ambiguu | absent_din_model | nepotrivit
  element_id  id-ul potrivit (sau None)
  metoda      id | coordonate | adresa | None
  calitate    0-1, intră în scor (weights.yaml, secțiunea potrivire)
  candidati   până la 3 elemente apropiate [{element_id, distanta_m}]
  coordonate_folosite  {lat, lon} după eventuala corecție, sau None
  semnale     etichete pentru scor: coordonate_corectate, coordonate_in_afara_zonei,
              cod_fara_prefix, inconsecventa_id_coordonate, doar_adresa
  motiv       text pentru „de ce"

`status = absent_din_model` NU e eroare: așa se descoperă elementele care lipsesc (nod lipsă, racord nou).
Date FICTIVE.
"""
from __future__ import annotations

import math
import re

from backend.engine.config import load_weights
from backend.engine.network import dist_m

TRONSON_CU_PREFIX = re.compile(r"^[ARS]-T-\d+$")
TRONSON_FARA_PREFIX = re.compile(r"^T-\d+$")


def _elemente(net: dict) -> dict[str, dict]:
    out = dict(net["noduri"])
    out.update(net["tronsoane"])
    if net.get("post"):
        out[net["post"]["id"]] = net["post"]
    return out


def _dist_la_punct(p: tuple[float, float], el: dict) -> float:
    """Distanța (m) de la punctul p=(lat, lon) la un element (punct sau linie)."""
    if "puncte" not in el:
        return dist_m(p, (el["lat"], el["lon"]))
    pts = el["puncte"]
    lat0 = math.radians(p[0])
    kx, ky = 111_320 * math.cos(lat0), 111_320

    def xy(q):
        return ((q[1] - p[1]) * kx, (q[0] - p[0]) * ky)

    best = float("inf")
    for a, b in zip(pts, pts[1:]):
        ax, ay = xy(a)
        bx, by = xy(b)
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L2))
        best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def _bbox(net: dict, margine_m: float = 500.0) -> tuple[float, float, float, float]:
    lats = [n["lat"] for n in net["noduri"].values()]
    lons = [n["lon"] for n in net["noduri"].values()]
    dlat = margine_m / 111_320
    dlon = margine_m / (111_320 * math.cos(math.radians(sum(lats) / len(lats))))
    return min(lats) - dlat, max(lats) + dlat, min(lons) - dlon, max(lons) + dlon


def _in_zona(lat: float, lon: float, bb) -> bool:
    return bb[0] <= lat <= bb[1] and bb[2] <= lon <= bb[3]


def _coordonate(ref: dict, net: dict, semnale: list[str]):
    """Întoarce (lat, lon) utilizabile sau None; corectează inversarea lat/lon."""
    c = ref.get("coordonate")
    if not c:
        return None
    lat, lon = float(c["lat"]), float(c["lon"])
    bb = _bbox(net)
    if _in_zona(lat, lon, bb):
        return (lat, lon)
    if _in_zona(lon, lat, bb):          # lat și lon inversate
        semnale.append("coordonate_corectate")
        return (lon, lat)
    # punct zecimal pierdut: 4427960 / 2606510 -> 44.27960 / 26.06510
    def _repara(v: float) -> float | None:
        t = str(int(abs(v)))
        return float(t[:2] + "." + t[2:]) if abs(v) >= 1000 and len(t) >= 4 else None
    a, b = _repara(lat), _repara(lon)
    if a is not None and b is not None:
        for la, lo in ((a, b), (b, a)):
            if _in_zona(la, lo, bb):
                semnale.append("coordonate_zecimale_reparate")
                return (la, lo)
    semnale.append("coordonate_in_afara_zonei")
    return None


def match_event(event: dict, net: dict, weights: dict | None = None) -> dict:
    """Potrivește `event` (contracts/event.schema.json) pe `net` (modelul curent)."""
    w = dict((weights or load_weights())["potrivire"])
    if event.get("echipa_sursa") == "apel_client":
        w["distanta_max_m"] = w.get("distanta_max_apel_m", w["distanta_max_m"])
    ref = event.get("referinta") or {}
    els = _elemente(net)
    semnale: list[str] = []
    pt = _coordonate(ref, net, semnale)
    cand = []
    if pt:
        cand = sorted(({"element_id": i, "distanta_m": round(_dist_la_punct(pt, e), 1)}
                       for i, e in els.items()), key=lambda x: x["distanta_m"])[:3]

    def rez(status, element_id, metoda, calitate, motiv):
        return {"status": status, "element_id": element_id, "metoda": metoda,
                "calitate": round(calitate, 3), "candidati": cand,
                "coordonate_folosite": {"lat": pt[0], "lon": pt[1]} if pt else None,
                "semnale": semnale, "motiv": motiv}

    eid = (ref.get("element_id") or "").strip()

    # 1. ID
    if eid:
        if eid in els:
            q = w["calitate_dupa_id"]
            if pt and _dist_la_punct(pt, els[eid]) > 3 * w["distanta_max_m"]:
                semnale.append("inconsecventa_id_coordonate")
                return rez("potrivit", eid, "id", q * 0.6,
                           f"ID {eid} există, dar coordonatele sunt la "
                           f"{_dist_la_punct(pt, els[eid]):.0f} m de el: semnal contradictoriu")
            return rez("potrivit", eid, "id", q, f"ID {eid} găsit în model")
        if TRONSON_FARA_PREFIX.match(eid):
            semnale.append("cod_fara_prefix")
            posibile = [f"{p}-{eid}" for p in "ARS" if f"{p}-{eid}" in els]
            if pt and posibile:
                posibile.sort(key=lambda i: _dist_la_punct(pt, els[i]))
                if _dist_la_punct(pt, els[posibile[0]]) <= w["distanta_max_m"]:
                    return rez("potrivit", posibile[0], "id", w["calitate_dupa_id"] * 0.8,
                               f"Cod {eid} fără prefix, ales {posibile[0]} după coordonate")
            if len(posibile) == 1:
                return rez("potrivit", posibile[0], "id", w["calitate_dupa_id"] * 0.6,
                           f"Cod {eid} fără prefix, un singur tronson posibil ({posibile[0]})")
            if len(posibile) > 1:
                return rez("ambiguu", None, "id", 0.3,
                           f"Cod {eid} fără prefix se potrivește cu {', '.join(posibile)}")
            return rez("absent_din_model", None, "id", 0.0,
                       f"Cod {eid} fără prefix, nu există în model în nicio categorie")
        if TRONSON_CU_PREFIX.match(eid) or re.fullmatch(r"\d{5,}", eid):
            return rez("absent_din_model", None, "id", 0.0,
                       f"ID {eid} are format valid, dar nu există în model")
        semnale.append("id_necunoscut")  # format neașteptat: încercăm coordonatele

    # 2. Coordonate
    if pt:
        d = cand[0]["distanta_m"]
        if d <= w["distanta_max_m"]:
            q = w["calitate_dupa_coordonate"] * (1 - 0.5 * d / w["distanta_max_m"])
            if "coordonate_corectate" in semnale:
                q *= 0.8
            if "coordonate_zecimale_reparate" in semnale:
                q *= w.get("factor_zecimale_reparate", 0.7)
            return rez("potrivit", cand[0]["element_id"], "coordonate", q,
                       f"Cel mai apropiat element: {cand[0]['element_id']} la {d} m")
        return rez("absent_din_model", None, "coordonate", 0.0,
                   f"Niciun element în raza de {w['distanta_max_m']} m "
                   f"(cel mai apropiat: {cand[0]['element_id']} la {d} m)")

    # 3. Doar adresă / nr. cadastral: geocodarea nu e implementată în prototip
    if ref.get("adresa") or ref.get("nr_cadastral"):
        semnale.append("doar_adresa")
        return rez("nepotrivit", None, "adresa", 0.0,
                   "Doar adresă / nr. cadastral, fără ID sau coordonate; geocodarea nu e implementată")
    if "coordonate_in_afara_zonei" in semnale:
        return rez("nepotrivit", None, "coordonate", 0.0,
                   "Coordonate în afara zonei rețelei (posibil zecimale lipsă sau greșite)")
    return rez("nepotrivit", None, None, 0.0, "Nicio referință utilizabilă în eveniment")
