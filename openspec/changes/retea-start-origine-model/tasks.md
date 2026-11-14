# Tasks

## 1. Contract (B, commit `contract:`, pasul 0)

- [x] 1.1 `origine` pe elemente în `state.schema.json`, `predictie.origine`, `interfaces.md`; `scor.initial_retea_start: 0.90` în `weights.yaml`

## 2. Puncte simulate (A)

- [x] 2.1 (A4) `data/simulare/genereaza_puncte.py`: stâlpi și case pe străzi OSM, seed fix, fără suprapuneri, în zonă; ieșire `data/simulare/puncte-simulare.json` hardcodată; README
- [x] 2.2 (A4) Test: toate punctele valide pe schemă, în zonă, la ≥ 2,5 m de existente

## 3. Motor (B)

- [x] 3.1 (B3) `network.py`: încarcă `puncte-simulare.json`, `origine: retea_start` (rămas, după A4); `model.py`: `origine: generat_model` pe tot ce adaugă sistemul; snapshot (făcut)
- [x] 3.2 (B7) Recalibrare cu scor inițial nou; diferența în `docs/calibrare.md`; teste în `smoke_network.py` și `smoke_engine.py`

## 4. API și UI (C)

- [x] 4.1 (C1) `origine` în răspuns și teste în `smoke_api.py` (API pass-through; complet după B3)
- [x] 4.2 (C4) Prompt Lovable (scris, netrimis): „Rețea de start" / „Generat de model", contur punctat, fără „Predicție AI"

## 5. Documentație

- [x] 5.1 `docs/etapa-21-retea-start-origine.md`, `data/simulare/README.md`, `data/model/README.md`, `DEMO.md`, board
