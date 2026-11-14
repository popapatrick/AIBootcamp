"""Umple data/cache/ fără API: listează textele fără cache, importă rezultatele subagenților Haiku.

    python -m backend.extract.fill_cache --lipsa [--out lipsa.json]   # [{text, sursa, data, user_message}]
    python -m backend.extract.fill_cache --import rezultate.json       # [{text, sursa, data, event}]
    python -m backend.extract.fill_cache --prompt                      # SYSTEM + schema uneltei (JSON)

Importul trece fiecare event prin același post-proces ca rezultatul API (_finalizeaza) și îl scrie sub cache_key.
"""
import argparse
import json
import sys

from backend.extract import extract as ex

REPORTS = ex.ROOT / "data" / "reports"


def texte() -> list[tuple[str, str, str | None]]:
    """(text, sursa, data) pentru exemple-dummy.json și rapoartele din index.json (aceleași ca run_all)."""
    out = []
    dummy = json.loads((REPORTS / "exemple-dummy.json").read_text(encoding="utf-8"))
    for sursa, lista in dummy.items():
        out += [(x["text"], sursa, x["data"]) for x in lista]
    for e in json.loads((REPORTS / "index.json").read_text(encoding="utf-8")):
        out.append(((REPORTS / e["fisier"]).read_text(encoding="utf-8"), e["sursa"], e["data"]))
    # setul de calibrare geocodare (sesiunea 3): texte cu grade diferite de standardizare
    geo = REPORTS / "geo-test.json"
    if geo.exists():
        out += [(x["text"], x["sursa"], x["data"]) for x in json.loads(geo.read_text(encoding="utf-8"))["adrese"]]
    # shortcut: trasee-dummy.json n-are texte de raport (doar descriere/puncte) și textele din docs/DEMO.md n-au dată fixă
    # (cheia depinde de data zilei la rulare live), deci nu sunt listate; de adăugat dacă apar câmpuri `text` / date fixe.
    return out


def lipsa() -> list[dict]:
    """Textele fără intrare în cache, deduplicate."""
    seen, res = set(), []
    for text, sursa, data in texte():
        k = ex.cache_key(text, sursa, data)
        if k in seen or (ex.CACHE_DIR / f"{k}.json").exists():
            continue
        seen.add(k)
        res.append({"text": text, "sursa": sursa, "data": data, "user_message": ex.user_message(text, sursa, data)})
    return res


def importa(items: list[dict]) -> tuple[int, int]:
    """Validează și scrie în cache. Întoarce (ok, erori)."""
    ok = err = 0
    for i, it in enumerate(items):
        text, sursa, data = it["text"], it["sursa"], it.get("data")
        key = ex.cache_key(text, sursa, data)
        ev, errors = ex._finalizeaza(it.get("event"), text, sursa, data, key)
        if errors:
            err += 1
            print(f"ERR {i} ({sursa}): {errors[:2]}")
        else:
            ex.write_cache(key, ev)
            ok += 1
            print(f"OK  {i} ({sursa}) {ev['tip']}")
    print(f"Total: {ok} OK, {err} ERR")
    return ok, err


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lipsa", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--import", dest="imp")
    ap.add_argument("--prompt", action="store_true")
    a = ap.parse_args()
    if a.prompt:
        print(json.dumps({"system": ex.SYSTEM, "tool": ex.TOOL, "input_schema": ex.tool_schema()}, ensure_ascii=False, indent=2))
    elif a.lipsa:
        res = lipsa()
        if a.out:
            with open(a.out, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
        print(f"{len(res)} texte fără cache" + (f" -> {a.out}" if a.out else ""), file=sys.stderr if not a.out else sys.stdout)
        if not a.out:
            print(json.dumps(res, ensure_ascii=False, indent=2))
    elif a.imp:
        with open(a.imp, encoding="utf-8") as f:
            _, err = importa(json.load(f))
        sys.exit(1 if err else 0)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
