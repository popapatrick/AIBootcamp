# Tasks

## 1. Contract (B, commit `contract:`, pasul 0)

- [x] 1.1 `zona.raza_max_m: 3000` în `weights.yaml`; `eronat_prototip` în StepTrace și semnalul `in_afara_zonei_prototip` în `interfaces.md`; zona (centru, rază) în `/stare` în `api.openapi.yaml`

## 2. Motor (B)

- [x] 2.1 (B1) `backend/engine/zona.py`: centroid, `zona_ok`; înlocuiește bbox +500 m din `match.py`
- [ ] 2.2 (B1) Aplicat în potrivire, mutare_fire, cerere_racordare, trace; stâlpi prezicși tăiați la zonă
- [x] 2.3 (B1) Teste în `smoke_engine.py` și `smoke_sesiune2.py` (40 km, 3,1 km, 2,9 km, om_teren, apel)

## 3. Folderele lui A

- [ ] 3.1 (A1, A3) `backend/geo` și `backend/trace` importă `zona_ok`, întorc `in_afara_zonei`; teste în smoke-urile lor

## 4. API (C)

- [x] 4.1 (C1) `zona` în `/stare`, `eronat_prototip` în răspuns, teste în `smoke_api.py` (API pass-through; complet după B1)

## 5. Documentație

- [ ] 5.1 `docs/etapa-20-safeguard-zona.md`, `interfaces.md`, `DEMO.md`, board
