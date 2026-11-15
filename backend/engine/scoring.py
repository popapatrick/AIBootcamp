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


def _regim_scadere(regim: str | None, w: dict) -> tuple[float, float | None]:
    """(rata la 30 de zile, minim) după regimul elementului: gis | verificat_om | None (normal, fără minim propriu)."""
    if regim == "gis":
        a = w["acuratete"]
        return a["scadere_gis_per_30_zile"], a["minim_gis"]
    if regim == "verificat_om":
        v = w["verificat_om"]
        return v["scadere_per_30_zile"], v["minim"]
    return w["scor"]["scadere_per_30_zile"], None


def rata_scadere(regim: str | None, w: dict) -> float:
    """Rata de scădere la 30 de zile pentru regim (pentru mesajele „de ce")."""
    return _regim_scadere(regim, w)[0]


def scor_la_data(scor_baza: float, data_baza: str, data: str, w: dict, regim: str | None = None) -> float:
    """Scorul unui element la `data`, cu scăderea în timp de la ultima actualizare.

    `regim`: "gis" (rată și minim din `acuratete`), "verificat_om" (din `verificat_om`) sau None (rata normală
    `scor.scadere_per_30_zile`, fără minim). Scăderea nu împinge scorul sub minim, dar un scor deja sub minim
    (după o contradicție) nu e ridicat: eff = max(min(scor, minim), scor + rata * zile / 30)."""
    zile_trecute = max(0, zile(data_baza, data))
    rata, minim = _regim_scadere(regim, w)
    eff = scor_baza + rata * zile_trecute / 30
    if minim is not None:
        eff = max(min(scor_baza, minim), eff)
    return clamp(eff, w)


def regim_stare(st: dict) -> str | None:
    """Regimul de scădere al unei stări: verificat_om | gis | None (normal). Se deduce din câmpurile stării."""
    if st.get("verificat_om"):
        return "verificat_om"
    if st.get("origine") == "retea_start" and st.get("sursa_locatie") == "gis":
        return "gis"
    return None


def fmt(x: float) -> str:
    """Număr cu virgulă și 2 zecimale, pentru textele în română (0,70)."""
    return f"{x:.2f}".replace(".", ",")


DESCRIERE_SURSA = {
    "coordonate": "locația vine din coordonate",
    "id": "locația vine dintr-un ID dat în raport",
    "adresa_numar": "locația vine dintr-o adresă cu număr",
    "intersectie": "locația vine dintr-o intersecție de străzi",
    "strada": "locația vine doar din numele străzii",
    "analiza_harta": "locația e dedusă din analiza hărții (vecini, străzi)",
    "reper": "locația vine dintr-un reper",
}


def text_plafon(sursa: str | None, w: dict) -> str:
    """Fraza „de ce” pentru plafonare: „Acuratețe plafonată la 0,70: locația vine dintr-o adresă cu număr.”"""
    return f"Acuratețe plafonată la {fmt(plafon(sursa, w))}: {DESCRIERE_SURSA.get(sursa, 'sursa locației e limitată')}."


def banda(scor: float, w: dict) -> str:
    """Banda de culoare a scorului: verde | galben | portocaliu | rosu (praguri `culori` din weights.yaml)."""
    c = w["culori"]
    if scor >= c["verde"]:
        return "verde"
    if scor >= c["galben"]:
        return "galben"
    if scor >= c["portocaliu"]:
        return "portocaliu"
    return "rosu"


def plafon(sursa_locatie: str | None, w: dict) -> float:
    """Scorul maxim al unui element după sursa locației (`plafon_locatie`); "gis" sau None = fără plafon (1.0)."""
    if sursa_locatie in (None, "gis"):
        return 1.0
    return float(w["plafon_locatie"].get(sursa_locatie, 1.0))


# ordinea calității locației (mai mare = mai bună); id și coordonate sunt la egalitate
ORDINE_SURSA = {"coordonate": 5, "id": 5, "adresa_numar": 4, "intersectie": 3, "strada": 2, "analiza_harta": 1, "reper": 0}


def mai_buna(a: str | None, b: str | None) -> str | None:
    """Sursa de locație mai bună dintre a și b (None = nespecificat)."""
    if a is None or b is None:
        return a or b
    return a if ORDINE_SURSA.get(a, -1) >= ORDINE_SURSA.get(b, -1) else b


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


def decizie(scor: float, w: dict, planificat: bool = False, executat_teren: bool = False) -> str:
    """Nivelul unei propuneri: in_model (aplicat) | predictie | de_verificat.

    Ce e doar planificat nu se aplică niciodată, indiferent de scor (rămâne propunere).
    `executat_teren`: raport executat de mentenanță/investiții; pragul de aplicare devine
    `acuratete.aplicat_raport_executat` în loc de `praguri.aplicat`."""
    prag = w["acuratete"]["aplicat_raport_executat"] if executat_teren else w["praguri"]["aplicat"]
    if planificat:
        return "predictie" if scor >= w["praguri"]["predictie"] else "de_verificat"
    if scor >= prag:
        return "in_model"
    if scor >= w["praguri"]["predictie"]:
        return "predictie"
    return "de_verificat"
