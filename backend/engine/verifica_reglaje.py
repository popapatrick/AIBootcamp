"""Verifică un reglaj în `contracts/weights.yaml` (Sesiunea 3, feature `reglaje-logica-fara-cod`).

    .venv/bin/python -m backend.engine.verifica_reglaje            # chei, limite, relații, diferență calibrare, smoke-uri
    .venv/bin/python -m backend.engine.verifica_reglaje --rapid    # fără smoke-uri
    .venv/bin/python -m backend.engine.verifica_reglaje --scrie-referinta   # (B) scrie data/golden/calibrare-referinta.json
    .venv/bin/python -m backend.engine.verifica_reglaje --strict-distributie   # distribuția culorilor în afara țintei = eșec

Reguli: aceleași chei ca în `contracts/weights.limits.yaml`, fiecare valoare numerică în [min, max], relațiile dintre
praguri respectate. Arată ce valori s-au schimbat față de `git HEAD`, ce evenimente de calibrare își schimbă decizia sau
scorul față de referință (`data/golden/calibrare-referinta.json`, sau față de HEAD dacă lipsește) și rulează smoke-urile.
Tipărește și distribuția culorilor (benzilor) doar pe rețea (predicțiile separat) la ultima dată a scenariului, față de `TINTA_DISTRIBUTIE` (informativ;
eșec doar cu `--strict-distributie`; sărită cu `--rapid`). Tipărește o linie gata de lipit în `board/<laptop>.md`. Cod de ieșire 0 = reglaj bun de împins (commit `reglaj:`).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WEIGHTS = ROOT / "contracts" / "weights.yaml"
LIMITS = ROOT / "contracts" / "weights.limits.yaml"
REF = ROOT / "data" / "golden" / "calibrare-referinta.json"
SMOKES = ["backend.engine.smoke_network", "backend.engine.smoke_match", "backend.engine.smoke_engine",
          "backend.engine.smoke_sesiune2", "backend.engine.smoke_sesiune4", "backend.engine.smoke_osm", "backend.geo.smoke_geo",
          "backend.trace.smoke_trace", "backend.racordare.smoke_racordare", "backend.api.smoke_api"]

# Ținta distribuției benzilor de culoare la ultima dată a scenariului (plan Sesiunea 4, 7.2), interval [min, max] în %.
# Se măsoară DOAR pe rețea (decizia lui Victor): elementele care fac parte din rețea la acea dată = ID prezent în
# `model._elemente()` (GIS, SIM-*, plus ce a fost adăugat/aplicat din rapoarte, căci `net` crește la aplicare), cu
# nivelul `in_model` sau `de_verificat`. NU intră: elementele `scos_din_uz` (demontate sau „demontat probabil”, ex. traseul
# vechi la o mutare de fire: nu mai sunt rețea, se afișează separat „scoase din uz: N”), predicțiile punctate (nivel `predictie`, `model.predictii`: element_nou,
# stâlpi prezisi, PLAN-*, MUT-*), pinurile VER-* (`model.pinuri`) și elementele retrase; sunt marcaje, nu rețea.
# Predicțiile se raportează separat, informativ.
TINTA_DISTRIBUTIE = {"verde": (70.0, 82.0), "galben": (8.0, 15.0), "portocaliu": (5.0, 10.0), "rosu": (2.0, 6.0)}


def aplatizeaza(d: dict, pre: str = "") -> dict:
    """{a: {b: 1}} -> {"a.b": 1} (doar frunze)."""
    out = {}
    for k, v in d.items():
        cheie = f"{pre}{k}"
        if isinstance(v, dict):
            out.update(aplatizeaza(v, cheie + "."))
        else:
            out[cheie] = v
    return out


def verifica_valori(w: dict, limite: dict) -> list[str]:
    """Erori: chei adăugate/șterse, tip schimbat, valori în afara limitelor, relații încălcate."""
    plat, err = aplatizeaza(w), []
    for k in sorted(set(plat) - set(limite)):
        err.append(f"cheie nouă fără limite: {k} (adaugă-o în weights.limits.yaml printr-o cerere de logică)")
    for k in sorted(set(limite) - set(plat)):
        err.append(f"cheie ștearsă din weights.yaml: {k}")
    for k, (lo, hi) in limite.items():
        if k not in plat:
            continue
        v = plat[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            err.append(f"{k}: valoarea trebuie să fie număr, e {v!r}")
        elif not (lo <= v <= hi):
            err.append(f"{k} = {v} în afara limitelor [{lo}, {hi}]")
    g = lambda k: plat.get(k)
    rel = [("praguri.predictie", "praguri.aplicat"), ("racordare.prag_afisare", "praguri.predictie"),
           # sesiunea 4
           ("culori.portocaliu", "culori.galben"), ("culori.galben", "culori.verde"),
           ("acuratete.minim_gis", "acuratete.initial_gis"), ("acuratete.aplicat_raport_executat", "praguri.aplicat"),
           ("plafon_locatie.analiza_harta", "plafon_locatie.strada"), ("plafon_locatie.strada", "plafon_locatie.adresa_numar"),
           ("plafon_locatie.adresa_numar", "plafon_locatie.coordonate"), ("verificat_om.minim", "verificat_om.scor")]
    for a, b in rel:
        if g(a) is not None and g(b) is not None and not g(a) < g(b):
            err.append(f"relație încălcată: {a} ({g(a)}) trebuie să fie < {b} ({g(b)})")
    return err


def din_head() -> dict | None:
    r = subprocess.run(["git", "show", "HEAD:contracts/weights.yaml"], cwd=ROOT, capture_output=True, text=True)
    return yaml.safe_load(r.stdout) if r.returncode == 0 else None


def diferente_valori(w: dict, vechi: dict | None) -> list[tuple[str, object, object]]:
    if not vechi:
        return []
    a, b = aplatizeaza(vechi), aplatizeaza(w)
    return [(k, a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


def diferenta_calibrare(w: dict) -> tuple[list[str], list[dict]]:
    """Evenimente care își schimbă decizia sau scorul (>0,005) față de referință."""
    from backend.engine.calibrare import ruleaza
    acum = ruleaza(w)
    if REF.exists():
        ref = {r["event_id"]: r for r in json.loads(REF.read_text(encoding="utf-8"))}
        sursa = "data/golden/calibrare-referinta.json"
    else:
        vechi = din_head()
        ref = {r["event_id"]: r for r in ruleaza(vechi)} if vechi else {}
        sursa = "weights.yaml din git HEAD (nu există referință de aur)"
    linii = []
    for r in acum:
        b = ref.get(r["event_id"])
        if not b:
            continue
        ds = (r["scor"] or 0) - (b["scor"] or 0)
        if r["decizie"] != b["decizie"] or abs(ds) > 0.005:
            linii.append(f"{r['event_id']} {r['tip']}: {b['decizie']} {b['scor']} -> {r['decizie']} {r['scor']}")
    return [f"referință: {sursa}"] + linii, acum


def distributie_culori(w: dict, data: str | None = None) -> tuple[str, dict, bool, dict]:
    """Rulează scenariul (calibrare.evenimente) cu ponderile `w`; la `data` (implicit ultima dată a scenariului).

    Întoarce (data, procente pe benzi DOAR pe rețea, în_țintă, predicții). Criteriul de rețea: vezi `TINTA_DISTRIBUTIE`
    (ID în `model._elemente()` și nivel nici `predictie`, nici `scos_din_uz`). `predicții` = {"n": N, "verde": .., "galben": ..,
    "portocaliu": .., "rosu": .., "scoase_din_uz": K} (numere absolute: tot ce e în snapshot și nu e rețea: predicții punctate,
    pinuri; K = elementele `scos_din_uz`, numărate separat și NU în n/benzi)."""
    from backend.engine import osm
    from backend.engine.calibrare import evenimente
    from backend.engine.model import GridModel
    ev, _ = evenimente()
    m = GridModel(weights=w)
    m.traseu_fn = osm.traseu_fn()
    for e in ev:
        m.apply_event(e)
    d = data or m.ultima_data
    retea_ids = m._elemente()
    retea = {"verde": 0, "galben": 0, "portocaliu": 0, "rosu": 0}
    pred = dict(retea)
    scoase = 0
    for f in m.snapshot(d)["features"]:
        p = f["properties"]
        if p["nivel"] == "scos_din_uz":
            scoase += 1          # nu mai e rețea (demontat / „demontat probabil”): nici în procent, nici în predicții
            continue
        in_retea = p["element_id"] in retea_ids and p["nivel"] != "predictie"
        (retea if in_retea else pred)[p["banda"]] += 1
    n = sum(retea.values()) or 1
    proc = {b: round(100 * v / n, 1) for b, v in retea.items()}
    return d, proc, all(lo <= proc[b] <= hi for b, (lo, hi) in TINTA_DISTRIBUTIE.items()), {"n": sum(pred.values()), **pred, "scoase_din_uz": scoase}


def rulează_smoke() -> list[str]:
    esuate = []
    env = {**os.environ, "EXTRACT_CLI": "0", "API_EXTRACTIE": os.environ.get("API_EXTRACTIE", "")}
    py = ROOT / ".venv" / "bin" / "python"
    py = str(py) if py.exists() else sys.executable
    for m in SMOKES:
        r = subprocess.run([py, "-m", m], cwd=ROOT, capture_output=True, text=True, env=env)
        print(f"  {'OK  ' if r.returncode == 0 else 'FAIL'} {m}")
        if r.returncode != 0:
            esuate.append(m)
    return esuate


def main() -> int:
    w = yaml.safe_load(WEIGHTS.read_text(encoding="utf-8"))
    limite = {k: tuple(v) for k, v in yaml.safe_load(LIMITS.read_text(encoding="utf-8")).items()}
    if "--scrie-referinta" in sys.argv:
        from backend.engine.calibrare import ruleaza
        REF.parent.mkdir(parents=True, exist_ok=True)
        REF.write_text(json.dumps(ruleaza(w), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"scris {REF.relative_to(ROOT)}")
        return 0
    erori = verifica_valori(w, limite)
    sch = diferente_valori(w, din_head())
    print("Valori schimbate față de HEAD:", ", ".join(f"{k} {a} -> {b}" for k, a, b in sch) or "(niciuna)")
    for e in erori:
        print("EROARE:", e)
    if erori:
        return 1
    linii, _ = diferenta_calibrare(w)
    print("Diferență calibrare:", linii[0])
    for l in linii[1:]:
        print("  ", l)
    if len(linii) == 1:
        print("   (nicio decizie sau scor schimbat)")
    in_tinta = True
    if "--rapid" not in sys.argv:
        d, p, in_tinta, pr = distributie_culori(w)
        tinta = ", ".join(f"{b.replace('rosu', 'roșu')} {lo:g}-{hi:g} %" for b, (lo, hi) in TINTA_DISTRIBUTIE.items())
        print(f"Distribuție culori (doar rețea) la {d}: verde {p['verde']} %, galben {p['galben']} %, portocaliu {p['portocaliu']} %, "
              f"roșu {p['rosu']} % (țintă {tinta}): " + ("în țintă" if in_tinta else "în afara țintei"))
        print(f"   predicții (nu intră în procent): {pr['n']} (verde {pr['verde']}, galben {pr['galben']}, "
              f"portocaliu {pr['portocaliu']}, roșu {pr['rosu']}); scoase din uz (nu sunt rețea): {pr['scoase_din_uz']}")
        if not in_tinta and "--strict-distributie" not in sys.argv:
            print("   (informativ; devine eșec cu --strict-distributie, după calibrare)")
    if not in_tinta and "--strict-distributie" in sys.argv:
        return 1
    esuate = [] if "--rapid" in sys.argv else rulează_smoke()
    if esuate:
        print("Smoke-uri eșuate:", ", ".join(esuate))
        return 1
    print("\nPentru board:")
    print("reglaj: " + ("; ".join(f"{k} {a} -> {b}" for k, a, b in sch) or "(nimic)") +
          f" | calibrare: {len(linii) - 1} evenimente schimbate | smoke: " + ("sărit (--rapid)" if "--rapid" in sys.argv else "toate OK"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
