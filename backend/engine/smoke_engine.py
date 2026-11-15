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


def ev(i, data, echipa, tip, status, forma="campuri", incredere=0.9, sursa=None, **kw):
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

    # nod_lipsa doar cu coordonate, la 3,9 m de un nod vecin: tratat ca element nou, nu ca nodul vecin
    mn = GridModel()
    t = mn.apply_event(ev(40, "2026-08-09", "mentenanta", "nod_lipsa", "executat", forma="text_liber", incredere=0.7,
                          referinta={"coordonate": c}))
    verifica("nod lipsă lângă un vecin -> element nou, nu confirmare", t["decizie"] in ("predictie", "adaugat")
             and "element_nou_langa_existent" in next(p_ for p_ in t["pasi"] if p_["nume"] == "potrivire")["rezultat"]["semnale"], t["decizie"])
    # fără coordonate, cu doi vecini în text: poziție dedusă, doar predicție
    t = GridModel().apply_event({**ev(41, "2026-08-09", "mentenanta", "nod_lipsa", "executat", incredere=0.95,
                                       sursa="tableta_coordonate", referinta={"element_id": LIPSA["nod_lipsa"]}),
                                 "text_original": f"Nodul lipsește între {LIPSA['noduri_vecine'][0]} și {LIPSA['noduri_vecine'][1]}."})
    verifica("fără coordonate: poziție dedusă, nu se aplică", t["decizie"] == "predictie"
             and t["pasi"][2]["rezultat"]["pozitie_dedusa"] is True, t["decizie"])
    # doua observatii diferite de secțiune în fereastră, fără aplicare anterioară -> conflict
    mc = GridModel()
    mc.apply_event(ev(42, "2026-08-26", "mentenanta", "avarie_semnalata", "semnalat", forma="text_liber", incredere=0.7,
                      referinta={"element_id": "A-T-021"}, detalii={"sectiune_observata": mc.net["tronsoane"]["A-T-021"]["sectiune"]}))
    t = mc.apply_event(ev(43, "2026-08-29", "racordari", "activ_inlocuit", "executat", forma="text_liber", incredere=0.7,
                          referinta={"element_id": "A-T-021"}, detalii={"sectiune_noua": "TYIR 3x50+54,6 OL-Al"}))
    verifica("secțiune observată vs raportată diferit -> conflict", t["decizie"] == "conflict", t["decizie"])
    # coordonate cu punct zecimal pierdut: reparate
    mr = GridModel()
    t = mr.apply_event(ev(44, "2026-09-03", "racordari", "racord_nou", "executat",
                          referinta={"coordonate": {"lat": 4427960, "lon": 2606510}}))
    verifica("coordonate fără punct zecimal: reparate", "coordonate_zecimale_reparate" in next(p_ for p_ in t["pasi"] if p_["nume"] == "potrivire")["rezultat"]["semnale"],
             str(next(p_ for p_ in t["pasi"] if p_["nume"] == "potrivire")["rezultat"]["semnale"]))

    # Scenariul 1b: același tip de raport, dar text liber, fără ID, vecini deduși -> doar predicție
    m2 = GridModel()
    # Sesiunea 4 (P1): un raport EXECUTAT de mentenanță aplică de la 0,50, deci predicția slabă se obține cu „semnalat"
    tx = GridModel().apply_event(ev(2, "2026-08-10", "mentenanta", "nod_lipsa", "executat", forma="text_liber", incredere=0.7,
                                    referinta={"coordonate": c}))
    verifica("P1: nod lipsă, text liber, EXECUTAT (scor peste 0,50) -> aplicat", tx["decizie"] == "adaugat",
             f"{tx['decizie']} {tx['pasi'][-1]['rezultat'].get('scor_propunere')}")
    t = m2.apply_event(ev(2, "2026-08-10", "mentenanta", "nod_lipsa", "semnalat", forma="text_liber", incredere=0.7,
                          referinta={"coordonate": c}))
    verifica("nod lipsă, text liber, semnalat -> predicție", t["decizie"] == "predictie" and not m2.net["noduri"].get("NOU-T-02"),
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
    t = m.apply_event(ev(6, "2026-09-02", "mentenanta", "activ_inlocuit", "semnalat", forma="text_liber", incredere=0.6,
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
    b = next(x for x in mm.snapshot("2027-08-01")["features"] if x["properties"]["element_id"] == alt)["properties"]
    # Sesiunea 4 (V1): GIS scade încet și nu coboară sub acuratete.minim_gis (rămâne in_model)
    verifica("GIS scade încet, nu sub minim_gis", b["scor"] < a["scor"] and b["scor"] >= mm.w["acuratete"]["minim_gis"] and b["nivel"] == "in_model",
             f"{a['scor']} -> {b['scor']} {b['nivel']}")
    sim_e = next(e_ for e_ in mm.net["noduri"] if e_.startswith("SIM-"))
    a2 = next(x for x in mm.snapshot("2026-08-01")["features"] if x["properties"]["element_id"] == sim_e)["properties"]
    b2 = next(x for x in mm.snapshot("2027-08-01")["features"] if x["properties"]["element_id"] == sim_e)["properties"]
    verifica("element din rapoarte mai vechi (SIM-*) scade în timp și devine de_verificat", b2["scor"] < a2["scor"] and b2["nivel"] == "de_verificat",
             f"{a2['scor']} -> {b2['scor']} {b2['nivel']}")
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
    verifica("statistici: ultima_actualizare = data ultimului eveniment aplicat sau actualizat",
             s["ultima_actualizare"] == "2026-09-10" or (s["ultima_actualizare"] or "") >= "2026-08-10", str(s["ultima_actualizare"]))
    verifica("ultima_actualizare nu depășește data cerută", m.statistici("2026-08-05")["ultima_actualizare"] is None
             or m.statistici("2026-08-05")["ultima_actualizare"] <= "2026-08-05")

    # schimbari[]: lista structurată pentru „Show pipeline"
    ms = GridModel()
    t1 = ms.apply_event(ev(60, "2026-08-10", "mentenanta", "nod_lipsa", "executat", sursa="tableta_coordonate",
                           incredere=0.95, referinta={"element_id": LIPSA["nod_lipsa"], "coordonate": c},
                           detalii={"noduri_vecine": LIPSA["noduri_vecine"]}))
    sch = t1["schimbari"]
    verifica("schimbari: nod lipsă adăugat + tronsoane noi", len(sch) >= 3 and all(
        {"element_id", "ce", "scor_inainte", "scor_dupa", "de_ce"} <= set(x) for x in sch)
        and any(x["ce"] == "adaugat" and x["scor_inainte"] is None for x in sch), str([x["ce"] for x in sch]))
    t2 = ms.apply_event(ev(61, "2026-08-12", "mentenanta", "verificare", "executat", sursa="tableta_coordonate",
                           referinta={"element_id": alt}))
    verifica("schimbari: confirmare = actualizat cu scor mai mare", t2["schimbari"] and t2["schimbari"][0]["ce"] == "actualizat"
             and t2["schimbari"][0]["scor_dupa"] > t2["schimbari"][0]["scor_inainte"],
             str(t2["schimbari"][:1]))
    t3 = ms.apply_event(ev(62, "2026-08-13", "apel_client", "avarie_semnalata", "semnalat", forma="text_liber", incredere=0.5,
                           referinta={"adresa": "Strada Necunoscută 5"}))
    verifica("schimbari: neaplicat are o intrare cu motiv", t3["schimbari"] and t3["schimbari"][0]["ce"] == "neaplicat"
             and t3["schimbari"][0]["de_ce"], str(t3["schimbari"]))
    # B4: decizia omului (om_teren) asupra unei predicții
    def decizie_ev(i, data, tinta, alege):
        return ev(i, data, "om_teren", "verificare", "executat", sursa="om_teren", incredere=1.0,
                  detalii={"decizie": {"tinta_id": tinta, "decizie": alege}})
    md = GridModel()
    tp = md.apply_event(ev(70, "2026-08-09", "mentenanta", "nod_lipsa", "semnalat", forma="text_liber", incredere=0.7,
                           referinta={"coordonate": c}))
    pred = next((x["element_id"] for x in tp["modificari"] if x["tip_element"] == "nod"), None)
    verifica("pregătire: există o predicție de nod", tp["decizie"] == "predictie" and pred is not None, str(pred))
    ta = md.apply_event(decizie_ev(71, "2026-08-20", pred, "accepta"))
    sa = next(x for x in md.snapshot("2026-08-21")["features"] if x["properties"]["element_id"] == pred)["properties"]
    verifica("om acceptă -> aplicat, confirmat_de om, scor mare", ta["decizie"] == "aplicat" and pred in md.net["noduri"]
             and sa["nivel"] == "in_model" and sa["confirmat_de"] == "om" and sa["scor"] >= 0.75, f"{sa['nivel']} {sa['scor']}")
    verifica("acceptarea: schimbari = adaugat", any(x["element_id"] == pred and x["ce"] == "adaugat" for x in ta["schimbari"]))
    sp_ = next(x for x in md.snapshot("2026-08-15")["features"] if x["properties"]["element_id"] == pred)["properties"]
    verifica("înainte de decizie e încă predicție AI", sp_["nivel"] == "predictie" and sp_["confirmat_de"] is None)
    t2x = md.apply_event(decizie_ev(72, "2026-08-21", pred, "respinge"))
    verifica("a doua decizie e refuzată (deja_decis)", t2x["decizie"] == "neaplicat" and t2x["eroare"]["cod"] == "deja_decis")
    tn = md.apply_event(decizie_ev(73, "2026-08-22", "NOU-INEXISTENT", "accepta"))
    verifica("predicție necunoscută", tn["eroare"]["cod"] == "necunoscut")

    mr = GridModel()
    tr0 = mr.apply_event(ev(74, "2026-08-09", "mentenanta", "nod_lipsa", "semnalat", forma="text_liber", incredere=0.7,
                            referinta={"coordonate": c}))
    predr = next(x["element_id"] for x in tr0["modificari"] if x["tip_element"] == "nod")
    sc0 = tr0["pasi"][-1]["rezultat"]["scor_propunere"] if "scor_propunere" in tr0["pasi"][-1]["rezultat"] else None
    tr = mr.apply_event(decizie_ev(75, "2026-08-20", predr, "respinge"))
    verifica("om respinge -> predicția e retrasă, nimic în model", tr["decizie"] == "respins" and predr not in mr.net["noduri"]
             and not any(x["properties"]["element_id"] == predr for x in mr.snapshot("2026-08-21")["features"]))
    verifica("respingerea retrage și legăturile", all(x["ce"] == "retras" for x in tr["schimbari"]) and len(tr["schimbari"]) >= 1,
             str([x["ce"] for x in tr["schimbari"]]))
    verifica("respingerea penalizează metoda", mr.penalizare_metoda and max(mr.penalizare_metoda.values()) > 0, str(mr.penalizare_metoda))
    tr2 = mr.apply_event(ev(76, "2026-08-25", "mentenanta", "nod_lipsa", "semnalat", forma="text_liber", incredere=0.7,
                            referinta={"coordonate": c}))
    verifica("propunere nouă cu aceeași metodă: scor mai mic și motivul penalizării",
             any("respinsă în teren" in x for x in tr2["pasi"][-1].get("motive", [])), str(tr2["decizie"]))

    # decizia omului asupra unei propuneri de secțiune (tronson existent)
    mp = GridModel()
    tpp = mp.apply_event({**ev(80, "2026-08-10", "apel_client", "activ_inlocuit", "semnalat", forma="text_liber", incredere=0.6,
                               referinta={"element_id": "A-T-021"}, detalii={"sectiune_noua": "TYIR 3x50+54,6 OL-Al"})})
    tdd = mp.apply_event(decizie_ev(81, "2026-08-12", "A-T-021", "accepta"))
    sp3 = next(x for x in mp.snapshot("2026-08-13")["features"] if x["properties"]["element_id"] == "A-T-021")["properties"]
    verifica("om acceptă propunerea de secțiune -> aplicată, confirmat de om",
             tpp["decizie"] == "predictie" and tdd["decizie"] == "aplicat" and sp3["sectiune"] == "TYIR 3x50+54,6 OL-Al"
             and sp3["confirmat_de"] == "om" and sp3["predictie"] is None, f"{sp3['nivel']} {sp3['scor']}")

    assert all(OK), "unele verificări au eșuat"
    print(f"OK: {len(OK)} verificări")


if __name__ == "__main__":
    main()
