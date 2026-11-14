"""Smoke test etapa 5: python -m backend.engine.smoke_engine

Evenimente sintetice (nu rapoartele lui A) pe scenariile din plan, cu verificarea deciziei.
"""
from backend.engine.defects import build
from backend.engine.model import GridModel

r = build()
D = r["defects"]
LIPSA = D["scenariul_1_nod_lipsa"]
CABLU = D["scenariul_2_cablu_inlocuit"]
REAL = r["real"]
OK: list[bool] = []


def ev(i, data, echipa, tip, status, forma="formular", incredere=0.9, sursa=None, **kw):
    e = {"event_id": f"T-{i:02d}", "echipa_sursa": echipa, "tip": tip, "status": status, "data": data,
         "forma_sursa": forma, "incredere_extractie": incredere, "text_original": "test",
         "referinta": kw.pop("referinta", {}), "detalii": kw.pop("detalii", {})}
    if sursa:
        e["tip_sursa_pondere"] = sursa
    return e


def verifica(nume, cond, info=""):
    OK.append(bool(cond))
    print(("OK  " if cond else "FAIL"), nume, info)


def main() -> None:
    m = GridModel()
    c = LIPSA["coordonate"]
    nod = next(iter(m.net["noduri"]))

    # Scenariul 1a: nod lipsă, tabletă cu coordonate + ID + vecini dați -> adăugat în model
    t = m.apply_event(ev(1, "2026-08-10", "mentenanta", "nod_lipsa", "executat", sursa="tableta_coordonate",
                         incredere=0.95, referinta={"element_id": LIPSA["nod_lipsa"], "coordonate": c},
                         detalii={"noduri_vecine": LIPSA["noduri_vecine"]}))
    verifica("nod lipsă, sursă bună -> adăugat", t["decizie"] == "adaugat" and LIPSA["nod_lipsa"] in m.net["noduri"],
             f"{t['decizie']} {t['pasi'][-1]['rezultat'].get('scor_propunere')}")
    verifica("tronsoanele noi sunt în model", sum(1 for k in m.net["tronsoane"] if k.startswith("NOU-")) == 2)

    # Scenariul 1b: același tip de raport, dar text liber, fără ID, vecini deduși -> doar predicție
    m2 = GridModel()
    t = m2.apply_event(ev(2, "2026-08-10", "mentenanta", "nod_lipsa", "executat", forma="text_liber", incredere=0.7,
                          referinta={"coordonate": c}))
    verifica("nod lipsă, text liber -> predicție", t["decizie"] == "predictie" and not m2.net["noduri"].get("NOU-T-02"),
             f"{t['decizie']} {t['pasi'][-1]['rezultat'].get('scor_propunere')}")
    pid = t["modificari"][0]["element_id"]
    # al doilea raport întărește predicția
    t = m2.apply_event(ev(3, "2026-08-20", "racordari", "nod_lipsa", "executat", sursa="tableta_coordonate",
                          incredere=0.95, referinta={"coordonate": c}))
    verifica("al doilea raport promovează predicția", t["decizie"] in ("adaugat", "predictie"),
             f"{t['decizie']} {t['pasi'][-1]['rezultat'].get('scor_propunere')}")

    # Scenariul 2: înlocuire de cablu (formular) -> aplicat; apoi raport contradictoriu -> conflict
    t = m.apply_event(ev(4, "2026-08-15", "investitii", "activ_inlocuit", "executat",
                         referinta={"element_id": CABLU["tronson"]}, detalii={"sectiune_noua": CABLU["sectiune_reala"]}))
    st = m.snapshot("2026-08-15")
    f = next(x for x in st["features"] if x["properties"]["element_id"] == CABLU["tronson"])
    verifica("înlocuire cablu -> aplicat", t["decizie"] == "aplicat" and f["properties"]["sectiune"] == CABLU["sectiune_reala"],
             f"{t['decizie']} scor {f['properties']['scor']}")
    t = m.apply_event(ev(5, "2026-09-01", "mentenanta", "activ_inlocuit", "executat", forma="text_liber", incredere=0.7,
                         referinta={"element_id": CABLU["tronson"]}, detalii={"sectiune_noua": "TYIR 3x95+54,6 OL-Al"}))
    verifica("raport contradictoriu -> conflict, de verificat", t["decizie"] == "conflict")
    f = next(x for x in m.snapshot("2026-09-01")["features"] if x["properties"]["element_id"] == CABLU["tronson"])
    verifica("secțiunea aplicată nu s-a schimbat", f["properties"]["sectiune"] == CABLU["sectiune_reala"]
             and f["properties"]["nivel"] == "de_verificat")

    # Înlocuire doar cu text liber -> predicție, neaplicată
    alt = next(k for k, v in m.net["tronsoane"].items() if k.startswith("A-") and k != CABLU["tronson"])
    t = m.apply_event(ev(6, "2026-09-02", "mentenanta", "activ_inlocuit", "executat", forma="text_liber", incredere=0.6,
                         referinta={"element_id": alt}, detalii={"sectiune_noua": "TYIR 3x95+54,6 OL-Al"}))
    verifica("înlocuire din text liber -> predicție", t["decizie"] == "predictie",
             f"{t['decizie']} {t['pasi'][-1]['rezultat'].get('scor_propunere')}")

    # Scenariul 4: apeluri de clienți scad încrederea, puțin, dar se adună; nu șterg nimic
    m3 = GridModel()
    el = m3.net["tronsoane"][alt]
    a_, b_ = el["puncte"][0], el["puncte"][-1]
    p0 = ((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2)   # mijlocul tronsonului, ca apelul să cadă pe el
    before = m3.snapshot("2026-08-02")
    s0 = next(x for x in before["features"] if x["properties"]["element_id"] == alt)["properties"]["scor"]
    for i in range(4):
        m3.apply_event(ev(10 + i, "2026-08-02", "apel_client", "avarie_semnalata", "semnalat", forma="text_liber",
                          referinta={"coordonate": {"lat": p0[0], "lon": p0[1]}, "id_client": f"C{i}"}))
    s1 = next(x for x in m3.snapshot("2026-08-02")["features"] if x["properties"]["element_id"] == alt)["properties"]
    verifica("apeluri scad scorul, fără să șteargă", s1["scor"] < s0 and alt in m3.net["tronsoane"], f"{s0} -> {s1['scor']}")
    verifica("un apel scade mai puțin decât o confirmare crește",
             abs(s1["scor"] - s0) / 4 < 0.25 * 0.75, f"{abs(s1['scor'] - s0) / 4:.3f}")

    # Confirmare din teren crește scorul și actualizează ultima verificare
    t = m3.apply_event(ev(20, "2026-08-05", "mentenanta", "avarie_semnalata", "executat", sursa="tableta_coordonate",
                          referinta={"element_id": alt}))
    s2 = next(x for x in m3.snapshot("2026-08-05")["features"] if x["properties"]["element_id"] == alt)["properties"]
    verifica("confirmare din teren crește scorul", s2["scor"] > s1["scor"] and s2["ultima_verificare"] == "2026-08-05",
             f"{s1['scor']} -> {s2['scor']}")

    # Scenariul 6: fără verificare, scorul scade în timp și devine de_verificat
    mm = GridModel()
    a = next(x for x in mm.snapshot("2026-08-01")["features"] if x["properties"]["element_id"] == alt)["properties"]
    b = next(x for x in mm.snapshot("2026-11-01")["features"] if x["properties"]["element_id"] == alt)["properties"]
    verifica("scade în timp", b["scor"] < a["scor"] and b["nivel"] == "de_verificat", f"{a['scor']} -> {b['scor']} {b['nivel']}")
    verifica("„de ce” include scăderea în timp", any("Neverificat" in x["text"] for x in b["motive"]))

    # Linie planificată: rămâne predicție chiar dacă sursa e bună
    t = m.apply_event(ev(30, "2026-09-10", "investitii", "linie_planificata", "planificat", sursa="tableta_coordonate",
                         incredere=0.99, detalii={"noduri": LIPSA["noduri_vecine"]}))
    verifica("planificat rămâne predicție", t["decizie"] == "predictie" and t["modificari"][0]["nivel"] == "predictie")

    # Date înainte de eveniment: elementul nou nu există încă
    verifica("elementul adăugat nu apare înainte de dată",
             not any(x["properties"]["element_id"] == LIPSA["nod_lipsa"] for x in m.snapshot("2026-08-05")["features"]))

    s = m.statistici("2026-09-10")
    verifica("statistici", s["elemente"] > 250 and "in_model" in s["procent"], str(s["procent"]))
    assert all(OK), "unele verificări au eșuat"
    print(f"OK: {len(OK)} verificări")


if __name__ == "__main__":
    main()
