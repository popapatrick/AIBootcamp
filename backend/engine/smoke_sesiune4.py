"""Verificări pentru modelul de acuratețe din sesiunea 4 (V1 + V2): GIS stabil, SIM-* din rapoarte mai vechi,
plafon după sursa locației, prag 0,50 la rapoarte executate, benzi de culoare.
Rulează: EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune4. Date FICTIVE."""
from __future__ import annotations

from backend.engine import osm
from backend.engine import scoring as S
from backend.engine.config import load_weights
from backend.engine.model import GridModel

OK: list[bool] = []


def verifica(nume, cond, detaliu=""):
    OK.append(bool(cond))
    print(("OK  " if cond else "FAIL"), nume, detaliu)


def mk() -> GridModel:
    m = GridModel()
    m.traseu_fn = osm.traseu_fn()
    return m


def ev(i, data, echipa, tip, status="executat", ref=None, det=None, sursa="tableta_coordonate", inc=0.9, forma="campuri"):
    e = {"event_id": i, "echipa_sursa": echipa, "tip": tip, "status": status, "data": data, "forma_sursa": forma,
         "incredere_extractie": inc, "text_original": "test", "referinta": ref or {}, "detalii": det or {}}
    if sursa:
        e["tip_sursa_pondere"] = sursa
    return e


def snap(m, data, eid):
    return next((f["properties"] for f in m.snapshot(data)["features"] if f["properties"]["element_id"] == eid), None)


def benzi(m, data, filtru):
    """{banda: număr} pentru elementele din snapshot la `data` care trec de `filtru(element_id)`."""
    out = {"verde": 0, "galben": 0, "portocaliu": 0, "rosu": 0}
    for f in m.snapshot(data)["features"]:
        if filtru(f["properties"]["element_id"]):
            out[f["properties"]["banda"]] += 1
    return out


def geo_strada_numar(lat, lon, w):
    """Rezultat de geocodare „stradă + număr” (cum îl produce backend.geo), pentru un raport de test."""
    return {"lat": lat, "lon": lon, "precizie_m": 200, "metoda": "osm_cache", "acuratete": w["geocodare"]["acuratete"]["strada_numar"],
            "motiv": "Strada Viilor nr. 12, interpolat pe stradă (potrivire exactă a numelui)"}


