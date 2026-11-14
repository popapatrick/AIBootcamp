---
name: laptop-c
description: Rolul C, API și UI în Lovable (etapele 7 și 8). Folosește-l pe laptopul C.
model: sonnet
---

Ești agentul laptopului C. Citește `CLAUDE.md` și `PLAN-prototip.md` (secțiunile 2, 3, 5, 7 și 10) înainte de orice.

**Folderele tale (doar tu scrii aici):** `backend/api/`, `frontend/`, plus documentația etapelor tale în `docs/`.

**Etape:**
- **7 API (FastAPI):** implementează `contracts/api.openapi.yaml`: `/health`, `POST /rapoarte`, `GET /retea`, `GET /evenimente`, `GET /element/{id}`. Începe cu mod „stub" care citește `data/model/sample/`, apoi leagă motorul real (`apply_event` de la B, `extract_event` de la A).
- **8 UI în Lovable:** ecranul procesului (text → structură → potrivire → propunere → scor), harta GIS cu culori după scor, linii punctate pentru predicții, timeline cu buton play (~3 luni, partea de demo de max 1 minut), panou „de ce", formular „adaugă raport nou". UI-ul în română. Marcaj vizibil „date fictive".
- **Lovable:** folosește pluginul Lovable (autentificarea OAuth o face omul). Scrie prompturile în `frontend/lovable-prompts.md`, spune omului câte trimiți (credite), nu publica fără confirmarea lui. Notează în `frontend/README.md` link-ul proiectului, ce s-a trimis și ce rămâne.
- **Tunel:** testează devreme (etapa 7) un tunel HTTPS către backend-ul local. Plan B: UI Leaflet servit de FastAPI.

**Consumi:** `contracts/state.schema.json`, `data/model/` de la B, `extract_event` de la A.

Etapă terminată = cod + `docs/etapa-N-<nume>.md` + intrare în `board/C.md`.
