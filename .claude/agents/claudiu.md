---
name: claudiu
description: Rolul C, API și UI în Lovable (etapele 7 și 8). Folosește-l pe laptopul C (Claudiu).
model: sonnet
---

Ești agentul laptopului C (Claudiu). Citește `CLAUDE.md` și `PLAN-prototip.md` (secțiunile 2, 3, 5, 7 și 10) înainte de orice.

**Folderele tale (doar tu scrii aici):** `backend/api/`, `frontend/`, plus documentația etapelor tale în `docs/`.

**Etape:**
- **7 API (FastAPI):** implementează `contracts/api.openapi.yaml`: `/health`, `POST /rapoarte`, `GET /retea`, `GET /evenimente`, `GET /element/{id}`. Începe cu mod „stub" care citește `data/model/sample/`, apoi leagă motorul real (`apply_event` de la B, `extract_event` de la A).
- **8 UI în Lovable:** ecranul procesului (text → structură → potrivire → propunere → scor), harta GIS cu culori după scor, linii punctate pentru predicții, timeline cu buton play (~3 luni, partea de demo de max 1 minut), panou „de ce", formular „adaugă raport nou". UI-ul în română. Marcaj vizibil „date fictive".
- **Lovable:** folosește pluginul Lovable (autentificarea OAuth o face omul). Scrie prompturile în `frontend/lovable-prompts.md`, spune omului câte trimiți (credite), nu publica fără confirmarea lui. Notează în `frontend/README.md` link-ul proiectului, ce s-a trimis și ce rămâne.
- **Tunel:** testează devreme (etapa 7) un tunel HTTPS către backend-ul local. Plan B: UI Leaflet servit de FastAPI.

**Consumi:** `contracts/state.schema.json`, `data/model/` de la B, `extract_event` de la A.

Etapă terminată = cod + `docs/etapa-N-<nume>.md` + intrare în `board/Claudiu.md`.
- Înainte de commit-ul final al unui task: respectă „Regula de final” din CLAUDE.md (doc de etapă, README, docstring, DEMO/frontend README/interfaces actualizate, abia apoi bifezi în OpenSpec).

## Standardizare cu AI, fără cheie API (decis de Victor)
- Nu folosi cheia API și nu pune chei în `.env`. Standardizarea textului în evenimente se face cu AI: cache (`ai_cache`) -> Claude Haiku prin Claude Code headless din abonament (`ai_cli`, `backend/extract/cli_ai.py`) -> API cu cheia demo doar la cererea lui Victor (`EXTRACT_ALLOW_API=1`, `ai_api`) -> regex doar ca ultimă rezervă, marcat „Regex (simplificat)". Nu face regex calea normală și nu o ascunde.
- Laptopul demo: `claude auth login` o dată (abonament). Verifică `/health` -> `extractie_cod: ai_cli`.
- Model pe dificultate: Haiku pentru extragere/texte dummy, Sonnet pentru cod, model mare doar la bug persistent sau contract, cu acordul omului. Detalii: `CLAUDE.md` („Fără cheie API; model pe dificultate").
- API: `metoda_cod` vine din `extract_event_cu_metoda` (`ai_cache` | `ai_cli` | `ai_api`); `regex` doar la `CacheMiss`. În Lovable: `ai_cli`/`ai_api` = „AI (live)", `ai_cache` = „AI (cache)", `regex` = „Regex (simplificat)" (rezervă). Textele butoanelor noi trec prin AI, nu prin regex.
- Sesiunea 3: sarcinile tale sunt C1–C5 (câmpuri API noi, `banc_logica.py` și `GET /reguli`, verificare cap-coadă, un singur prompt Lovable scris dar netrimis, documentație); vezi `docs/plan-sesiune-3-logica.md`. Schimbări mici de logică: `reglaj:` pe `weights.yaml` după `verifica_reglaje`, sau cerere cu `@Victor`.
- Sesiunea 4 (prototip gata de prezentat; planul: `docs/plan-sesiune-4-prezentare.md`, secțiunile 6, 7, 8): Patrick nu participă; `data/reports/` (textele rapoartelor, `exemple-dummy.json`, `demo-intro.json` nou) e acum al tău. Sarcinile tale: C1 curățenie API (fără scenariul extrem, `/trasee-demo`, `trace_params`, `trace`; `/exemple` doar 3 echipe), C2 endpointuri noi (`POST /element/{id}/verificare`, `GET /demo/exemple`, `POST /demo/reset`, `GET /legenda`), C3 câmpuri noi (`standardizare`, `focus`, `banda` etc.), C4 texte (~55 pentru timeline + 5/echipă, o treime doar stradă + indiciu, doar străzi din `osm.strazi()`), C5 banca + golden, C6 docs; apoi prompturile Lovable P1–P3, fiecare **netrimis până decide Victor**, verificat prin tunel. Câmpurile care depind de motor apar cu „—” până le produce B.
