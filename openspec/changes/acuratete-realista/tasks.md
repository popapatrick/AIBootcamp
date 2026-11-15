# Tasks

## 1. Contract (B, `contract:`)

- [x] 1.1 `weights.yaml` (`acuratete`, `retea_start`, `plafon_locatie`, `culori`, `verificat_om`), limite, relații în `verifica_reglaje`, `state.schema.json` (`banda`, `verificat_om`, `sursa_locatie`, `t0`), `event.schema.json` (`verificare_om`), `interfaces.md`

## 2. Motor (B)

- [x] 2.1 (V1) Scădere separată pe origine, plafon după sursa locației, prag de aplicare pentru rapoarte executate, `banda`, `sursa_locatie`
- [x] 2.2 (V2) SIM-* „din rapoarte mai vechi”, scoruri amestecate deterministe
- [ ] 2.3 (V5) Eveniment `verificare_om`, „Acceptă” = verificare de om, contradicție
- [ ] 2.4 Teste în `smoke_sesiune4.py`, `docs/etapa-26-acuratete-realista.md`, `docs/etapa-29-verificat-om.md`

## 3. API (C)

- [x] 3.1 (C2, C3) `POST /element/{id}/verificare`, `banda`/`verificat_om`/`sursa_locatie`/`t0`/`eticheta_origine` în `GET /retea`, `GET /legenda`; teste în `smoke_api.py`
