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
