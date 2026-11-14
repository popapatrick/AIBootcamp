# Tasks

## 1. Contract (B, commit `contract:`, pasul 0)

- [x] 1.1 `detalii.trace_params`, `detalii.trace_sursa` în `event.schema.json` și `interfaces.md`; semnătura `backend.trace.genereaza_traseu(punct, strazi, params, seed)`
- [x] 1.2 Secțiunea `trace_generat` în `weights.yaml` (puncte, zgomot, durată, acoperire, decalaj, bonus_max, acoperire_min, toleranta_adresa_m)

## 2. Generator (A)

- [x] 2.1 (A3) `backend/trace/genereaza.py`: `genereaza_traseu`, determinist pe seed, cu parametri
- [x] 2.2 (A3) `smoke_trace.py`: oprirea generată e redescoperită de `localizeaza`; cazuri cu zgomot mare, acoperire mică, decalaj; README

## 3. Motor (B)

- [x] 3.1 (B4) La procesarea raportului cu locație și fără trace, apelează generatorul; `localizeaza` pe rezultat; `factor_trace` în calitatea locației; jurnal
- [x] 3.2 (B4) Teste în `smoke_engine.py`: bonus, penalizare, contradicție, fără trace

## 4. API (C)

- [x] 4.1 (C1) `trace_params` în `POST /rapoarte`, `trace_sursa` și opririle în răspuns; teste în `smoke_api.py` (API pass-through; complet după B4)

## 5. Documentație

- [x] 5.1 `docs/etapa-19-traseu-generat.md`, README `backend/trace`, `interfaces.md`, `DEMO.md`, board
