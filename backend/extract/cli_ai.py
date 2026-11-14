"""Standardizare cu AI prin Claude Code în mod headless (`claude -p`), din abonament, FĂRĂ cheie API.

Când un text nu e în cache, `extract_event_cu_metoda` încearcă mai întâi aici (metoda_cod `ai_cli`), apoi API-ul (doar cu
EXTRACT_ALLOW_API=1), apoi CacheMiss (API-ul de sus cade pe regex). Rezultatul se scrie în cache (data/cache/), deci a doua oară e `ai_cache`.

Cerințe: binarul `claude` (din PATH, `CLAUDE_BIN` sau aplicația Claude pentru Mac) și autentificare în abonament, o singură dată:
    claude auth login      # se deschide browserul; fără cheie API
Dezactivare: EXTRACT_CLI=0. Model: EXTRACT_CLI_MODEL (implicit haiku). Timeout: EXTRACT_CLI_TIMEOUT (implicit 90 s).
Rulează într-un director temporar, ca să nu încarce CLAUDE.md-ul proiectului. Date FICTIVE.
"""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

_stare: dict = {"verificat": 0.0, "ok": False, "motiv": "neverificat"}
_TTL = 60.0   # cât timp ținem minte că nu e autentificat (nu lansăm un proces la fiecare text)


def gaseste_claude() -> str | None:
    """Calea binarului `claude`: CLAUDE_BIN, PATH, aplicația Claude pentru Mac."""
    cale = os.environ.get("CLAUDE_BIN")
    if cale and Path(cale).is_file():
        return cale
    din_path = shutil.which("claude")
    if din_path:
        return din_path
    cand = sorted(glob.glob(str(Path.home() / "Library/Application Support/Claude/claude-code/*/*/claude.app/Contents/MacOS/claude")))
    return cand[-1] if cand else None


def _env() -> dict:
    """Mediul copilului: fără chei API (se folosește doar abonamentul)."""
    e = dict(os.environ)
    for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        e.pop(k, None)
    return e


def stare(forta: bool = False) -> dict:
    """{ok, motiv}: există binarul și e autentificat în abonament? Rezultatul se ține minte 60 s."""
    if os.environ.get("EXTRACT_CLI") == "0":
        return {"ok": False, "motiv": "dezactivat (EXTRACT_CLI=0)"}
    if not forta and time.time() - _stare["verificat"] < _TTL:
        return {"ok": _stare["ok"], "motiv": _stare["motiv"]}
    binar = gaseste_claude()
    if not binar:
        r = {"ok": False, "motiv": "binarul claude nu a fost găsit (instalează Claude Code sau setează CLAUDE_BIN)"}
    else:
        try:
            p = subprocess.run([binar, "auth", "status"], capture_output=True, text=True, timeout=20, env=_env())
            d = json.loads(p.stdout or "{}")
            r = ({"ok": True, "motiv": f"autentificat ({d.get('authMethod', '?')})"} if d.get("loggedIn")
                 else {"ok": False, "motiv": "neautentificat: rulează `claude auth login` o dată (abonament, fără cheie API)"})
        except Exception as e:  # binar defect, timeout, ieșire neașteptată
            r = {"ok": False, "motiv": f"{type(e).__name__}: {e}"}
    _stare.update(verificat=time.time(), ok=r["ok"], motiv=r["motiv"])
    return r


def _json_din_text(t: str) -> dict | None:
    t = (t or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        d = json.loads(t)
        return d if isinstance(d, dict) else None
    except ValueError:
        i, j = t.find("{"), t.rfind("}")
        if i >= 0 and j > i:
            try:
                d = json.loads(t[i:j + 1])
                return d if isinstance(d, dict) else None
            except ValueError:
                return None
    return None


def call_cli(system: str, schema: dict, mesaj: str) -> dict | None:
    """Un apel Claude (Haiku) prin CLI. Întoarce evenimentul brut (dict) sau None dacă nu merge.

    `system` = promptul extractorului, `schema` = schema evenimentului, `mesaj` = mesajul utilizatorului."""
    if not stare()["ok"]:
        return None
    binar = gaseste_claude()
    cmd = [binar, "-p", "--model", os.environ.get("EXTRACT_CLI_MODEL", "haiku"), "--output-format", "json",
           "--no-session-persistence", "--tools", "", "--disable-slash-commands",
           "--system-prompt", system + "\n\nRăspunde DOAR cu obiectul JSON al evenimentului, fără alt text.",
           "--json-schema", json.dumps(schema, ensure_ascii=False)]
    try:
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run(cmd, input=mesaj, capture_output=True, text=True, cwd=d, env=_env(),
                               timeout=float(os.environ.get("EXTRACT_CLI_TIMEOUT", "90")))
        out = json.loads(p.stdout)
    except Exception as e:
        _stare.update(verificat=time.time(), ok=False, motiv=f"apel CLI eșuat: {type(e).__name__}")
        return None
    if out.get("is_error"):
        _stare.update(verificat=time.time(), ok=False, motiv=f"CLI: {str(out.get('result'))[:120]}")
        return None
    so = out.get("structured_output")
    return so if isinstance(so, dict) else _json_din_text(out.get("result", ""))
