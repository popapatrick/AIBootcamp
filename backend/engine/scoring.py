"""Etapa 5: regulile de scor și decizie. Funcții pure, toate parametrii vin din contracts/weights.yaml.

Aceleași reguli pentru TOATE inputurile (rapoarte, apeluri) și pentru predicții:
- efect asupra unui element existent = (confirmare_teren | contradictie) × fiabilitate_sursa × calitate_potrivire
- scor de propunere = medie ponderată (fiabilitate, încredere extracție, calitate potrivire, [urmează strada])
- decizie după praguri: aplicat / predicție / de_verificat
Date FICTIVE.
"""
from __future__ import annotations

from datetime import date

ECHIPE_TEREN = {"mentenanta", "investitii", "racordari"}


def zile(d1: str, d2: str) -> int:
    return (date.fromisoformat(d2) - date.fromisoformat(d1)).days


def fiabilitate(event: dict, w: dict) -> float:
    """Fiabilitatea sursei din tabelul de ponderi. Cheia vine din event, altfel se deduce."""
    cheie = event.get("tip_sursa_pondere")
    if not cheie:
        if event.get("echipa_sursa") == "apel_client":
            cheie = "apel_client"
        else:
            cheie = "formular" if event.get("forma_sursa") == "campuri" else "text_liber"
    return w["fiabilitate_sursa"][cheie]


def clamp(x: float, w: dict) -> float:
    return max(w["scor"]["minim"], min(w["scor"]["maxim"], x))


def scor_la_data(scor_baza: float, data_baza: str, data: str, w: dict) -> float:
    """Scorul unui element la `data`, cu scăderea în timp de la ultima actualizare."""
    zile_trecute = max(0, zile(data_baza, data))
    return clamp(scor_baza + w["scor"]["scadere_per_30_zile"] * zile_trecute / 30, w)


def efect_input(event: dict, calitate_potrivire: float, w: dict) -> tuple[float, str]:
    """Efectul unui input asupra elementului potrivit: (delta, tip_efect).

    Raport executat al unei echipe din teren = confirmare. Apel de client = semnal negativ slab
    (nu înseamnă că rețeaua nu există, dar scade încrederea). Planificat = niciun efect."""
    f = fiabilitate(event, w)
    if event.get("echipa_sursa") == "apel_client":
        return w["scor"]["contradictie"] * f * calitate_potrivire, "semnal_negativ"
    if event.get("echipa_sursa") in ECHIPE_TEREN:
        if event.get("status") == "executat":
            return w["scor"]["confirmare_teren"] * f * calitate_potrivire, "confirmare"
        if event.get("status") == "semnalat":
            return w["scor"]["confirmare_teren"] * w["scor"]["factor_semnalat_teren"] * f * calitate_potrivire, "confirmare"
    return 0.0, "fara_efect"


def scor_propunere(event: dict, calitate: float, w: dict, urmeaza_strada: float | None = None) -> tuple[float, dict]:
    """Scorul unei propuneri și factorii folosiți (pentru „de ce")."""
    p = w["propunere"]
    factori = {
        "fiabilitate_sursa": (fiabilitate(event, w), p["pondere_fiabilitate_sursa"]),
        "incredere_extractie": (float(event.get("incredere_extractie", 0.8)), p["pondere_incredere_extractie"]),
        "calitate_potrivire": (calitate, p["pondere_calitate_potrivire"]),
    }
    if urmeaza_strada is not None:
        factori["urmeaza_strada"] = (urmeaza_strada, p["pondere_urmeaza_strada"])
    total = sum(pond for _, pond in factori.values())
    scor = sum(v * pond for v, pond in factori.values()) / total
    return round(clamp(scor, w), 3), {k: round(v, 3) for k, (v, _) in factori.items()}


def decizie(scor: float, w: dict, planificat: bool = False) -> str:
    """Nivelul unei propuneri: in_model (aplicat) | predictie | de_verificat.

    Ce e doar planificat nu se aplică niciodată, indiferent de scor (rămâne propunere)."""
    if planificat:
        return "predictie" if scor >= w["praguri"]["predictie"] else "de_verificat"
    if scor >= w["praguri"]["aplicat"]:
        return "in_model"
    if scor >= w["praguri"]["predictie"]:
        return "predictie"
    return "de_verificat"
