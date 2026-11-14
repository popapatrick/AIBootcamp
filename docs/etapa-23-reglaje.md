# Etapa 23: ghid de reglaje fără cod (C5)

Metoda din `docs/plan-sesiune-3-logica.md`, secțiunea 9. Un reglaj = schimbarea unui număr în `contracts/weights.yaml`, fără alt cod. Orice laptop poate face asta, inclusiv C.

B6 e pe main (tag `logic-v1`): `backend/engine/verifica_reglaje.py`, `contracts/weights.limits.yaml`, `scripts/verifica_tot.sh`, regula `reglaj:` în CLAUDE.md și șablonul `docs/cerere-logica.md`. `verifica_reglaje` arată ce valori ai schimbat față de HEAD, ce evenimente de calibrare își schimbă decizia sau scorul, rulează toate smoke-urile și tipărește linia pentru board.

## Pași
1. `git pull --rebase origin main`. Citește `board/*.md`.
2. Vezi valoarea curentă: `curl -s localhost:8000/reguli` sau deschide `contracts/weights.yaml`.
3. Rulează bancul **înainte**, salvează rezultatul: `python3 -m backend.api.banc_logica --json > /tmp/inainte.json` (scratch, nu în repo). Pe fallback (fără `data/golden/`) comparația e orientativă.
4. Schimbă DOAR valoarea în `contracts/weights.yaml` (nu cheia, nu structura).
5. `python3 -m backend.engine.verifica_reglaje`: verifică valoarea față de `weights.limits.yaml` și tipărește o linie rezumat. Dacă ieși din limite, reglajul nu se împinge.
6. Rulează din nou bancul și compară cu pasul 3: `python3 -m backend.api.banc_logica --doar-diferente`. Rulează și smoke-urile (`python3 -m backend.engine.smoke_engine`, `.venv/bin/python -m backend.api.smoke_api`; `bash scripts/verifica_tot.sh` le face pe toate și se termină cu `TOT VERDE`).
7. Lipește linia de la `verifica_reglaje` și efectul din banc (ce cazuri au schimbat decizia/scorul) în `board/<laptop>.md`.
8. Commit doar cu `contracts/weights.yaml`: `reglaj: <cheia> a -> b, motiv` (ex. `reglaj: zona.raza_max_m 3000 -> 2500, demo mai strâns`). Push pe `main`; dacă e respins, `git pull --rebase origin main`, niciodată `--force`.

## Reguli
- Doar valori numerice. Orice altceva (logică nouă, cheie nouă, regulă) = **cerere de logică**: scrie în `board/<laptop>.md` cu `@Victor` după `docs/cerere-logica.md` (ce vrei, intrare exemplu, ieșire așteptată, de ce).
- Prompturile AI le schimbă doar A (invalidează cache-ul).
- Ponderile se aplică întregului sistem: un reglaj schimbă toate inputurile și predicțiile, nu doar cazul care te interesează. De aceea se verifică pe tot bancul.
- Reglajul care rupe limite sau smoke-uri nu se împinge.
- După tag `logic-v1` (B7), schimbările de cod în motor trec prin cerere aprobată; reglajele de valori rămân permise.

## Limite
- Bancul nu are încă `data/golden/` (A6): efectul unui reglaj se vede doar pe cele 29 de cazuri din `exemple-dummy.json`, dintre care 7 diferă deja de `asteptat` (vezi `docs/etapa-24-api-sesiune3.md`).
- `GET /reguli` arată valorile din fișier pe disc la fiecare apel; motorul poate ține valorile vechi în memorie până la repornirea serverului.

## După `logic-v1`
Verificat: `python3 -m backend.engine.verifica_reglaje` tipărește valorile schimbate față de HEAD, diferența de calibrare față de `data/golden/calibrare-referinta.json`, smoke-urile (toate OK) și linia `reglaj: (nimic) | calibrare: N evenimente schimbate | smoke: toate OK` pentru board. După tag, schimbările de cod în motor merg doar printr-o cerere de logică aprobată (`docs/cerere-logica.md`); reglajele numerice rămân în limitele din `contracts/weights.limits.yaml`.
