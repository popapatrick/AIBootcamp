# Tasks

## 1. Contract (B, commit `contract:`)

- [x] 1.1 `detalii.trace` și `detalii.trace_rezumat` în `event.schema.json` și `interfaces.md`
- [x] 1.2 Secțiune `trace` în `weights.yaml` (fereastra 60 min, rază oprire 12 m, durată minimă 3 min, distanța la stradă 40 m, prag ambiguitate)

## 2. Modul `backend/trace/` (A)

- [x] 2.1 (A3) `backend/trace/`: `gaseste_opriri` și `localizeaza` (opriri, potrivire cu strada OSM, alegerea locului, ambiguitate)
- [x] 2.2 (A3) `smoke_trace.py` (opriri, stradă, ambiguitate, fallback) și README în folder

## 2b. Integrare în motor (B)

- [x] 2b.1 (B7) Apelează `backend/trace` din potrivire ca „coordonate din trace", semnal în jurnal
- [x] 2b.2 (B7) Confirmări pentru opririle de lângă stâlpi existenți; completare `smoke_engine.py`

## 3. Date (A, A5)

- [x] 3.1 `data/reports/trasee-dummy.json`: cel puțin 3 trasee, între care „verificat stâlpi existenți și oprit unde nu era stâlp"
- [ ] 3.2 Rapoarte de tabletă asociate (adresă vagă) în `exemple-dummy.json`
- [x] 3.3 `docs/etapa-16-trasee-dummy.md`

## 4. API și UI (C)

- [ ] 4.1 `POST /rapoarte` acceptă `trace`; `GET /trasee-demo` returnează traseele gata făcute
- [ ] 4.2 Prompt Lovable: buton „Generează traseu ultima oră", editare cu clic pe hartă, afișare opriri și traseu
- [ ] 4.3 Verificare cap-coadă pe preview

## 5. Documentație

- [x] 5.1 `docs/etapa-17-locatie-din-trace.md` (B): limite (GPS simulat, necalibrat)
