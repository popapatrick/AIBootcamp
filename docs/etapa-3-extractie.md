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
- Cache în `data/cache/` (cheie sha256 din model + sursa + data + text). Cache hit = fără apel API.
- Promptul (`SYSTEM`) nu intră în cheia cache. După orice modificare a promptului: șterge `data/cache/*.json`.

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
- Pendinte: verificare manuală a ≥3 rapoarte față de `data/reports/index.json`.

## Limite cunoscute
- Cheie `sk-or-` (OpenRouter): folosește `base_url=openrouter.ai/api`, model `anthropic/claude-haiku-5.5` (slug verificat pe OpenRouter; suprascrie cu `EXTRACT_MODEL`).
- Cache-ul nu prinde schimbările de prompt (vezi mai sus).
- Coordonatele sunt luate doar dacă apar explicit în text; nu se deduc.

## Ce trebuie să știe ceilalți
- B: `events.json` are același format ca `events.stub.json`, cu ID-uri `EV-001`...

## Rulare reală (OpenRouter)
- 28/28 evenimente valide pe schemă în `data/events/events.json`.
- Față de `data/reports/index.json`: `element_id` 28/28, `tip` 27/28 (excepție: `2026-08-29_racordari_02`, scenariul 5, extras ca `racord_nou`).
- `verificare` = inspecție fără defecte (contract `bf8e4ae`). Coduri de tronson fără prefix (`T-054`) → `element_id: null`, cod brut în `detalii.id_partial`.
- Cheia de cache include promptul de sistem: o schimbare de prompt invalidează cache-ul automat.
