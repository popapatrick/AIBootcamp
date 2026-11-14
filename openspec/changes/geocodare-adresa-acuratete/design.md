# Design

## Context

Zona modelului are ~77 de străzi în cache-ul OSM local (`osm.strazi()`, 30 cu nume). Potrivirea merge pe ID, apoi coordonate, apoi adresă; adresa dă azi `nepotrivit`. Regula de proiect: standardizarea e cu AI, fără cheie API (ai_cache -> ai_cli -> ai_api -> regex ca ultimă rezervă).

## Goals / Non-Goals

**Goals:** coordonate aproximative din adresă în zona modelului; acuratețe care scade vizibil cu vagul textului; explicație în „De ce?".
**Non-Goals:** geocodare națională (decis de Victor: doar cache OSM local + AI); număr exact de casă; apeluri de rețea la servicii externe.

## Decisions

- Ordinea în `geocodeaza`: (1) potrivire deterministă a numelui străzii normalizat (fără diacritice, fără „Str."/„Strada") pe `osm.strazi()`; (2) intersecție dacă sunt două străzi; (3) dacă nu e potrivire sigură, AI (Haiku prin `cli_ai.call_cli`, cache pe text) primește lista de străzi candidate și alege una sau spune „necunoscută"; AI nu inventează coordonate, alege dintre străzile din cache. Rezultatul AI primește `factor_ai_fuzzy`.
- Locul pe stradă: fără număr = mijlocul străzii, precizie ~ jumătate din lungime (min/max din config); cu număr = interpolare între capete (par/impar nu se distinge în prototip), precizie mai mică; intersecție = punctul comun.
- Acuratețea e un număr 0-1 din tabel `geocodare.acuratete` (`stradă_număr`, `intersectie`, `strada`, `reper`) × `factor_ai_fuzzy` dacă a decis AI. Intră în calitatea potrivirii, deci în scorul propunerii, la fel ca orice alt input.
- `standardizare.plafon_dupa_localizator` limitează `incredere_extractie` (id 1.0, coordonate 0.9, stradă+număr 0.7, stradă 0.5, reper 0.3). Textul foarte apropiat de formatul standard, ca exemplele generate la rapoarte, primește acuratețe mare; textul vag, mică.
- Dacă geocodarea dă un punct în afara zonei prototipului, rezultatul e marcat `in_afara_zonei` (vezi `safeguard-zona-prototip`), nu se ascunde.
- Extindere națională, dezactivată: ar necesita un serviciu extern (Nominatim). Nu se implementează acum; interfața `geocodeaza` e făcută astfel încât să se poată adăuga ca metodă `nominatim`, oprită implicit.

## Risks / Trade-offs

- Cu doar 30 de străzi cu nume, multe adrese reale nu se potrivesc; atunci rezultatul e „necunoscut", nu inventat.
- Tabelul de acuratețe e necalibrat pe date reale; calibrare pe setul de test cu adrese (A) și raport în `docs/calibrare.md`.
