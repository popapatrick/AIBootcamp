"""Banc de logică (C2): texte de test prin pipeline-ul din POST /rapoarte, fără server HTTP.

Rulare: `python -m backend.api.banc_logica [--fisier F] [--json] [--doar-diferente] [--cu-ai]`
Sursa implicită: `data/golden/*.json` (listă de {id, sursa, text, data?, asteptat?}); dacă lipsește,
`data/reports/exemple-dummy.json`. Rulează pe modelul din memorie; nu scrie în data/.
`asteptat` (opțional) poate avea: tip, decizie, nivel, origine, slaba, treapta, eronat_prototip, element_id.
Câmpurile pe care contractul le are doar în sesiunea 3 și lipsesc din rezultat apar ca „-".
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "data" / "golden"
DUMMY = ROOT / "data" / "reports" / "exemple-dummy.json"
COLOANE = ["id", "sursa", "tip", "metoda_cod", "decizie", "scor", "origine", "slaba", "treapta", "eronat", "ok"]


def incarca(fisier: str | None = None) -> tuple[list[dict], str]:
    """Întoarce (cazuri, nota sursei). Cazuri = [{id, sursa, text, data?, asteptat?}]."""
    cai = [Path(fisier)] if fisier else sorted(GOLDEN.glob("*.json")) if GOLDEN.is_dir() else []
    cai = [c for c in cai if c.name != "calibrare-referinta.json"] if not fisier else cai
    nota = ""
    if not cai:
        cai, nota = [DUMMY], "ATENȚIE: data/golden/ nu există (A6 nu e gata); folosesc data/reports/exemple-dummy.json."
    cazuri: list[dict] = []
    for c in cai:
        d = json.loads(c.read_text(encoding="utf-8"))
        if isinstance(d, dict):   # exemple-dummy: {sursa: [{id, text, data, asteptat}]}
            d = [{**x, "sursa": s} for s, lst in d.items() for x in lst]
        cazuri += d
    return cazuri, nota or f"Sursa: {', '.join(str(c.relative_to(ROOT)) if c.is_relative_to(ROOT) else str(c) for c in cai)}"


def _g(d, *chei):
    for k in chei:
        d = d.get(k) if isinstance(d, dict) else None
    return d


def ruleaza_caz(caz: dict) -> dict:
    """Rulează un caz prin `pipeline.proceseaza`; întoarce rândul (câmpuri plate, None = lipsă) + `ok` față de `asteptat`."""
    from backend.api import pipeline
    out = pipeline.proceseaza(caz["text"], caz["sursa"], caz.get("data"))
    pasi = {p["nume"]: p for p in out.get("pasi", [])}
    ev = _g(pasi.get("extractie"), "rezultat") or {}
    mod = (out.get("modificari") or [{}])[0]
    pred = mod.get("predictie") or _g(pasi.get("predictie"), "rezultat") or {}
    sch = (out.get("schimbari") or [{}])[0]
    r = {"id": caz.get("id"), "sursa": caz["sursa"], "tip": ev.get("tip"),
         "metoda_cod": _g(pasi.get("extractie"), "metoda_cod"),
         "decizie": out.get("decizie") or mod.get("nivel") or sch.get("ce"),
         "scor": _g(pasi.get("scor"), "rezultat", "scor_nou") or mod.get("scor"),
         "origine": mod.get("origine") or pred.get("origine"),
         "slaba": pred.get("slaba"), "treapta": pred.get("treapta"),
         "eronat": out.get("eronat_prototip"),
         # element referit (potrivire, apoi ID din text); `modificari[0].element_id` e doar elementul creat de motor (ex. NOU-...)
         "element_id": _g(pasi.get("potrivire"), "rezultat", "element_id") or _g(ev, "referinta", "element_id") or mod.get("element_id"),
         "element_modificat": mod.get("element_id"),
         # doar în --json (nu în tabel): pasul geocodare (B2) și traseul generat (B4)
         "geocodare_status": _g(pasi.get("geocodare"), "rezultat", "status"),
         "precizie_m": _g(pasi.get("geocodare"), "rezultat", "precizie_m"),
         "trace_sursa": _g(pasi.get("trace"), "rezultat", "sursa")}
    ast = caz.get("asteptat")
    if ast:
        gresit = [k for k, v in ast.items()
                  if k in ({**r, "eronat_prototip": r["eronat"]}) and v is not None
                  and {**r, "eronat_prototip": r["eronat"]}[k] != v]
        r["ok"] = not gresit
        r["diferente"] = gresit
    else:
        r["ok"] = None
    return r


def ruleaza(cazuri: list[dict]) -> list[dict]:
    """Rulează toate cazurile; o eroare pe un caz devine rând cu `eroare`, nu oprește banca."""
    rez = []
    for c in cazuri:
        try:
            rez.append(ruleaza_caz(c))
        except Exception as e:
            rez.append({"id": c.get("id"), "sursa": c.get("sursa"), "eroare": f"{type(e).__name__}: {e}", "ok": False})
    return rez


def _fmt(v) -> str:
    return "-" if v is None else ("da" if v is True else "nu" if v is False else f"{v:.3f}" if isinstance(v, float) else str(v))


def tabel(rez: list[dict]) -> str:
    """Tabel text aliniat; `ok`: da/nu/- (fără asteptat)."""
    rows = [COLOANE] + [[_fmt(r.get(c)) for c in COLOANE] for r in rez]
    w = [max(len(x[i]) for x in rows) for i in range(len(COLOANE))]
    return "\n".join("  ".join(c.ljust(w[i]) for i, c in enumerate(x)) for x in rows)


def sumar(rez: list[dict]) -> dict:
    """{total, cu_asteptat, ok, nok, erori}."""
    ca = [r for r in rez if r.get("ok") is not None]
    return {"total": len(rez), "cu_asteptat": len(ca), "ok": sum(r["ok"] for r in ca),
            "nok": sum(not r["ok"] for r in ca), "erori": sum("eroare" in r for r in rez)}


def main(argv: list[str] | None = None) -> int:
    """Intrarea CLI. Cod de ieșire 1 dacă există rânduri nepotrivite sau erori."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fisier", help="JSON cu cazuri (implicit data/golden/, apoi exemple-dummy)")
    ap.add_argument("--json", action="store_true", help="ieșire mașină (JSON)")
    ap.add_argument("--doar-diferente", action="store_true", help="doar rândurile cu ok=nu sau eroare")
    ap.add_argument("--cu-ai", action="store_true", help="permite ai_cli (Claude Code); implicit EXTRACT_CLI=0")
    a = ap.parse_args(argv)
    if not a.cu_ai:
        os.environ["EXTRACT_CLI"] = "0"
    cazuri, nota = incarca(a.fisier)
    rez = ruleaza(cazuri)
    s = sumar(rez)
    vis = [r for r in rez if r.get("ok") is False] if a.doar_diferente else rez
    if a.json:
        print(json.dumps({"sursa": nota, "sumar": s, "rezultate": vis}, ensure_ascii=False, indent=1))
    else:
        print(nota)
        print(tabel(vis) if vis else "(nimic de arătat)")
        print(f"\nSumar: {s['total']} cazuri, {s['cu_asteptat']} cu asteptat: {s['ok']} ok, {s['nok']} diferite, {s['erori']} erori")
    return 1 if s["nok"] or s["erori"] else 0


if __name__ == "__main__":
    sys.exit(main())
