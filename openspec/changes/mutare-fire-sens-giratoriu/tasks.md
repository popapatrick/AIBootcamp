# Tasks

## 1. Contract (B, commit `contract:`)

- [x] 1.1 Adaugă `mutare_fire` în `tip` și `detalii` (`centru`, `raza_m`, `motiv`) în `contracts/event.schema.json` și `interfaces.md`
- [x] 1.2 Adaugă `potrivire.raza_mutare_m` și plafonul de elemente în `contracts/weights.yaml`
- [x] 1.3 Anunță în `board/Victor.md`

## 2. Extragere (A)

- [x] 2.1 Prompt și exemple pentru `mutare_fire`, centrul din coordonatele din text
- [x] 2.2 2-3 texte dummy cu sens giratoriu în `data/reports/exemple-dummy.json`
- [x] 2.3 `docs/etapa-13-mutare-fire.md`

## 3. Motor (B)

- [x] 3.1 Regula de zonă în `model.py`: semnal negativ pe elementele din rază, plafon, jurnal
- [x] 3.2 Propunere de traseu pe străzi pentru legăturile afectate (`osm.py`)
- [x] 3.3 Teste în `smoke_engine.py` și `smoke_osm.py`

## 4. API și UI (C)

- [ ] 4.1 API acceptă `centru` din clic pe hartă în `POST /rapoarte`
- [ ] 4.2 Prompt Lovable: buton „Fire mutate", text, clic pe hartă pentru locație, afișare zonă și traseu punctat
- [ ] 4.3 Verificare pe preview

## 5. Documentație

- [ ] 5.1 Pas nou în `docs/DEMO.md` (B)
