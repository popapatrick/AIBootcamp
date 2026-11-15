# Tasks

## 1. Contract (B, `contract:`)

- [x] 1.1 `cautare_strada`, `analiza_harta`, `mutare_fire_document` în `weights.yaml` + limite; `adresa_structurata.indiciu`, `detalii.intersectie/strada_noua/latura` în `event.schema.json`; `predictie.traseu/alternative`, metode noi în `state.schema.json`; `interfaces.md`

## 2. Motor și geo (B)

- [x] 2.1 (V6) Prompt: `indiciu`; `geo`: fereastră pe stradă (ancore, convenție, indicii relative); motor: căutarea în fereastră, pas `cautare_strada`
- [x] 2.2 (V3) `analiza_harta.traseu_pe_strazi`, folosit în racordare (înlocuiește treptele 3–4), nod lipsă departe; pas `analiza_harta`
- [ ] 2.3 (V4) Fire mutate din document: intersecție, ocolire, strada nouă
- [ ] 2.4 Teste în `smoke_sesiune4.py`, golden (8 căutare pe stradă, 3 analiză hartă, 3 mutare fire), `docs/etapa-27-analiza-harta.md`, `etapa-28-mutare-fire-document.md`, `etapa-31-cautare-strada.md`

## 3. API și bancă (C)

- [ ] 3.1 (C3, C5) Pașii `cautare_strada`/`analiza_harta` și `standardizare.localizare` în răspuns; coloane noi în `banc_logica`
