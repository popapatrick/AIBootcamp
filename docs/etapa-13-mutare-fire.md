# Etapa 13: extracția pentru mutare fire, apel, cerere racordare, decizie om

Date FICTIVE. Rol A.

## Ce face
Promptul `SYSTEM` din `backend/extract/extract.py` acoperă acum:
- `apel_client`: call center, `status: semnalat`, `avarie_semnalata`, `id_client`, locația în `referinta` (revenire curent = `verificare`).
- `mutare_fire`: `detalii.centru {lat, lon}` din coordonatele din text, `raza_m` (doar dacă apare), `motiv_mutare` (ex. `sens_giratoriu`); centru/rază lipsă -> nu se inventează, intră în `campuri_lipsa`.
- `cerere_racordare`: locația casei în `referinta.coordonate`; fără locație -> `coordonate` în `campuri_lipsa`.
- decizie om: `tip: verificare`, `echipa_sursa: om_teren`, `tip_sursa_pondere: om_teren`, `detalii.decizie {tinta_id, decizie, motiv}`.
`extract_event` acceptă sursa `om_teren`; enum-urile din schema curentă acoperă toate valorile (validare existentă).

## Cum se verifică
`.venv/bin/python -m backend.extract.test_extract`: teste cu API mock pentru cele 4 tipuri (ieșiri valide trec, centru incomplet și decizie invalidă dau `ValueError`) și forma `exemple-dummy.json`. Nu face apel real. Texte de probă: `data/reports/exemple-dummy.json`.

## Decizii
- Fără exemple few-shot în prompt (păstrat scurt); regulile sunt explicite pe tip.
- Centrul se copiază în `referinta.coordonate` și în `detalii.centru`, ca motorul să poată folosi oricare.
- Nicio normalizare nouă în cod: schema validează forma, promptul decide conținutul.

## Limite
- Promptul nu a fost rulat pe un model real (fără apel API în această etapă): calitatea extracției pe tipurile noi e neverificată (task interfata 3.2 rămâne deschis).
- Raza implicită e în `contracts/weights.yaml` (`mutare_fire.raza_m`), nu în extracție.

## Pentru ceilalți (Victor, Claudiu)
Schimbarea promptului schimbă cheia de cache (sha256 din MODEL+SYSTEM+...). Rapoartele existente dau cache miss și un apel API nou la următorul `run_all`; `data/events/events.json` rămâne cum e până la reextragere. Nu am șters nimic din `data/cache/`. Dacă UI trimite `centru`/`locatie` din clic, completați direct `detalii.centru`/`referinta.coordonate` în eveniment, fără extracție.
