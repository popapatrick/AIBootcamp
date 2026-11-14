# Tasks

## 1. Contract (B, commit `contract:`, pasul 0)

- [ ] 1.1 `referinta.adresa_structurata` în `event.schema.json`; `detalii.geocodare {lat, lon, precizie_m, metoda, acuratete, motiv}` în `interfaces.md`
- [ ] 1.2 Secțiunile `geocodare` (tabel acuratețe, `factor_ai_fuzzy`, precizii min/max) și `standardizare.plafon_dupa_localizator` în `weights.yaml`; semnătura `backend.geo.geocodeaza(referinta, strazi, cfg)` în `interfaces.md`

## 2. Modul `backend/geo/` (A)

- [x] 2.1 (A1) `geocodeaza`: normalizare nume stradă, potrivire pe `osm.strazi()`, intersecție, interpolare număr, precizie
- [x] 2.2 (A1) Pas AI pentru străzi ortografiate diferit sau vagi, prin `cli_ai.call_cli`, cu cache; AI alege doar dintre străzile din cache
- [x] 2.3 (A1) `smoke_geo.py` (stradă cu număr, ortografie, necunoscut, intersecție, reper) și README în folder
- [x] 2.4 (A2) Prompt de extracție: `adresa_structurata`; texte cu grade diferite de standardizare; setul `data/reports/geo-test.json` cu coordonate așteptate

## 3. Motor (B)

- [ ] 3.1 (B2) `match.py` pasul 3: apelează `backend.geo`, folosește rezultatul ca coordonate din adresă, calitate = acuratețe, semnal în jurnal
- [ ] 3.2 (B2) Plafon `incredere_extractie` după localizator; teste în `smoke_match.py` și `smoke_engine.py`
- [ ] 3.3 (B7) Calibrare pe `geo-test.json`: eroare în metri vs. acuratețe, rezultat în `docs/calibrare.md`

## 4. API (C)

- [ ] 4.1 (C1) `detalii.geocodare` în răspuns și pasul „geocodare" în `trace` (Show pipeline); `GET /geocodeaza?adresa=` de depanare; teste în `smoke_api.py`

## 5. Documentație

- [ ] 5.1 `docs/etapa-18-geocodare-adresa.md`, README `backend/geo`, `interfaces.md`, `DEMO.md`, board
