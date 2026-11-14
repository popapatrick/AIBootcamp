"""Test offline pentru backend-ul CLI (`claude -p`), cu un binar `claude` fals. Rulează: python -m backend.extract.test_cli_ai"""
from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path

FAKE = r'''#!/usr/bin/env python3
import json, sys
a = sys.argv[1:]
if a[:2] == ["auth", "status"]:
    print(json.dumps({"loggedIn": %(logged)s, "authMethod": "claude.ai"})); sys.exit(0)
msg = sys.stdin.read()
ev = {"tip": "nod_lipsa", "referinta": {"element_id": None, "coordonate": {"lat": 44.2849, "lon": 26.0601}, "adresa": None,
      "nr_cadastral": None, "id_client": None}, "status": "semnalat", "data": "2026-11-01", "forma_sursa": "text_liber",
      "tip_sursa_pondere": "text_liber", "incredere_extractie": 0.8, "campuri_lipsa": [], "detalii": {}}
print(json.dumps({"is_error": False, "result": "```json\n" + json.dumps(ev) + "\n```"}))
'''


def _fals(d: Path, logged: bool) -> str:
    p = d / "claude"
    p.write_text(FAKE % {"logged": "True" if logged else "False"}, encoding="utf-8")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def main() -> None:
    from backend.extract import cli_ai, extract as ex
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        ex.CACHE_DIR = t / "cache"
        os.environ.pop("EXTRACT_ALLOW_API", None)
        os.environ["CLAUDE_BIN"] = _fals(t, logged=False)
        cli_ai._stare["verificat"] = 0.0
        try:
            ex.extract_event_cu_metoda("Lipsește un stâlp la 44.2849, 26.0601.", "mentenanta", "2026-11-01")
            raise AssertionError("fără autentificare ar fi trebuit CacheMiss")
        except ex.CacheMiss:
            pass
        assert "neautentificat" in cli_ai.stare()["motiv"], cli_ai.stare()

        os.environ["CLAUDE_BIN"] = _fals(t, logged=True)
        cli_ai._stare["verificat"] = 0.0
        ev, cod = ex.extract_event_cu_metoda("Lipsește un stâlp la 44.2849, 26.0601.", "mentenanta", "2026-11-01")
        assert cod == "ai_cli" and ev["tip"] == "nod_lipsa" and ev["echipa_sursa"] == "mentenanta", (cod, ev)
        assert not list(ex._validator.iter_errors(ev))
        ev2, cod2 = ex.extract_event_cu_metoda("Lipsește un stâlp la 44.2849, 26.0601.", "mentenanta", "2026-11-01")
        assert cod2 == "ai_cache" and ev2 == ev, cod2          # a doua oară vine din cache

        os.environ["EXTRACT_CLI"] = "0"
        try:
            ex.extract_event_cu_metoda("Alt text nou fără cache.", "mentenanta", "2026-11-02")
            raise AssertionError("EXTRACT_CLI=0 ar fi trebuit CacheMiss")
        except ex.CacheMiss:
            pass
        os.environ.pop("EXTRACT_CLI")
    print("OK: backend CLI (autentificare, ai_cli, cache, dezactivare)")


if __name__ == "__main__":
    main()
