# Extracție (etapa 3)

Date FICTIVE. `extract_event(text, sursa, data)` transformă un raport sau apel în `Event` conform `contracts/event.schema.json`, prin Claude (unealta `emit_event` forțată).

## Rulare
Din rădăcina repo-ului:
```bash
.venv/bin/python -m backend.extract.run_all          # toate rapoartele -> data/events/events.json
.venv/bin/python -m backend.extract.test_extract     # test offline, fără API
```

## Flux fără cheie API (decis 14 nov.)
- La rulare: `extract_event` = **cache hit** (din `data/cache/`) sau **`CacheMiss`** (exportat din `backend.extract`). `backend/api/pipeline.py` prinde `Exception` și cade pe stub regex.
- Producție cu API: `EXTRACT_ALLOW_API=1` + `ANTHROPIC_API_KEY` (`sk-or-...` = OpenRouter); `EXTRACT_MODEL` suprascrie modelul. Implicit oprit.
- Cheia de cache: `cache_key(text, sursa, data)` = sha256(`CACHE_TAG` ("agent-haiku") + `SYSTEM` + sursa + data + text); nu depinde de model. Schimbarea promptului `SYSTEM` invalidează cache-ul.

## Umplerea cache-ului cu subagenți Haiku (`fill_cache`)
```bash
.venv/bin/python -m backend.extract.fill_cache --lipsa --out lipsa.json   # texte fără cache: [{text, sursa, data, user_message}]
.venv/bin/python -m backend.extract.fill_cache --prompt                   # SYSTEM + schema uneltei, pentru agenți
.venv/bin/python -m backend.extract.fill_cache --import rezultate.json    # [{text, sursa, data, event}] -> validare -> cache
```
Agentul Haiku primește `system` + `user_message` și întoarce JSON-ul evenimentului. Importul aplică același post-proces ca API-ul (`_finalizeaza`: event_id, data, `_normalizeaza`, `_sectiune`, schema). Sunt acoperite `exemple-dummy.json` (cu `om_teren`) și rapoartele din `data/reports/index.json`; nu `trasee-dummy.json` (fără texte) și nu textele din `DEMO.md` (fără dată fixă).

## Rulare
```bash
.venv/bin/python -m backend.extract.run_all          # toate rapoartele -> data/events/events.json (din cache)
.venv/bin/python -m backend.extract.test_extract     # test offline, fără API
```

## Sesiunea 2: tipuri noi
Promptul acoperă și `apel_client` (call center), `mutare_fire` (`detalii.centru/raza_m/motiv_mutare`), `cerere_racordare` (locația în `referinta.coordonate`) și decizia omului (`verificare`, sursa `om_teren`, `detalii.decizie`). `extract_event` acceptă sursa `om_teren`. Atenție: schimbarea promptului schimbă cheile din `data/cache/`: rapoartele deja extrase dau cache miss (`CacheMiss`) până la reumplere cu `fill_cache`. Vezi `docs/etapa-13-mutare-fire.md`.

`extract_event_cu_metoda(text, sursa, data=None) -> (event, metoda_cod)`: aceeași logică ca `extract_event` (care o apelează), plus `metoda_cod` = `ai_cache` (cache hit) sau `ai_api` (apel API cu `EXTRACT_ALLOW_API=1`). Cache miss fără API: `CacheMiss`, apelantul cade pe `regex`. Metoda nu intră în event (cache și schemă neschimbate).
