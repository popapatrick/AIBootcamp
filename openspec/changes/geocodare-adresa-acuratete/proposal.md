# Proposal

## Why

Standardizarea cu AI înțelege azi doar texte foarte apropiate de formatul standard: ID-uri de stâlp, coordonate, coduri de racord. Un raport care dă doar o adresă sau o stradă ajunge `nepotrivit`, fără locație. Oamenii scriu adrese, nu coordonate. Sistemul trebuie să scoată din adresă și stradă coordonate geografice aproximative și să calculeze acuratețea după cât de aproape e textul de formatul standard.

## What Changes

- Modul nou `backend/geo/` (rol A): `geocodeaza(referinta, strazi, cfg)` întoarce `{lat, lon, precizie_m, metoda, acuratete, motiv}` din adresă, stradă, intersecție sau reper. Folosește DOAR cache-ul OSM local (străzile zonei modelului), cu AI (Haiku din abonament, `cli_ai`) pentru adrese ortografiate diferit sau vagi („lângă școală", „pe la intersecția cu..."). Fără apel de rețea spre servicii de geocodare, fără cheie.
- Extracția scoate și `referinta.adresa_structurata {strada, numar, localitate, reper}`, nu doar textul adresei.
- Acuratețea locației se calculează pe nivel de standardizare: ID existent > coordonate explicite > stradă + număr > intersecție > doar stradă > doar reper. Valorile stau în `weights.yaml`, nu în cod.
- Potrivirea (pasul 3, „doar adresă") nu mai întoarce `nepotrivit`: apelează geocodarea și folosește rezultatul ca „coordonate din adresă", cu calitatea din tabel.
- Incredere de extracție plafonată după cât de standardizat e textul (plafon pe cel mai bun localizator din text).

## Capabilities

### New Capabilities
- `geocodare-adresa`: coordonate aproximative și acuratețe pornind de la adresă/stradă, în zona modelului.

### Modified Capabilities

## Impact

- Contract (`contract:`, B): `referinta.adresa_structurata`, `detalii.geocodare`, secțiunea `geocodare` și `standardizare` în `weights.yaml`.
- A: `backend/geo/` (nou), `backend/extract` (prompt), date de test cu adrese și coordonate așteptate.
- B: `backend/engine/match.py` (pasul 3), scor, jurnal „de ce".
- C: câmpurile noi în API și pasul „geocodare" în Show pipeline.
- În afara scopului: acoperire națională (necesită serviciu extern; rămâne ca extindere dezactivată, vezi design), geocodarea numărului exact al casei (se interpolează doar, cu acuratețe mică).
