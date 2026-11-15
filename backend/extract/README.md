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

## Standardizare AI fără cheie: `cli_ai.py` (`ai_cli`)
La cache miss, înainte de API, `extract_event_cu_metoda` apelează Claude Haiku prin Claude Code headless (`claude -p`), din abonament, fără cheie. Cerință: `claude auth login` o dată pe laptop. Rezultatul intră în cache (a doua oară `ai_cache`). `EXTRACT_CLI=0` dezactivează. Test: `.venv/bin/python -m backend.extract.test_cli_ai`. Detalii: `docs/etapa-3-extractie.md`.

## Sesiunea 3: adresa structurată
Promptul completează `referinta.adresa_structurata {strada, numar, localitate, reper}` și plafonează `incredere_extractie` după localizator (cod 1.0, coordonate 0.9, stradă+număr 0.7, stradă 0.5, reper 0.3). Promptul nou schimbă toate cheile de cache: re-umple cu `fill_cache --lipsa --out` + agenți Haiku + `--import` (85 de texte, inclusiv cele 15 din `data/reports/geo-test.json`; `--lipsa` listează și textele din `data/golden/*.json`, fără `detaliu/`). Detalii: `docs/etapa-3-extractie.md`.

Sesiunea 4 (V6): `SYSTEM` cere și `referinta.adresa_structurata.indiciu {tip, numar, numar_2, strada_2, element_id, distanta_stalpi, paritate}` („lângă nr. 15”, „între nr. 10 și 20”, „la capătul străzii”, „colț cu Strada X”, „la 2 stâlpi de <ID>”, „partea cu numere pare”), cu 4 exemple. Schimbarea promptului invalidează cache-ul (`data/cache/`): `backend.api.smoke_api` pică la `ai_cache` până la reumplere (făcută pe 15 nov., vezi mai jos). Folosit de `backend.geo.fereastra_strada`; vezi `docs/etapa-31-cautare-strada.md`.

Sesiunea 4 (cache refăcut, 15 nov.): `SYSTEM` cunoaște și `verificare_om` (om din teren confirmă personal un element: `detalii.tinta_id`, status `executat`; distinct de `verificare` = inspecție de rutină). Cele 112 texte (`fill_cache.texte()`) au fost reextrase cu Haiku prin `ai_cli` (în paralel, 6 fire, ~2 min); cache-ul vechi (cheile fără corespondent) a fost șters. Refacere: modifici `SYSTEM`, listezi cu `fill_cache --lipsa --out lipsa.json` și apelezi `extract_event_cu_metoda(text, sursa, data)` pentru fiecare (cu `EXTRACT_CLI` nesetat). Detalii: `docs/etapa-3-extractie.md`.
