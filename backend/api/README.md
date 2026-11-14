# backend/api/ (proprietar: C)

API FastAPI pentru prototip (etapa 7). Implementează `contracts/api.openapi.yaml`. Date FICTIVE.

- `main.py`: aplicația și endpoint-urile; servește și UI-ul plan B (`frontend/plan-b/`) la `/ui/`.
- `sources.py`: de unde vin datele (motorul lui B → fișierele lui B → eșantionul `data/model/sample/`), ales automat.
- `pipeline.py`: `POST /rapoarte` (extracție → potrivire → predicție → scor); folosește `extract_event` (A) și `apply_event` (B) când există, altfel stub + `match_event` real.
- `POST /predictii/{id}/decizie`: Event `om_teren` dat lui `apply_event`; 404 necunoscută, 409 deja decisă, 400 invalidă. `?scenariu=extrem`: `engine.model_scenariu("extrem")` (404 dacă lipsește fișierul). `API_EXTRACTIE=stub` forțează extracția regex. Detalii: `docs/etapa-7b-api-sesiunea-2.md`.
- `smoke_api.py`: test pe toate endpoint-urile.

```bash
python3 -m venv .venv && .venv/bin/pip install -r backend/api/requirements.txt
.venv/bin/python -m backend.api.smoke_api                    # așteptat: OK: API
.venv/bin/uvicorn backend.api.main:app --reload --port 8000  # UI: http://localhost:8000/ui/
```

## metoda_cod și regex (sesiunea 3)
`pasi[extractie].metoda_cod` = `ai_cache` | `ai_api` | `regex`; `/health.extractie_cod` la fel. Cache miss -> `CacheMiss` -> regex, cu `motiv`. Regex înțelege textele butoanelor Cerere racordare / Fire mutate / Raport tabletă. Detalii: `docs/etapa-7b-api-sesiunea-2.md`.
