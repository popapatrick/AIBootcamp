# Etapa 35: API tracking echipe + ștergere de către om (C)

Date FICTIVE. Motorul e al lui B (`docs/etapa-32-tracking-echipe.md`, `docs/etapa-34-stergere-om.md`); aici doar API-ul și prezentarea.

## Ce face
- `POST /tracking/genereaza {echipa, seed?, data?}`: `backend.tracking.genereaza_tura` cu rețeaua și scorurile curente ale modelului (stâlpii nu-verzi sunt preferați). NU schimbă modelul. Tura se ține în memorie. `seed` implicit `<echipa>-<data>`, `data` implicită azi. Răspuns: tura (`tura_id`, `echipa`, `echipa_eticheta`, `data`, `seed`, `puncte[{t, lat, lon}]`, `plan[]` doar pentru depanare, `lungime_m`, `durata_min`). 422 la echipă necunoscută / dată invalidă / tură imposibilă.
- `GET /tracking/ture`: turele din sesiune și din scenariu (`EV4-T01/T02`), fără puncte: `{tura_id, echipa, echipa_eticheta, data, seed, aplicata, durata_min, lungime_m, n_puncte}`.
- `POST /tracking/aplica {tura_id | tura, data?}`: `engine.apply_event({tip: "tracking_tura", echipa_sursa, tip_sursa_pondere: "tracking_gps", data, detalii: {tura}})`. Răspuns = StepTrace + `tracking[]` + `focus`. 404 `tura_id` necunoscut, 422 fără `tura_id` și `tura`, 501 fără motor. A doua aplicare = `decizie: fara_efect`.
  - `tracking[]` = opririle motorului, cu `t_ajungere` în SECUNDE de la primul punct al turei (motorul dă ISO; API-ul îl convertește) și `eticheta` română (`Stâlp confirmat`, `Stâlp presupus`, `Oprire scurtă`, `Oprire neclară`). Câmpuri: `lat, lon, inceput, sfarsit, durata_min, tip (validare|stalp_presupus|scurta|neclara), motiv, element_id?, distanta_m?, scor_inainte?, banda_inainte?, scor_dupa?, banda_dupa?, calitate?, scor_propunere?, legatura_id?`.
  - `focus` = bbox-ul punctelor turei (+30 m), zoom 16.
- `POST /element/{id}/stergere {motiv?, data?}`: `engine.apply_event({tip: "stergere_om", echipa_sursa: "om_teren", detalii: {tinta_id, motiv}})`. Se șterge tot grupul (`stergere {tinta_id, elemente[], n, motiv}`, `decizie: sters`). 409 `nu_se_sterge_retea_start` (GIS/SIM-*) sau `deja_sters`; 404 `necunoscut`; 501 fără motor. `detail` = `<cod>: <mesaj în română>`.
- `GET /retea`: `stergibil` și `stergere_n` vin din motor (neatinse de API).
- `GET /evenimente`: `eticheta_text` nou, din `prezentare.ETICHETE_TIMELINE` (`tracking` = „Tracking echipă”, `stergere` = „Ștergere”, `verificat_om`, `decizie_om`, ...); `prezentare.DECIZII["sters"]` = „Șters de om”.
- `POST /demo/reset` golește și turele din memorie.

## Verificare
```bash
.venv/bin/python -m backend.api.smoke_api        # ultima linie: OK: API (cu "tracking + ștergere: ok 6 opriri; 2 elemente șterse")
bash scripts/verifica_tot.sh                      # TOT VERDE
EXTRACT_CLI=0 .venv/bin/python -m backend.api.banc_logica   # fără erori (0 erori)
curl -s -X POST localhost:8000/tracking/genereaza -H 'content-type: application/json' -d '{"echipa":"mentenanta","seed":"demo","data":"2026-11-15"}' | jq .tura_id
curl -s -X POST localhost:8000/tracking/aplica -H 'content-type: application/json' -d '{"tura_id":"<tura_id>"}' | jq '.tracking[]|{tip,element_id,t_ajungere}'
```
Testul (`tracking_stergere` în `smoke_api.py`, doar cu motor real) acoperă: generare determinist (același seed = același `tura_id`), listare cu `aplicata`, aplicare cu validări și stâlp presupus, `t_ajungere` crescător, a doua aplicare `fara_efect`, ștergerea unui `TRK-*` (2 elemente, `n` = `stergere_n`), 409 pe SIM-*/GIS și pe deja șters, 404 pe id inexistent, `eticheta_text`, apoi `/demo/reset` (turele dispar).

## Decizii și limite
- Turele sunt în memoria procesului (`pipeline._ture`); repornirea serverului sau `/demo/reset` le pierde (turele scenariului rămân, vin din fișier).
- `tura_id` e determinist (echipă + dată + seed): generarea repetată cu aceiași parametri dă aceeași tură.
- O ștergere refuzată (409/404) e totuși jurnalizată de motor ca „Ștergere neaplicată” și apare în `GET /evenimente` (comportament B); UI-ul nu are de ce să o arate dacă apelează doar pentru `stergibil: true`.
- Un stâlp presupus (`TRK-*`) are `scor_dupa` 0,45; `scor_propunere` e scorul propunerii înainte de plafon (nu se afișează).
- `data` implicită la `/tracking/genereaza` = azi (`date.today()`), la aplicare = data turei.

## Ce trebuie să știe ceilalți
- UI (Lovable): `frontend/lovable-prompt-sesiune4-P4.md`, netrimis până decide Victor.
- B: `t_ajungere` din `tracking[]` e convertit în secunde (contractul spune secunde; motorul dă ISO).
