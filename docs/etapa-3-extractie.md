# Etapa 3: extracție (A)

Date FICTIVE (PTAB 7812).

## Ce face
`backend/extract/extract.py` transformă textul unui raport sau apel într un `Event` conform `contracts/event.schema.json`, folosind Claude.

```python
extract_event(text: str, sursa: str, data: str | None = None) -> dict
```
`sursa`: `mentenanta`, `investitii`, `racordari` sau `apel_client`.

## Cum funcționează
- Model: `claude-haiku-5-5`, cu unealta `emit_event` forțată (`tool_choice`), având ca input schema evenimentului.
- Validare cu `jsonschema`. La eroare, o reîncercare. Dacă și a doua e invalidă: `ValueError`.
- Cache în `data/cache/` (cheie sha256 din model + prompt `SYSTEM` + sursa + data + text). Cache hit = fără apel API.

## Cum se rulează
```bash
pip install anthropic jsonschema python-dotenv
echo 'ANTHROPIC_API_KEY=...' > .env          # cheia nu se pune în cod
python -m backend.extract.run_all            # scrie data/events/events.json
python -m backend.extract.test_extract       # test offline: fără API, fără rețea
```
`run_all` parcurge `data/reports/*.txt`, sare peste nume nerecunoscute și numerotează evenimentele `EV-001`...

## Status
- Nerulat pe API real (lipsă cheie).
- Testul offline (`test_extract`) acoperă validarea, cache-ul, reîncercarea și eroarea după reîncercare.
- Verificat: toate rapoartele comparate automat cu `data/reports/index.json`, plus citite manual `2026-08-05_mentenanta_02`, `2026-08-29_racordari_02`, `2026-10-20_mentenanta_10`.

## Limite cunoscute
- Cheie `sk-or-` (OpenRouter): folosește `base_url=openrouter.ai/api`, model `anthropic/claude-haiku-5.5` (slug verificat pe OpenRouter; suprascrie cu `EXTRACT_MODEL`).
- Cache-ul nu prinde schimbările de prompt (vezi mai sus).
- Data lipsă/invalidă (schema cere `date`, fără null): mesajul spune modelului „necunoscută; caut-o în text”; dacă răspunsul nu e YYYY-MM-DD valid, se pune data de azi și `data` intră în `campuri_lipsa` (`_data_valida`). Fix pentru `ValueError: '(din text)' is not a 'date'`.
- Coordonatele sunt luate doar dacă apar explicit în text; nu se deduc.
- Coordonate malformate (zecimală lipsă, lat/lon inversate): copiate exact ca în text, nu corectate; `coordonate_de_verificat` în `campuri_lipsa`. Corectarea o face motorul.
- `sectiune_noua` de rezervă (`_sectiune`): dacă modelul o lasă goală, se ia din text cu regex (TYIR/NA2XS, `,` sau `.`), doar la o singură potrivire distinctă și nu dacă propoziția spune demontat/vechi/scos/înlocuit. Se aplică și pe cache hit (fișierul e rescris). Euristic: nu înțelege contextul complet.

## Ce trebuie să știe ceilalți
- B: `detalii.sectiune_noua` poate veni din model sau din regex-ul determinist `_sectiune`; EV-010 (A-T-021, 3x50) a fost completat așa → conflict cu EV-009 (3x70) în scenariul 5.
- B: `events.json` are același format ca `events.stub.json`, cu ID-uri `EV-001`...

## Rulare reală (OpenRouter)
- 28/28 evenimente valide pe schemă în `data/events/events.json`.
- Față de `data/reports/index.json`: `element_id` 28/28, `tip` 27/28 (excepție: `2026-08-29_racordari_02`, scenariul 5, extras ca `racord_nou`).
- `verificare` = inspecție fără defecte (contract `bf8e4ae`). Coduri de tronson fără prefix (`T-054`) → `element_id: null`, cod brut în `detalii.id_partial`.
- Cheia de cache include promptul de sistem: o schimbare de prompt invalidează cache-ul automat.

