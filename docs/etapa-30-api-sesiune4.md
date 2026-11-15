# Etapa 30: API sesiunea 4 (C1, C2, C3, C5; C6 parțial)

Date FICTIVE. Cod: `backend/api/` (`main.py`, `pipeline.py`, `sources.py`, `prezentare.py` nou, `banc_logica.py`, `smoke_api.py`).

## Ce face
- **C1, curățenie:** scos `?scenariu=extrem` (din `/retea`, `/evenimente`), `GET /trasee-demo`, `trace_params` și `trace` din `POST /rapoarte` (+ `TraceParams`), `model_extrem`/`ScenariuLipsa` din `sources.py`. `GET /exemple?sursa=` acceptă doar `mentenanta|investitii|racordari` (`apel_client` = 422). `locatie` (clic) și `locatie_operator` rămân (teste). `NOTA` din `/health` rămâne.
- **C2, endpointuri noi:**
  - `POST /element/{id}/verificare` `{motiv?, data?}`: Event `verificare_om` (`om_teren`, `detalii.tinta_id`) prin `apply_event`. 404 dacă elementul nu există. **501 „verificare_om nu e încă în motor (V5, Victor)”** cât timp codul din `backend/engine/*.py` nu conține `verificare_om` (verificare automată în `pipeline._motorul_stie_verificare_om`); după V5 răspunde 200 cu StepTrace, fără alt cod în API.
  - `GET /demo/exemple`: conținutul `data/reports/demo-intro.json`; `[]` dacă lipsește (îl scrie C4).
  - `POST /demo/reset`: `engine.reset()` + șterge rapoartele live; `{status: ok, evenimente: N}`.
  - `GET /legenda`: `{benzi[{banda, de_la, pana_la, culoare, text}], linii[{stil, text}], insigne[{cod, text}]}`; pragurile din `weights.culori`, culorile hex alese în `prezentare.py`.
- **C3, câmpuri noi** (construite în `prezentare.py`, etichete în română în API):
  - `POST /rapoarte`: `standardizare {metoda, metoda_eticheta, campuri[{camp, valoare, eticheta, din: text|dedus|lipsa}], lipsa[], localizare{sursa, precizie_m, plafon, metoda, indiciu, text} | null, decizie{cod, text, scor, banda}}` și `focus {lat, lon, zoom, bbox{lat_min, lon_min, lat_max, lon_max}} | null`. `metoda_eticheta`: „AI (live)” (`ai_cli`/`ai_api`), „AI (cache)”, „Regex (simplificat)”.
  - `focus`: bbox-ul elementelor din `schimbari` + 30 m; altfel punctul geocodat/din text; zoom 17 (16 la `mutare_fire`). Pozițiile vin din instantaneul cel mai recent.
  - `GET /retea` (pe fiecare feature): `banda`, `verificat_om`, `sursa_locatie`, `t0` (null dacă motorul nu le dă, altfel neatinse), `eticheta_origine` („GIS” pentru `retea_start`, „Din raport” pentru `generat_model`, altfel null).
  - `GET /evenimente`: `text_original`, `echipa` (Mentenanță/Investiții/Racordări/Apel client/Om din teren), `standardizare`, `focus`, `banda_inainte`, `banda_dupa`. Valorile date deja de motor rămân neatinse (`setdefault`).
- **C5, banc:** coloane noi `banda`, `sursa_locatie`, `verificat_om`, `lungime_m` (din `analiza_harta.ales.lungime_m`, null-safe); pot apărea și în `asteptat`.

## Verificare
```
.venv/bin/python -m backend.api.smoke_api      # ultima linie: OK: API
scripts/verifica_tot.sh                         # ultima linie: TOT VERDE
EXTRACT_CLI=0 .venv/bin/python -m backend.api.banc_logica   # Sumar: 20 cazuri, 20 ok, 0 diferite
```
Smoke-ul acoperă: `/trasee-demo` 404, `apel_client` 422 la `/exemple`, `standardizare`/`focus` pe un raport cu coordonate, câmpurile noi din `/retea` și `/evenimente`, `/legenda`, `/demo/exemple`, 404/501(200 după V5) la verificare, `/demo/reset`.

## Ce așteaptă motorul (null acum)
`banda`, `verificat_om`, `sursa_locatie`, `t0` în `/retea`; `banda`/`banda_inainte`/`banda_dupa` în `standardizare.decizie` și timeline (se citesc din `modificari[0].banda`, `schimbari[0].banda_inainte|banda_dupa`); `eticheta_origine` apare când motorul pune `origine`; `localizare` din pasul `cautare_strada` (V6) e scrisă după formatul contractului, netestată pe date reale; `/element/{id}/verificare` (V5).

## Decizii și limite
- API-ul nu calculează `banda` din scor: o afișează cum o dă motorul (D5).
- `standardizare.metoda` e null pe intrările din timeline ale scenariului (evenimentele vin din fișier, metoda de extracție nu e păstrată); pe rapoartele live e completă.
- `focus` din instantaneul cel mai recent: un element mutat ulterior apare la poziția nouă.
- `echipa`/`text_original` din `events.json` via `engine._incarca_evenimente()` (funcție privată a motorului).

## Pentru ceilalți
- Victor (V1/V5/V6): când pui `banda`, `verificat_om`, `sursa_locatie`, `schimbari[].banda_*`, `modificari[].sursa_locatie`, API-ul le trece neatinse. `frontend/plan-b/` (Leaflet) poate folosi încă `/trasee-demo`/`?scenariu=extrem`: de verificat (nu e folderul meu).
- Lovable: textele și etichetele vin gata din API; fără coduri brute.
