# Tasks

Toate sarcinile le face C (Claudiu) la cererea omului, inclusiv cele din folderele lui A și B (excepție, ca la commit 31b0847).

## 1. Contract (C, commit `contract:`)

- [ ] 1.1 `GET /locatie-operator-demo` și `locatie_operator` în `POST /rapoarte` în `api.openapi.yaml`; `sursa_locatie` și `detalii.locatie_operator` în `interfaces.md`
- [ ] 1.2 `racordare.factor_locatie_operator`, `operator_precizie_m`, `operator_distanta_min_m` în `weights.yaml`

## 2. Modul `backend/racordare/` (rol A, făcut de C)

- [ ] 2.1 `locatie_operator_demo(adresa, net, strazi, cfg, ...)`: funcție pură, determinist, cu docstring
- [ ] 2.2 Teste în `smoke_racordare.py` și README

## 3. Motor (rol B, făcut de C)

- [ ] 3.1 `_cerere_racordare`: folosește `detalii.locatie_operator`, factor de scor, nivel maxim predicție, jurnal „de ce", `sursa_locatie` în pași
- [ ] 3.2 Teste în `smoke_sesiune2.py` (scor operator < scor clic)

## 4. API (C)

- [ ] 4.1 Endpoint `GET /locatie-operator-demo` (200 / 422)
- [ ] 4.2 `POST /rapoarte` acceptă `locatie_operator`; regex „Cerere racordare: ..." fără coordonate
- [ ] 4.3 Teste în `smoke_api.py`
- [ ] 4.4 Prompt Lovable: buton „Folosește locația operatorului (simulată)" (la cererea omului, separat)

## 5. Documentație

- [ ] 5.1 `docs/etapa-17-locatie-operator-racordare.md`, `docs/DEMO.md`, `docs/demo-checklist-C.md`, board