Dată: când apelantul nu dă `data`, data întoarsă de model se păstrează doar dacă apare efectiv în text (ISO, DD.MM.YYYY, DD/MM/YYYY, „14 septembrie 2026"); altfel data de azi și „data" în `campuri_lipsa`. Verificarea se aplică și pe intrările din cache (reparat de C la cererea omului).

## Fără cheie API: cache + stub (14 nov.)
- `extract_event`: cache hit întoarce evenimentul; cache miss ridică `CacheMiss` (exportat), dacă nu e `EXTRACT_ALLOW_API=1`. `backend/api/pipeline.py` prinde `Exception` și folosește stub-ul regex (`metoda_extractie` = `stub_regex (rezervă: CacheMiss)`). Cu `EXTRACT_ALLOW_API=1` (producție) apelul API, validarea și reîncercarea merg ca înainte.
- Cheia de cache nu mai depinde de `MODEL`: `cache_key` = sha256(`CACHE_TAG`="agent-haiku" + `SYSTEM` + sursa + data + text). Vechiul cache (cu MODEL în hash) nu mai e găsit; cele 91 de fișiere existente trebuie regenerate (nu le-am șters).
- Unealta `python -m backend.extract.fill_cache`: `--lipsa [--out]` listează textele fără cache (exemple-dummy cu `om_teren`, rapoartele din `index.json`; acum 70 de texte), `--prompt` dă `SYSTEM` + schema, `--import fisier.json` ia `[{text, sursa, data, event}]` de la subagenții Haiku, aplică `_finalizeaza` (event_id, `_data_valida`, `_normalizeaza`, `_sectiune`, schema) și scrie în cache; tipărește OK/ERR per element.
- Flux: `--lipsa --out` -> loturi către agenți Haiku (primesc `system` + `user_message`, întorc JSON) -> `--import`.
- Neacoperit: `trasee-dummy.json` (fără texte de raport) și textele din `docs/DEMO.md` (fără dată fixă, deci cheie variabilă).
- Verificare: `.venv/bin/python -m backend.extract.test_extract` (CacheMiss implicit, calea `EXTRACT_ALLOW_API=1`, cheie fără MODEL, round-trip `--import`). **Atenție:** regulile din prompt (ex. stâlp necartat = `nod_lipsa`, `mutare_fire`, decizie om) sunt verificate doar cu mock; trebuie verificate cu un agent Haiku real înainte de a considera cache-ul bun.

## Metoda de extracție (contract: `metoda_cod`)
`extract_event_cu_metoda(text, sursa, data=None) -> (event, metoda_cod)` (exportat din `backend.extract`): `ai_cache` la cache hit, `ai_api` la apel API; `CacheMiss` rămâne neschimbat (apelantul folosește `regex`). `extract_event` = `extract_event_cu_metoda(...)[0]`, semnătura neschimbată; metoda nu e în event.

## Standardizare cu AI fără cheie: backend Claude Code headless (`ai_cli`) (adăugat de B, la cererea lui Victor)
Regex nu mai e calea normală a demo-ului: un text nou, fără cache, se standardizează cu AI. `extract_event_cu_metoda` încearcă, în ordine: cache (`ai_cache`), **Claude Haiku prin Claude Code headless** (`ai_cli`, din abonament, fără cheie API), API-ul (`ai_api`, doar cu `EXTRACT_ALLOW_API=1`, cheia demo), apoi `CacheMiss` (API-ul cade pe regex, ultima rezervă, marcată „Regex (simplificat)"). Rezultatul `ai_cli` se scrie în `data/cache/`, deci a doua oară e `ai_cache`.
- Cod: `backend/extract/cli_ai.py` (`gaseste_claude`, `stare`, `call_cli`), cârlig în `extract_event_cu_metoda` (cache miss, înaintea gate-ului API).
- Cerință, o singură dată pe laptopul demo: autentificare în abonament, fără cheie: `claude auth login` (se deschide browserul). Verificare: `claude auth status` -> `"loggedIn": true`. Binarul se caută în `CLAUDE_BIN`, PATH sau aplicația Claude pentru Mac.
- Variabile: `EXTRACT_CLI=0` dezactivează; `EXTRACT_CLI_MODEL` (implicit `haiku`); `EXTRACT_CLI_TIMEOUT` (90 s). Procesul rulează într-un director temporar (nu încarcă CLAUDE.md al proiectului) și fără chei API în mediu.
- Latență: câteva secunde per text nou (UI-ul arată „standardizare AI în curs"); cache-ul face textele de demo instantanee.
- Verificare: `.venv/bin/python -m backend.extract.test_cli_ai` (binar fals: neautentificat -> CacheMiss; autentificat -> `ai_cli` și apoi `ai_cache`). Testat cu binar fals; apelul real depinde de autentificare și nu a putut fi rulat până acum (binarul din aplicația Claude era neautentificat).
- Limită: pe laptopurile fără login rămâne cache + regex (ultima rezervă).

## Sesiunea 3: `adresa_structurata` și încredere după standardizare (A2)
- Promptul `SYSTEM` completează `referinta.adresa_structurata {strada, numar, localitate, reper}` (null pentru părțile lipsă, nimic inventat; strada copiată cum apare, cu ortografia greșită, pentru că alegerea o face `backend.geo`). `referinta.adresa` rămâne textul brut. Schema uneltei (`_schema`, din `contracts/event.schema.json`) conține deja câmpul (contract B).
- `incredere_extractie` are plafon după cel mai bun localizator din text, ca în `weights.yaml` `standardizare.plafon_dupa_localizator`: cod 1.0, coordonate 0.9, stradă+număr 0.7, stradă/intersecție 0.5, reper 0.3 (intersecția nu e în tabel; am pus 0.5). Promptul are 4 exemple de grade diferite. Plafonul real îl aplică motorul (B2); promptul doar îl apropie.
- Set de calibrare `data/reports/geo-test.json` (15 adrese, de la cod existent la vag/necunoscut), generat de `data/reports/genereaza_geo_test.py` din geometria OSM (`osm.strazi()`, `network.geojson`): stradă/număr = mijlocul celui mai lung tronson cu numele (numărul nu e interpolat), intersecție = nodul comun. Fiecare intrare: `text, sursa, data, adresa_structurata_asteptata, asteptat {status, lat, lon, toleranta_m, acuratete_tinta}, plafon_incredere`. Textele intră în `fill_cache --lipsa`.
- Re-umplere cache: promptul s-a schimbat, deci `cache_key` s-a schimbat pentru TOATE textele. `fill_cache --lipsa` listează 85 de texte (70 vechi + 15 din geo-test); de umplut cu agenți Haiku (`--lipsa --out`, `--import`). Până atunci `CacheMiss` -> stub regex.
- Limite: exemplele din prompt nu sunt verificate cu un model real; ținta geo-test pentru numere e doar mijlocul străzii; `gt-12` (reper aproape de Carpati) are ținta aproximată.
