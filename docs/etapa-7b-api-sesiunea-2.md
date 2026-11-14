# Etapa 7b: API sesiunea 2 (C1)

Date FICTIVE. Cod în `backend/api/`. Verificare: `.venv/bin/python -m backend.api.smoke_api` (ultima linie `OK: API`).

## Ce face
- `POST /rapoarte`: câmpuri noi `locatie {lat,lon}` și `trace [{t,lat,lon}]`. Intră în `detalii.locatie`, `detalii.centru`, `detalii.trace` ale Event-ului; `locatie` completează `referinta.coordonate` doar dacă extracția n-a găsit. Răspunsul are mereu `schimbari` (din motor; `[]` doar dacă motorul nu le dă; B3 le dă) și `ultima_actualizare`.
- `ultima_actualizare` (din `statistici(data)` al motorului, din B3 (ea24eeb); `null` doar dacă motorul nu o dă): apare în `GET /health`, `GET /retea` (nivel superior al FeatureCollection) și `POST /rapoarte`.
- `GET /exemple?sursa=`: din `data/reports/exemple-dummy.json` (listă cu `sursa` per element sau `{sursa: [...]}`); `[]` dacă lipsește.
- `GET /trasee-demo`: din `data/reports/trasee-dummy.json`; `[]` dacă lipsește.
- `POST /predictii/{id}/decizie` `{decizie: accepta|respinge, motiv, data}`: construiește Event `verificare`/`om_teren` și cheamă `aplica_decizie(event)` din motor. 501 dacă funcția lipsește; KeyError -> 404, ValueError -> 409.
- `?scenariu=extrem` pe `/retea` și `/evenimente`: model separat (evenimente de bază + `data/events/events.extreme.json`); 404 clar dacă fișierul lipsește. Rapoartele live nu se amestecă în scenariu.

## Limite
- Decizia: nu simulează; 501 până la B4. Numele `aplica_decizie(event)` e presupunerea mea, de confirmat de Victor.
- Scenariul extrem e construit în `sources.model_extrem()` (folosește `GridModel` direct) până engine acceptă sursa `extreme` (B 3.3). Netestat cu fișier real.
- `/element/{id}` nu acceptă `scenariu`.
