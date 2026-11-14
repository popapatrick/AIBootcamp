# Tasks

## 1. Contract (B, commit `contract:`)

- [x] 1.1 Adaugă `activ_demontat` în `tip` din `contracts/event.schema.json` și în `interfaces.md`
- [x] 1.2 Adaugă în `contracts/weights.yaml` pragurile pentru valul de apeluri (număr, fereastră, plafon)
- [x] 1.3 Anunță în `board/Victor.md`

## 2. Date (A)

- [x] 2.1 `data/events/events.extreme.json`: ramură pe etape (3-4 evenimente), segment demontat (2 rapoarte), val de apeluri (3+), peste setul existent
- [x] 2.2 Rapoartele text aferente în `data/reports/` și intrări în `index.json`
- [x] 2.3 Validează toate evenimentele cu `event.schema.json`
- [x] 2.4 `docs/etapa-12-scenariu-extrem.md`

## 3. Motor (B)

- [x] 3.1 Regula `activ_demontat` în `model.py` (neaplicat sub prag, jurnal cu „de ce")
- [x] 3.2 Semnal agregat pentru val de apeluri
- [x] 3.3 Încărcare scenariu: `engine.get_model()` acceptă sursa `extreme`; teste în `smoke_engine.py`
- [x] 3.4 Recalibrare și rezultat în `docs/calibrare.md`

## 4. API și UI (C)

- [x] 4.1 Endpoint de selecție scenariu (`/evenimente?scenariu=extrem` sau echivalent) și test în `smoke_api.py`
- [ ] 4.2 Prompt Lovable: buton „Încarcă rețeaua cu evenimente", Play, halou verde și galben
- [ ] 4.3 Verificare timeline sub 45 s pe preview

## 5. Documentație

- [x] 5.1 Pași noi în `docs/DEMO.md` (B)
