# Extracție (etapa 3)

Date FICTIVE. `extract_event(text, sursa, data)` transformă un raport sau apel în `Event` conform `contracts/event.schema.json`, prin Claude (unealta `emit_event` forțată).

## Rulare
Din rădăcina repo-ului:
```bash
.venv/bin/python -m backend.extract.run_all          # toate rapoartele -> data/events/events.json
.venv/bin/python -m backend.extract.test_extract     # test offline, fără API
```

## Chei și model
- `ANTHROPIC_API_KEY` în `.env` (sau mediu). Cheie `sk-or-...` = OpenRouter: se folosește automat `openrouter.ai/api`.
- `EXTRACT_MODEL` suprascrie modelul (implicit `claude-haiku-5-5`, sau `anthropic/claude-haiku-5.5` pe OpenRouter).

## Cache
Rezultatele se scriu în `data/cache/` (cheie sha256 din model, sursă, dată, text și prompt). Cache hit = fără apel API. După o modificare de prompt cheia se schimbă automat; șterge `data/cache/` doar dacă vrei refacere completă.