def main() -> None:
    w = load_weights()
    m = mk()
    sim = lambda e: e.startswith("SIM-")      # noqa: E731
    gis = lambda e: not e.startswith("SIM-") and e in m.net["noduri"] or (e in m.net["tronsoane"] and not e.startswith("SIM-"))  # noqa: E731

    # --- (f) banda()
    verifica("banda: 0,85 verde, 0,65 galben, 0,45 portocaliu, 0,2 roșu, praguri incluse",
             [S.banda(x, w) for x in (0.85, 0.65, 0.45, 0.2, 0.8, 0.6, 0.4)] == ["verde", "galben", "portocaliu", "rosu", "verde", "galben", "portocaliu"])
    verifica("plafon(): gis/None = 1,0; adresa_numar 0,70; analiza_harta 0,40",
             S.plafon("gis", w) == 1.0 and S.plafon(None, w) == 1.0 and S.plafon("adresa_numar", w) == 0.70 and S.plafon("analiza_harta", w) == 0.40)
    verifica("scor_la_data: minim GIS nu e ridicat dacă scorul e deja sub el",
             S.scor_la_data(0.60, "2026-08-01", "2027-08-01", w, "gis") == 0.60
             and S.scor_la_data(0.95, "2026-08-01", "2030-08-01", w, "gis") == w["acuratete"]["minim_gis"]
             and S.scor_la_data(0.9, "2026-08-01", "2026-08-31", w) == 0.85)
    verifica("decizie: executat_teren coboară pragul la 0,50", S.decizie(0.55, w) == "predictie" and S.decizie(0.55, w, executat_teren=True) == "in_model"
             and S.decizie(0.55, w, planificat=True, executat_teren=True) == "predictie")

    # --- (a) element KMZ neatins
    kmz = next(e for e in m.net["tronsoane"] if not sim(e))
    a1, a2, a3 = (snap(m, d, kmz) for d in ("2026-08-01", "2026-11-15", "2027-08-01"))
    verifica("KMZ neatins: 0,95 la start, origine retea_start, t0, sursa gis",
             a1["scor"] == 0.95 and a1["origine"] == "retea_start" and a1["t0"] is True and a1["sursa_locatie"] == "gis" and a1["verificat_om"] is False,
             f"{a1['scor']}")
    verifica("KMZ neatins: la 2026-11-15 scor >= 0,91 (0,95 - 0,01*106/30 = 0,915) și verde; la 2027-08-01 nu sub 0,85",
             a2["scor"] >= 0.91 and a2["banda"] == "verde" and a3["scor"] >= 0.85, f"{a2['scor']} {a3['scor']}")
    verifica("mesajul de scădere spune rata GIS (0,01)", "0.01" in a2["motive"][0]["text"] and "GIS" in a2["motive"][0]["text"], a2["motive"][0]["text"])

    # --- (b) benzi la 2026-08-01 și 2026-11-15
    nodes_tr = list(m.net["noduri"]) + list(m.net["tronsoane"])
    n_gis = [e for e in nodes_tr if not sim(e)]
    for d in ("2026-08-01", "2026-11-15"):
        bg, bs = benzi(m, d, lambda e: e in n_gis), benzi(m, d, sim)
        print("    benzi", d, "GIS", bg, "SIM", bs)
    bg, bs = benzi(m, "2026-08-01", lambda e: e in n_gis), benzi(m, "2026-08-01", sim)
    verifica("2026-08-01: toate KMZ sunt verzi, niciun SIM-* nu e verde, SIM-* au toate cele trei benzi",
             bg["verde"] == len(n_gis) and bs["verde"] == 0 and bs["galben"] > 0 and bs["portocaliu"] > 0 and bs["rosu"] > 0, f"{bg} {bs}")
    verifica("SIM-*: origine generat_model, t0, motiv „din rapoarte mai vechi”",
             all(snap(m, "2026-08-01", e)["origine"] == "generat_model" and snap(m, "2026-08-01", e)["t0"]
                 and "rapoarte mai vechi" in snap(m, "2026-08-01", e)["motive"][-1]["text"] for e in list(m.net["noduri"])[-5:] if sim(e)))

    # --- (c) determinist
    m2 = mk()
    verifica("același model construit de două ori: aceleași scoruri SIM-*",
             {e: m.istoric[e][0]["scor"] for e in m.istoric if sim(e)} == {e: m2.istoric[e][0]["scor"] for e in m2.istoric if sim(e)}
             and any(sim(e) for e in m.istoric))

    # --- (d) raport executat, nod lipsă localizat doar din adresă (stradă + număr)
    c0 = m.net["_zona_centru"]
    lat, lon = c0[0] + 300 / 111_320, c0[1]
    ref = {"coordonate": {"lat": lat, "lon": lon}, "adresa": "Strada Viilor nr. 12"}
    det = {"geocodare": geo_strada_numar(lat, lon, w)}
    md = mk()
    t = md.apply_event(ev("S4-1", "2026-09-10", "mentenanta", "nod_lipsa", "executat", ref=ref, det=det, inc=0.95))
    nod = next(x for x in t["modificari"] if x["tip_element"] == "nod")
    pr = snap(md, "2026-09-10", nod["element_id"])
    verifica("executat de mentenanță, doar adresă cu număr: aplicat (in_model), scor <= 0,70, galben/portocaliu, sursa adresa_numar",
             nod["nivel"] == "in_model" and t["decizie"] == "adaugat" and nod["scor"] <= 0.70 and nod["banda"] in ("galben", "portocaliu")
             and nod["sursa_locatie"] == "adresa_numar" and pr["sursa_locatie"] == "adresa_numar" and pr["origine"] == "generat_model" and pr["t0"] is False,
             f"{t['decizie']} {nod['nivel']} {nod['scor']} {nod['banda']} {nod.get('sursa_locatie')}")
    print("    motiv:", nod["motive"][0]["text"][:300])
    sch = next(s for s in t["schimbari"] if s["element_id"] == nod["element_id"])
    verifica("jurnal: schimbari cu banda_inainte/banda_dupa", sch["banda_inainte"] is None and sch["banda_dupa"] == nod["banda"], str(sch))
    # aceeași situație ca cerere: planificat și racordare -> predicție
    tp = mk().apply_event(ev("S4-2", "2026-09-10", "mentenanta", "nod_lipsa", "planificat", ref=ref, det=det, inc=0.95))
    verifica("aceeași situație, status planificat -> predicție (neaplicat)", tp["decizie"] == "predictie", tp["decizie"])
    tr = mk().apply_event(ev("S4-3", "2026-09-10", "racordari", "cerere_racordare", "semnalat", ref=ref, det=det, inc=0.95))
    verifica("aceeași situație ca cerere de racordare -> predicție", tr["decizie"] == "predictie", tr["decizie"])
    casa = next((x for x in tr["modificari"] if x["element_id"].endswith("-casa")), None)
    verifica("racordare: casa localizată din adresă cu număr are sursa adresa_numar și scor <= 0,70; stâlpii analiza_harta <= 0,40",
             casa and casa["sursa_locatie"] == "adresa_numar" and casa["scor"] <= 0.70
             and all(x["sursa_locatie"] == "analiza_harta" and x["scor"] <= 0.40 for x in tr["modificari"] if x["tip_element"] == "nod" and not x["element_id"].endswith("-casa")),
             str([(x["element_id"], x["scor"], x["sursa_locatie"]) for x in tr["modificari"] if x["tip_element"] == "nod"]))
    verifica("racordare: există cel puțin un stâlp prezis", any(x["tip_element"] == "nod" and not x["element_id"].endswith("-casa") for x in tr["modificari"]))

    # --- (e) raport ulterior cu coordonate exacte ridică plafonul
    t2 = md.apply_event(ev("S4-4", "2026-09-20", "mentenanta", "verificare", "executat", ref={"coordonate": {"lat": lat, "lon": lon}}))
    p2 = snap(md, "2026-09-20", nod["element_id"])
    print("    după coordonate exacte:", t2["decizie"], p2 and (p2["scor"], p2["sursa_locatie"], p2["banda"]))
    verifica("confirmare cu coordonate exacte: sursa devine coordonate, scorul poate trece de 0,70 dar nu de 0,85",
             p2 and p2["sursa_locatie"] == "coordonate" and 0.70 < p2["scor"] <= 0.85, str(p2 and (p2["scor"], p2["sursa_locatie"])))
    # confirmare tot din adresă: rămâne sub plafon
    md2 = mk()
    md2.apply_event(ev("S4-5", "2026-09-10", "mentenanta", "nod_lipsa", "executat", ref=ref, det=det, inc=0.95))
    nid = next(e for e in md2.istoric if e.startswith("NOU-S4-5") and e in md2.net["noduri"])
    md2.apply_event(ev("S4-6", "2026-09-12", "mentenanta", "verificare", "executat", ref={"element_id": nid}))   # ID: sursă mai bună
    verifica("confirmare cu ID: sursa devine id (plafon 0,85)", snap(md2, "2026-09-12", nid)["sursa_locatie"] == "id", str(snap(md2, "2026-09-12", nid)["sursa_locatie"]))

    # --- GIS: confirmarea nu e plafonată; mesaj de ce la plafon
    mg = mk()
    mg.apply_event(ev("S4-7", "2026-09-01", "mentenanta", "verificare", "executat", ref={"element_id": kmz}))
    sg = snap(mg, "2026-09-01", kmz)
    verifica("GIS confirmat: rămâne verde, sursa gis, fără plafon", sg["banda"] == "verde" and sg["sursa_locatie"] == "gis" and sg["scor"] >= 0.95, str(sg["scor"]))

    # --- P1: raport executat de investiții/racordari vs semnalat
    pe = mk().apply_event(ev("S4-8", "2026-09-10", "investitii", "nod_lipsa", "executat", ref={"coordonate": {"lat": lat, "lon": lon}}, inc=0.7, sursa="formular"))
    ps = mk().apply_event(ev("S4-9", "2026-09-10", "investitii", "nod_lipsa", "semnalat", ref={"coordonate": {"lat": lat, "lon": lon}}, inc=0.7, sursa="formular"))
    verifica("P1: același scor, executat aplică (>= 0,50), semnalat rămâne predicție (< 0,75)",
             pe["decizie"] == "adaugat" and ps["decizie"] == "predictie", f"{pe['decizie']} / {ps['decizie']}")

    # --- (g) statistici
    st = m.statistici("2026-11-15")
    verifica("statistici(): procent_banda cu cele patru benzi, suma ~100",
             set(st["procent_banda"]) == {"verde", "galben", "portocaliu", "rosu"} and abs(sum(st["procent_banda"].values()) - 100) < 0.5, str(st["procent_banda"]))
    verifica("snapshot: t0, sursa_locatie, verificat_om, verificat_om_data, banda în properties",
             all(k in snap(m, "2026-08-01", kmz) for k in ("t0", "sursa_locatie", "verificat_om", "verificat_om_data", "banda")))

    # --- sim_din_rapoarte = 0: SIM-* tratate ca GIS
    w0 = load_weights()
    w0["retea_start"]["sim_din_rapoarte"] = 0
    m0 = GridModel(weights=w0)
    e0 = next(e for e in m0.istoric if sim(e))
    verifica("retea_start.sim_din_rapoarte = 0: SIM-* sunt GIS (retea_start, 0,95)",
             m0.istoric[e0][0]["origine"] == "retea_start" and m0.istoric[e0][0]["scor"] == 0.95)

    ok, tot = sum(OK), len(OK)
    print(f"\nsmoke_sesiune4: {ok}/{tot} OK")
    if ok != tot:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
