"""Evenimente de rezervă (B), ca motorul, API-ul și UI-ul să aibă ce arăta cât timp A nu a împins `data/events/`.

Sunt sintetice, aliniate la scenariile din plan, cu ID-uri reale din `data/model/defects.json`.
Motorul le folosește DOAR dacă lipsesc `data/events/events.json` și `events.stub.json` (ale lui A).

    python -m backend.engine.fallback_events      # scrie data/model/events.fallback.json
"""
from __future__ import annotations

import json
from pathlib import Path

from backend.engine.defects import build
from backend.engine.network import dist_m

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "model" / "events.fallback.json"


def _ev(i, data, echipa, tip, status, text, forma="campuri", incredere=0.9, sursa=None, ref=None, det=None):
    e = {"event_id": f"FB-{i:02d}", "echipa_sursa": echipa, "tip": tip, "status": status, "data": data,
         "forma_sursa": forma, "incredere_extractie": incredere, "text_original": text,
         "referinta": ref or {}, "campuri_lipsa": [], "detalii": {**(det or {}), "sursa_date": "rezerva_B (sintetic)"}}
    if sursa:
        e["tip_sursa_pondere"] = sursa
    return e


def _mijloc(t):
    a, b = t["puncte"][0], t["puncte"][-1]
    return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2


def build_events() -> list[dict]:
    r = build()
    D = r["defects"]
    s1, s2 = D["scenariul_1_nod_lipsa"], D["scenariul_2_cablu_inlocuit"]
    net = r["model"]
    c1 = s1["coordonate"]
    aer = [t for t in net["tronsoane"].values() if t["id"].startswith("A-") and t["lungime_m"] > 25
           and t["id"] != s2["tronson"]]
    k = len(aer)
    apel_t = conf_t = aer[k // 5]                                # apeluri apoi confirmare pe același tronson
    text_t = aer[(3 * k) // 5]
    pa = _mijloc(apel_t)
    # racord nou: punct la ~25 m de un tronson, cu lat/lon inversate (greșeală de introducere)
    # punct liber (niciun element la < 20 m), ca racordul nou să nu cadă peste ceva existent
    from backend.engine.match import _dist_la_punct
    elem = list(net["noduri"].values()) + list(net["tronsoane"].values())
    rlat = rlon = None
    for t in aer[(4 * k) // 5:] + aer:
        la, lo = _mijloc(t)
        for dy, dx in ((30, 0), (-30, 0), (0, 30), (0, -30)):
            p = (la + dy / 111_320, lo + dx / 80_000)
            if all(_dist_la_punct(p, e) >= 20 for e in elem):
                rlat, rlon = p
                break
        if rlat is not None:
            break
    noduri = [n for n in net["noduri"].values() if n["id"] not in s1["noduri_vecine"]]
    n1 = noduri[5]
    n2 = min((n for n in noduri if n["id"] != n1["id"] and 40 <= dist_m((n1["lat"], n1["lon"]), (n["lat"], n["lon"])) <= 90),
             key=lambda n: dist_m((n1["lat"], n1["lon"]), (n["lat"], n["lon"])))
    out = [
        _ev(1, "2026-08-12", "mentenanta", "nod_lipsa", "executat", forma="text_liber", incredere=0.7,
            text=f"La colțul străzii lipsește un stâlp din GIS, la {c1['lat']:.5f}, {c1['lon']:.5f}.",
            ref={"coordonate": c1}),
        _ev(2, "2026-08-26", "racordari", "nod_lipsa", "executat", sursa="tableta_coordonate", incredere=0.95,
            text=f"Confirm stâlpul {s1['nod_lipsa']} la {c1['lat']:.5f}, {c1['lon']:.5f}, între {s1['noduri_vecine'][0]} și {s1['noduri_vecine'][1]}.",
            ref={"element_id": s1["nod_lipsa"], "coordonate": c1}, det={"noduri_vecine": s1["noduri_vecine"]}),
        _ev(3, "2026-09-03", "investitii", "activ_inlocuit", "executat",
            text=f"Înlocuit cablul pe {s2['tronson']} cu {s2['sectiune_reala']}.",
            ref={"element_id": s2["tronson"]}, det={"sectiune_noua": s2["sectiune_reala"]}),
        _ev(4, "2026-09-08", "racordari", "racord_nou", "executat", incredere=0.85,
            text=f"Racord nou client; coordonate trecute greșit: {rlon:.6f}, {rlat:.6f}.",
            ref={"coordonate": {"lat": rlon, "lon": rlat}}),
        _ev(5, "2026-09-12", "apel_client", "avarie_semnalata", "semnalat", forma="text_liber", incredere=0.8,
            text="Nu am curent, client C-1001.", ref={"coordonate": {"lat": pa[0], "lon": pa[1]}, "id_client": "C-1001"}),
        _ev(6, "2026-09-13", "apel_client", "avarie_semnalata", "semnalat", forma="text_liber", incredere=0.8,
            text="Nu am curent, client C-1002.", ref={"coordonate": {"lat": pa[0], "lon": pa[1]}, "id_client": "C-1002"}),
        _ev(7, "2026-09-14", "apel_client", "avarie_semnalata", "semnalat", forma="text_liber", incredere=0.8,
            text="Cablu căzut, client C-1003.", ref={"coordonate": {"lat": pa[0], "lon": pa[1]}, "id_client": "C-1003"}),
        _ev(8, "2026-09-20", "mentenanta", "activ_inlocuit", "executat", forma="text_liber", incredere=0.7,
            text=f"Pe {s2['tronson']} am montat TYIR 3x95+54,6 OL-Al.",
            ref={"element_id": s2["tronson"]}, det={"sectiune_noua": "TYIR 3x95+54,6 OL-Al"}),
        _ev(9, "2026-10-05", "mentenanta", "avarie_semnalata", "executat", sursa="tableta_coordonate",
            text=f"Verificat în teren {conf_t['id']}, avarie remediată.", ref={"element_id": conf_t["id"]}),
        _ev(10, "2026-10-10", "investitii", "linie_planificata", "planificat", sursa="tableta_coordonate", incredere=0.95,
            text=f"Linie nouă planificată între nodurile {n1['id']} și {n2['id']}.", ref={},
            det={"noduri": [n1["id"], n2["id"]]}),
        _ev(11, "2026-10-15", "mentenanta", "activ_inlocuit", "executat", forma="text_liber", incredere=0.6,
            text=f"Se pare că {text_t['id']} a fost schimbat cu un cablu mai gros.",
            ref={"element_id": text_t["id"]}, det={"sectiune_noua": "TYIR 3x70+54,6 OL-Al"}),
    ]
    return sorted(out, key=lambda e: (e["data"], e["event_id"]))


def main() -> None:
    ev = build_events()
    OUT.write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(ev)} evenimente de rezervă -> {OUT}")


if __name__ == "__main__":
    main()
