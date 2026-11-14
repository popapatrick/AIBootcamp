# Tasks

Toate sarcinile le face C (Claudiu) la cererea omului, inclusiv cele din folderele lui A și B (excepție, ca la commit 31b0847).

## 1. Contract (C, commit `contract:`)

- [x] 1.1 `GET /locatie-operator-demo` și `locatie_operator` în `POST /rapoarte` în `api.openapi.yaml`; `sursa_locatie` și `detalii.locatie_operator` în `interfaces.md`
- [x] 1.2 `racordare.factor_locatie_operator`, `operator_distanta_min_m` și pragurile de precizie în `weights.yaml`

## 2. Modul `backend/racordare/` (rol A, făcut de C)

- [x] 2.1 `locatie_operator_demo(text, net, strazi, cfg, lat, lon)`: parsare cu reguli simple (stradă, intersecție, cartier, reper), funcție pură, determinist, cu docstring; `osm.strazi()` întoarce și `zona`
- [x] 2.2 Teste în `smoke_racordare.py` și README

## 3. Motor (rol B, făcut de C)

- [x] 3.1 `_cerere_racordare`: folosește `detalii.locatie_operator`, factor de scor, nivel maxim predicție, jurnal „de ce", `sursa_locatie` în pași
- [x] 3.2 Teste în `smoke_sesiune2.py` (scor operator < scor clic)

## 4. API (C)

- [x] 4.1 Endpoint `GET /locatie-operator-demo` (200 / 422)
- [x] 4.2 `POST /rapoarte` acceptă `locatie_operator`; regex „Cerere racordare: ..." fără coordonate
- [x] 4.3 Teste în `smoke_api.py`
- [ ] 4.4 Prompt Lovable: buton „Folosește locația operatorului (simulată)" (la cererea omului, separat)

## 5. Documentație

- [x] 5.1 `docs/etapa-17-locatie-operator-racordare.md`, `docs/DEMO.md`, `docs/demo-checklist-C.md`, board
