# Etapa 16: trasee dummy și `backend/trace` (A3 + A5)

Date fictive. Vezi `openspec/changes/locatie-din-trace-tableta/`.

## Ce face
- `backend/trace/`: `gaseste_opriri(puncte, cfg)` și `localizeaza(trace, adresa, net, strazi, cfg)` (funcții pure, semnături din `contracts/interfaces.md`).
- `data/reports/trasee-dummy.json`: 4 trasee de ~1 oră, punct la 25 s, zgomot GPS ~1,5 m. Câmpuri: `id`, `descriere`, `adresa`, `data`, `puncte[{t, lat, lon}]`.

| id | scenariu | rezultat așteptat |
|---|---|---|
| trace-1 | 3 stâlpi existenți verificați (~4 min) + 22 min fără stâlp pe Strada Liviu Rebreanu | `gasit`, `element_id` null (stâlp prezis), 3 `vizitate` |
| trace-2 | două opriri fără stâlp, 11 și 10,5 min, Strada Bălții | `ambiguu`, calitate 0,54 |
| trace-3 | adresa „Strada Fluturilor" nu există | `gasit`, `strada` null, calitate 0,63 |
| trace-4 | doar mers | `fara_opriri` |

## Cum se rulează / verifică
`.venv/bin/python -m backend.trace.smoke_trace` -> `OK: 10 verificări` (opriri, stradă, ambiguitate, fără stradă, fără opriri, toate traseele din fișier).

## Intrări / ieșiri
Intrări: `trace` (listă de puncte), `adresa`, `net = load_network()`, `strazi = osm.strazi()`, `cfg = load_weights()`. Ieșire: structura din `interfaces.md`.

## Decizii
- Oprire: puncte consecutive la cel mult `raza_oprire_m` de centroidul grupului; durata = ultimul - primul punct.
- Strada: numele normalizat (fără diacritice, majuscule, prefix Strada/Str./Bd./Aleea etc.) trebuie să apară în adresă; se aleg cele mai lungi nume; mai multe segmente OSM cu același nume se tratează ca o singură stradă. Distanța la stradă = la segmente, nu la vârfuri.
- `calitate` de bază 0,9; `* factor_ambiguitate` (primele două opriri candidate diferă cu mai puțin de `prag_ambiguitate_min`); `* factor_fara_strada` (adresă fără stradă potrivită sau nicio oprire la `distanta_strada_m` de ea). Ambiguitatea se aplică și pe fallback.
- `element_id` = cel mai apropiat element (noduri + post) la cel mult `raza_oprire_m`, altfel null. `vizitate` = opriri lângă elemente existente (toate opririle, nu doar cele de pe stradă).
- Strada potrivită, dar fără oprire la 40 m: fallback pe cea mai lungă oprire, cu `factor_fara_strada`, `strada` rămâne null.

## Limite
GPS simulat, necalibrat. Potrivire doar pe nume de stradă (fără număr, fără fuzzy). Ordinea de străzi cu același nume în orașe diferite nu e tratată. `calitate` de bază 0,9 e o alegere de prototip, nu e în `weights.yaml`. Pragul de 15 m din spec (oprire câștigătoare vs. element) nu e folosit aici: se folosește `raza_oprire_m` (12 m).

## Pentru ceilalți
- B (B7): apelează `localizeaza` la potrivire când raportul nu are ID/coordonate; `alegere.element_id` null înseamnă stâlp nou prezis la `alegere.{lat,lon}`; `vizitate` dau confirmări.
- C: `GET /trasee-demo` poate servi direct `data/reports/trasee-dummy.json`.
