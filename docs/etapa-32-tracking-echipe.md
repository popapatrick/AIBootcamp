# Etapa 32: tracking echipe

Plan: `docs/plan-tracking-echipe.md`. OpenSpec: `openspec/changes/tracking-echipe/`. Date FICTIVE.

## Contract (Faza 0)
- `event.schema.json`: tip `tracking_tura`; `tip_sursa_pondere: tracking_gps`; `detalii.tura {tura_id, seed, echipa, puncte[{t, lat, lon}]}`; `detalii.tracking` (scris de motor).
- `state.schema.json`: `predictie.metoda: oprire_tracking`; `ultima_validare_tracking` (dată sau null).
- `weights.yaml`/`weights.limits.yaml`: `fiabilitate_sursa.tracking_gps` 0,60 și secțiunea `tracking` (valorile din plan 2.3). Relații verificate de `verifica_reglaje`: `durata_validare_min < durata_stalp_nou_min`, `raza_validare_m < raza_fara_stalp_m` (strict, lista `rel`) și `stalpi_min <= stalpi_max` (listă nouă `rel_le`, cu `<=`).
- `api.openapi.yaml`: `POST /tracking/genereaza`, `POST /tracking/aplica`, `GET /tracking/ture`. `interfaces.md`: secțiunea „Sesiunea 4b”.
- Verificare: `EXTRACT_CLI=0 .venv/bin/python -m backend.engine.verifica_reglaje --rapid` (fără erori, nicio „cheie nouă fără limite”) și `openspec validate --all`.

## Generator (B1)
**Ce face.** `backend.tracking.genereaza_tura(net, strazi, cfg, echipa, seed, data, scoruri=None, ora_start="08:00:00")` alege 3–5 stâlpi existenți (preferând cei care nu sunt verzi, dacă primește `scoruri`) și un loc fără stâlp pe o stradă, îi ordonează „cel mai apropiat următor” de la un capăt, îi leagă pe străzi OSM (`osm.traseu`), apoi emite puncte GPS la `tracking.pas_s` secunde (viteza `viteza_m_s`, zgomot gaussian `zgomot_m`). Opriri: stâlp 6–10 min la 3–8 m de stâlp; loc fără stâlp 15 min; 1–2 opriri scurte de 1–2 min pe drum.

**Verificare.** `.venv/bin/python -m backend.tracking.smoke_tracking` => `OK: 140 verificări` (cod 0). Acoperă: determinism, 3 echipe, seed diferit, preferința pentru stâlpi nu-verzi, toate punctele în zona de 3 km, fiecare oprire din `plan` regăsită de `gaseste_opriri` cu durată la ±1 min și nicio oprire în plus, opririle scurte sub `durata_validare_min` și nedetectate, locul fără stâlp la >= `raza_fara_stalp_m` de orice nod, puncte de mers fără zgomot la <= 20 m de stradă.

**Intrări.** `net` (rețeaua cu SIM-*), `strazi` (cache OSM), `cfg` (weights), `echipa` (mentenanta|investitii|racordari), `seed`, `data`, opțional `scoruri` {id: scor} și `ora_start`.
**Ieșire.** `{tura_id, echipa, data, seed, puncte[{t, lat, lon}], plan[{lat, lon, durata_min, tip_plan: stalp|fara_stalp|scurta, element_id?}], lungime_m, durata_min, linie_dreapta}`. `tura_id` = `TURA-<echipa>-<data>-<hash8>`. `plan` = doar depanare și teste.

**Decizii.**
- Determinism: `random.Random` seminat din sha256 al (echipă, dată, seed); zgomotul are un flux separat de alegeri.
- Stâlpii sunt aleși într-o zonă restrânsă în jurul unui stâlp-ancoră (rază 500 m, apoi 800/1300/3000), la >= 60 m unul de altul (altfel `gaseste_opriri` le-ar putea lipi), la >= 100 m în interiorul zonei de 3 km (zgomotul nu o depășește).
- Contractul cere stâlpi la <= 40 m de stradă; intern se preferă <= 25 m (mersul rămâne aproape de stradă), cu 40 m ca rezervă.
- În opriri zgomotul e plafonat la 0,4 × `trace.raza_oprire_m` (ca generatorul vechi), deci opririle rămân detectabile.
- Fără drum pe străzi, linie dreaptă, numărată în `linie_dreapta`; se reîncearcă alte alegeri (până la 8) înainte să se accepte o tură cu linie dreaptă.

**Limite.** O tură are ~190–350 de puncte și 47–88 min (mai mult decât cei ~200 de puncte din plan; scade cu `pas_s` mai mare sau cu mai puțini stâlpi). Opririle scurte (1–2 min) sunt sub `trace.durata_min_min` (3 min), deci `gaseste_opriri` nu le vede; motorul trebuie să le trateze doar dacă detectorul le raportează (altfel nu apar în `tracking[]`). Fără cache OSM generatorul ridică `ValueError`. Zgomotul mare (> `trace.raza_oprire_m`) poate pierde opriri, ca la generatorul vechi.

## Motor (B2)
Urmează: `backend/engine/tracking.py` (ramura `tracking_tura`), teste, scenariul (B3).
