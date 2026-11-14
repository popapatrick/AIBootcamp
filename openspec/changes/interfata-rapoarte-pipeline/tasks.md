# Tasks

## 1. Contract (B, commit `contract:`)

- [x] 1.1 Adaugă `schimbari[]` în răspunsul `POST /rapoarte` și `ultima_actualizare` în `statistici` (`contracts/interfaces.md`, `contracts/api.openapi.yaml`)
- [x] 1.2 Anunță în `board/Victor.md` cu `@Patrick @Claudiu`

## 2. Motor (B)

- [x] 2.1 `apply_event` întoarce `schimbari` structurate (ce, scor înainte/după, de ce)
- [x] 2.2 `statistici()` întoarce `ultima_actualizare`
- [x] 2.3 Teste în `smoke_engine.py` pentru `schimbari` și `ultima_actualizare`

## 3. Extragere și date (A)

- [x] 3.1 `data/reports/exemple-dummy.json`: câte 4 texte messy pe sursă (racordări, investiții, mentenanță, apel call center), inclusiv cazuri cu stâlp inexistent
- [ ] 3.2 Verifică `extract_event` pe textele de call center (surse `apel_client`)
- [x] 3.3 `docs/etapa-10-exemple-dummy.md`

## 4. API (C)

- [x] 4.1 `POST /rapoarte` returnează `schimbari`; `GET /exemple?sursa=` returnează textele dummy
- [x] 4.2 Test în `smoke_api.py`

## 5. UI Lovable (C)

- [ ] 5.1 Ecran cu 4 butoane de sursă, câmp text, „Generează exemplu"
- [ ] 5.2 „Show pipeline" cu pași și schimbări; data ultimei actualizări
- [ ] 5.3 Traseu punctat pe străzi pentru stâlp inexistent
- [ ] 5.4 Verificare cap-coadă pe preview cu API-ul real

## 6. Documentație

- [x] 6.1 `docs/etapa-11-interfata-rapoarte.md` (C), completări în `docs/DEMO.md` (B)
