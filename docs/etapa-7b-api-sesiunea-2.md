# Etapa 7b: API sesiunea 2 (C1)

Date FICTIVE. Cod în `backend/api/`. Verificare: `.venv/bin/python -m backend.api.smoke_api` (ultima linie `OK: API`).

## Ce face
- `POST /rapoarte`: câmpuri noi `locatie {lat,lon}` și `trace [{t,lat,lon}]`. Intră în `detalii.locatie`, `detalii.centru`, `detalii.trace` ale Event-ului; `locatie` completează `referinta.coordonate` doar dacă extracția n-a găsit. Răspunsul are mereu `schimbari` (din motor; `[]` doar dacă motorul nu le dă; B3 le dă) și `ultima_actualizare`.
- `ultima_actualizare` (din `statistici(data)` al motorului, din B3 (ea24eeb); `null` doar dacă motorul nu o dă): apare în `GET /health`, `GET /retea` (nivel superior al FeatureCollection) și `POST /rapoarte`.
- `GET /exemple?sursa=`: din `data/reports/exemple-dummy.json` (listă cu `sursa` per element sau `{sursa: [...]}`); `[]` dacă lipsește.
- `GET /trasee-demo`: din `data/reports/trasee-dummy.json`; `[]` dacă lipsește.
- `POST /predictii/{id}/decizie` `{decizie: accepta|respinge, motiv, data}`: construiește Event `verificare`/`om_teren` (`EV-DEC-NNN`, `detalii.decizie`) și îl dă lui `apply_event` (B4). Întoarce StepTrace cu `schimbari`. `trace.eroare.cod`: `deja_decis` -> 409, `necunoscut` -> 404, `decizie_invalida` -> 400; 501 doar fără motor real.
- `?scenariu=extrem` pe `/retea` și `/evenimente`: model separat (evenimente de bază + `data/events/events.extreme.json`); 404 clar dacă fișierul lipsește. Rapoartele live nu se amestecă în scenariu.

## Limite
- Decizia: verificată real (200, apoi 409, 404). Id exemplu: `NOU-EV-LIVE-004` (nod prezis după un apel_client cu coordonate).
- Scenariul extrem vine din `engine.model_scenariu("extrem")` (B); `FileNotFoundError` -> 404 clar. Testat cu `events.extreme.json` real (A6): 68 evenimente vs 29 în bază. `/exemple` și `/trasee-demo` citesc formatul real (dict pe sursă, inclusiv cheia `om_teren`, neexpusă în `/exemple`).
- `/element/{id}` nu acceptă `scenariu`.

## C1c: aliniere la B5-B8
- `sources.model_extrem()` doar înfășoară `engine.model_scenariu("extrem")`; fără shortcut local.
- Decizia rămâne pe `apply_event` + `trace.eroare.cod`: `engine.aplica_decizie` pierde codul (`deja_decis` și `decizie_invalida` devin ambele `ValueError`), deci nu poate da 409 vs 400.
- `tip`/`eticheta` (timeline), `verificat_recent`, nivelul `scos_din_uz`, pasul `trace` și `potrivire.status: zona` trec neatinse (API-ul nu remapează câmpuri). Locația: `detalii.centru` (mutare_fire) și `detalii.locatie` / `referinta.coordonate` (racordare) sunt deja setate din `locatie`; nu a fost nevoie de alt câmp.
- `API_EXTRACTIE=stub` forțează extracția regex (teste/demo fără cheie). `smoke_api` pregătește predicția și `mutare_fire` direct prin `apply_event`, deci trece identic cu Claude și cu stub: rulează ambele moduri.
