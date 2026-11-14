# frontend/ (C)

Date FICTIVE.

- `plan-b/index.html`: UI complet în HTML + Leaflet, servit de FastAPI la `http://localhost:8000/ui/`. Hartă colorată după scor, predicții punctate, timeline cu play, panou „De ce?", ecranul procesului și formular de raport nou. E planul B din plan (secțiunea 7) și referința pentru Lovable.
- `lovable-prompts.md`: cele 4 prompturi pentru Lovable.

## Stare Lovable
- Editor: https://lovable.dev/projects/fd19026a-1ce3-4de6-8f4d-355c351e028a
- Preview: https://id-preview--fd19026a-1ce3-4de6-8f4d-355c351e028a.lovable.app
- **NEpublicat** (publicare doar cu confirmarea omului).
- Trimis 2026-11-14: toate 4 prompturile (credite: 1,4 + 0,9 + 1,9 + 2,8 ≈ 7,0). Adăugirile față de text sunt notate în `lovable-prompts.md`.
- Lovable a construit tot, dar **nu a fost testat cu API-ul real**.
- Rămâne: (1) tunel HTTPS (preview-ul e HTTPS, `http://localhost` e blocat ca mixed content; pe laptop nu există cloudflared/ngrok, are nevoie de om); (2) setat `API_BASE` în „Setări” în aplicație; (3) test cap-coadă (hartă, timeline, „De ce?”, proces raport); (4) eventuale corecturi; (5) publicare doar cu confirmarea omului. Plan B: `plan-b/` la `/ui/`.

## Tunel (pentru Lovable)
Instalat fără sudo: binarul oficial `cloudflared-linux-amd64` (v2026.11.0) în `~/.local/bin/cloudflared`.
Pornire (detașat, tunel rapid fără cont):
```bash
nohup .venv/bin/uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 > /tmp/claude-1000/uvicorn.log 2>&1 &
setsid nohup ~/.local/bin/cloudflared tunnel --no-autoupdate --url http://localhost:8000 > /tmp/claude-1000/cloudflared.log 2>&1 &
grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/claude-1000/cloudflared.log | head -1
```
- Log tunel: `/tmp/claude-1000/cloudflared.log`; log API: `/tmp/claude-1000/uvicorn.log`.
- URL-ul trycloudflare se schimbă la fiecare repornire; se pune din nou în „Setări → API_BASE" în aplicația Lovable. Nu se scrie în repo.
- Verificat prin tunel: /health, /evenimente, /retea, POST /rapoarte, header CORS `access-control-allow-origin: *`.
- POST /rapoarte modifică modelul din memorie (demo); repornește uvicorn pentru reset.

## Cum văd aplicația
- Pornire: `backend/api/demo_start.sh` (`--restart` repornește API-ul, `--reset-model` îl repornește cu model curat, tunelul rămâne; `--port N` pentru alt port). Scriptul afișează linkul gata de deschis.
- Link: `https://id-preview--fd19026a-1ce3-4de6-8f4d-355c351e028a.lovable.app/?api=<URL tunel trycloudflare>`; URL-ul tunelului e în `/tmp/claude-1000/tunnel.url` și se schimbă la fiecare repornire a tunelului.
- Plan B: `http://localhost:8000/ui/` (UI Leaflet servit de FastAPI).
- Checklist demo: `docs/demo-checklist-C.md`.
- Prompt Lovable sesiunea 3 (origine, predicție slabă/treaptă, eronat în prototip, cerc de zonă, parametri trace, pas „Geocodare"): scris în `frontend/lovable-prompt-sesiune3.md`, **netrimis** până decide omul și backend-ul întoarce câmpurile. API nou pentru el: `zona` în `GET /retea`, `trace_params` în `POST /rapoarte`; vezi `docs/etapa-24-api-sesiune3.md`.
