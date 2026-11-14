"""Safeguard: zona prototipului (Sesiunea 3, feature `safeguard-zona-prototip`).

Nimic nu iese din cercul de `zona.raza_max_m` (3000 m) în jurul centroidului rețelei de start. Un punct din
afară e „eronat în cadrul prototipului": nu se aplică și nu intră în model. Funcții pure, fără rețea.
"""
from __future__ import annotations

from backend.engine.network import dist_m

RAZA_IMPLICITA_M = 3000.0


def centru_retea(net: dict) -> tuple[float, float]:
    """Centroidul nodurilor rețelei de start (calculat o dată și reținut în `net["_zona_centru"]`).

    Se cheamă la încărcarea modelului, înainte să fie adăugat ceva; nodurile adăugate ulterior nu mută centrul.
    """
    c = net.get("_zona_centru")
    if c is None:
        noduri = list(net["noduri"].values())
        c = (sum(n["lat"] for n in noduri) / len(noduri), sum(n["lon"] for n in noduri) / len(noduri))
        net["_zona_centru"] = c
    return c


def zona_ok(lat: float, lon: float, net: dict, cfg: dict) -> dict:
    """{ok, distanta_m, raza_m, centru:{lat,lon}} pentru un punct; `cfg` = weights.yaml încărcat."""
    raza = float((cfg.get("zona") or {}).get("raza_max_m", RAZA_IMPLICITA_M))
    c = centru_retea(net)
    d = dist_m(c, (float(lat), float(lon)))
    return {"ok": d <= raza, "distanta_m": round(d), "raza_m": raza, "centru": {"lat": c[0], "lon": c[1]}}


def motiv_afara(z: dict) -> str:
    """Textul pentru „De ce?": punct în afara zonei prototipului."""
    return (f"Punct la {z['distanta_m']} m de centrul rețelei, peste limita de {z['raza_m']:g} m: "
            f"eronat în cadrul prototipului, nu se aplică.")
