# Etapa 18: geocodare din adresă și acuratețe după standardizare (A + B, Sesiunea 3)

Date FICTIVE. Feature OpenSpec: `openspec/changes/geocodare-adresa-acuratete/`.

## Ce face
- **A:** `backend/geo.geocodeaza(referinta, strazi, cfg)`: coordonate aproximative din adresă/stradă/intersecție/reper, doar din cache-ul OSM local; AI (`cli_ai`) alege doar dintre numele străzilor din cache. Detalii: `backend/geo/README.md`.
- **B (motor):** `backend/engine/sesiune2.py::_foloseste_geocodare`. Fără ID și fără coordonate, dar cu adresă, motorul apelează `geocodeaza`; coordonatele intră în potrivire ca „coordonate din adresă" (`metoda: adresa`, semnal `coordonate_din_adresa`), cu `calitate = min(calitatea potrivirii, acuratețea geocodării)`. Pasul nou „geocodare" apare în StepTrace, iar `detalii.geocodare` ajunge în eveniment. Stradă necunoscută = fără coordonate inventate (`nepotrivit`). Geocodare în afara zonei = `eronat_prototip` (safeguard).
- **Plafon de standardizare:** `_plafon_standardizare`: `incredere_extractie` nu depășește `standardizare.plafon_dupa_localizator[localizator]` (id 1,0; coordonate 0,9; stradă+număr 0,7; stradă 0,5; reper 0,3). Se vede în pasul „extracție" (`plafon_standardizare`).
- Clicul pe hartă, poziția operatorului și trace-ul au prioritate față de adresă (sunt mai precise).

## Cum se verifică
```bash
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune2   # blocul „geocodare" și „standardizare" (52 verificări)
.venv/bin/python -m backend.geo.smoke_geo
.venv/bin/python -m backend.engine.calibrare                       # decizii neschimbate pe cele 29 de evenimente
```

## Decizii și limite
- Doar zona modelului (cache OSM local); acoperirea națională a rămas în afara scopului (decis de Victor).
- Potrivirea pe un element existent cere tot ≤ 15 m (`potrivire.distanta_max_m`), deci o adresă imprecisă duce de regulă la element nou/predicție, nu la un element existent.
- Pragurile și acuratețele din `weights.yaml` sunt puncte de plecare; calibrarea pe `data/reports/geo-test.json` rămâne la B7.
- Ce trebuie să știe ceilalți: C expune pasul „geocodare" și `detalii.geocodare` în Show pipeline (C1); A păstrează `adresa_structurata` în prompt (A2).
