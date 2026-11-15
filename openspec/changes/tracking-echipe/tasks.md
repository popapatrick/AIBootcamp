# Tasks

## 1. Contract (B, `contract:`, Faza 0)

- [x] 1.1 `event.schema.json` (`tracking_tura`, `detalii.tura`, `detalii.tracking`), `state.schema.json` (`oprire_tracking`, `ultima_validare_tracking`), `weights.yaml` + limite + relații (`tracking`, `fiabilitate_sursa.tracking_gps`), `api.openapi.yaml` (3 endpointuri), `interfaces.md`

## 2. Generator și motor (B, Faza 1)

- [x] 2.1 (B1) `backend/tracking/genereaza_tura` + `smoke_tracking.py`
- [x] 2.2 (B2) `backend/engine/tracking.py`: ramura `tracking_tura` (validare, stâlp presupus, opriri scurte), pași StepTrace, teste
- [ ] 2.3 (B3) 2 ture în scenariu (`data/events/ture-tracking.json`, `genereaza_scenariu.py`), distribuția în țintă
- [ ] 2.4 `docs/etapa-32-tracking-echipe.md`, README-uri

## 3. API (C, Faza 2)

- [ ] 3.1 `POST /tracking/genereaza`, `POST /tracking/aplica` (cu `tracking[]` pe opriri și `t_ajungere`), `GET /tracking/ture`; teste în `smoke_api.py`; `docs/etapa-33-api-tracking.md`

## 4. UI (C, Faza 3)

- [ ] 4.1 Prompt Lovable P4 „Tracking echipe” (netrimis până decide Victor): tab, generare, animație, rezultate pe opriri, rezumat, accesibilitate
- [ ] 4.2 Verificare prin tunel, capturi pe board

## 5. Demo (B + C, Faza 4)

- [ ] 5.1 Pas nou în `docs/DEMO.md`; `verifica_tot.sh` TOT VERDE
