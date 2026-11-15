# frontend/ (C)

Date FICTIVE.

- `plan-b/index.html`: UI complet în HTML + Leaflet, servit de FastAPI la `http://localhost:8000/ui/`. Hartă colorată după scor, predicții punctate, timeline cu play, panou „De ce?", ecranul procesului și formular de raport nou. E planul B din plan (secțiunea 7) și referința pentru Lovable.
- `lovable-prompts.md`: cele 4 prompturi pentru Lovable.
- `lovable-prompt-sesiune4-P1.md`, `-P2.md`, `-P3.md`, `-P4.md`: sesiunea 4 (vezi „Sesiunea 4” mai jos).
- Notă: `plan-b/` nu folosește `?scenariu=extrem` sau `/trasee-demo` (scoase din API în sesiunea 4).

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
- Checklist demo (sesiunea 4): `docs/demo-checklist-C.md`.
- Prompt Lovable sesiunea 3 (origine, predicție slabă/treaptă, eronat în prototip, cerc de zonă, parametri trace, pas „Geocodare"): scris în `frontend/lovable-prompt-sesiune3.md`, **netrimis** până decide omul și backend-ul întoarce câmpurile. API nou pentru el: `zona` în `GET /retea`, `trace_params` în `POST /rapoarte`; vezi `docs/etapa-24-api-sesiune3.md`.
- Prompt Lovable timeline derulabil (panou vertical, scroll mută harta, în locul Play și al barei de dată): `frontend/lovable-prompt-timeline-derulabil.md`, **netrimis** până decide omul (~4-6 credite). API: `GET /evenimente` trece `schimbari`, `pasi`, `eronat_prototip` (vezi `docs/etapa-24-api-sesiune3.md`).

## Sesiunea 4 (prototip gata de prezentat; plan: `docs/plan-sesiune-4-prezentare.md`, secțiunea 8)
Trei prompturi, un mesaj grupat fiecare, cu „NU SCHIMBA”, câmpuri exacte și „—” pentru orice lipsă. Fiecare are checklist de verificare prin tunel în fișierul lui; varianta scurtă e în `docs/demo-checklist-C.md`.

| Prompt | Conținut | Stare | Credite estimate |
|---|---|---|---|
| `lovable-prompt-sesiune4-P1.md` | curățenie, hartă tip GIS (Straturi, legendă, căutare, Identificare), culori din `banda`, „Marchează verificat de om”, accesibilitate | **aplicat 15 nov.** (6,3 credite, Lovable `966a24e`) | 5-7 |
| `lovable-prompt-sesiune4-P2.md` | pagina de intro `/`, 4 carduri „Vezi pe hartă”, 3 butoane de echipă, panoul „Ce a înțeles AI-ul”, „Resetează demo” | **aplicat 15 nov.** (5,7 credite, Lovable `34da2bf`) | ~5 |
| `lovable-prompt-sesiune4-P3.md` | timeline orizontal, vizualizarea „Căutare pe stradă” (accentul) și „Analiza hărții” | **aplicat 15 nov.** (5,9 credite, Lovable `f54b58c`) | ~5 |
| `lovable-prompt-sesiune4-P4.md` | tab „Tracking echipe” (generează tură, animare, opriri colorate, aplică, rezultat înainte→după) + buton „Șterge” în Identificare | **trimis 15 nov.** (credite neexpuse de API; estimat ~5, de verificat în editor; Lovable `0e79a4d`) | ~5 |
| `lovable-prompt-sesiune4-P5.md` | corecturi după test: fișa evenimentului nu mai acoperă Identificare, fișe curate pentru `tracking_tura`/`stergere_om`, tură nouă = „Neaplicată" (lipsa `aplicata` = false, buton „Aplică" dezactivat după aplicare), harta Tracking rămâne încadrată pe rețea/focus | **aplicat 15 nov.** (4,6 credite, Lovable `35b48c0`, 198 teste verzi) | ~5 |

Buget total 15-20 credite. 
### Publicare
- URL public: https://retea-jt-demo.lovable.app (publicat 15 nov. după P5, `deploy_project` cu `name="retea-jt-demo"`).
- Se folosește cu `?api=<URL tunel>` (ex. `https://retea-jt-demo.lovable.app/?api=https://xxx.trycloudflare.com`); fără `?api=` arată „Exemplele nu sunt disponibile".
- După orice prompt nou trebuie republicat cu deploy; previzualizarea (`id-preview--...`) se actualizează singură, URL-ul public nu.

**Endpointuri noi folosite de UI** (detalii în `docs/etapa-30-api-sesiune4.md`):
- `GET /legenda` (benzi, linii, insigne; UI nu hardcodează culori sau praguri).
- `GET /demo/exemple` (4 carduri din `data/reports/demo-intro.json`), `POST /demo/reset`.
- `POST /element/{id}/verificare` (501 până la V5 în motor).
- `GET /exemple?sursa=mentenanta|investitii|racordari` (5 texte/echipă; `apel_client` = 422).
- Câmpuri noi: `standardizare` și `focus` în `POST /rapoarte` și `GET /evenimente`; `text_original`, `echipa`, `banda_inainte`, `banda_dupa` în `GET /evenimente`; `banda`, `verificat_om`, `sursa_locatie`, `t0`, `eticheta_origine` în `GET /retea`. Etichetele „AI (live)”, „AI (cache)”, „Regex (simplificat)” vin din API (`standardizare.metoda_eticheta`).

**Ce s-a scos din UI și API:** scenariul extrem (`?scenariu=extrem`), `GET /trasee-demo`, `trace_params` și `trace` (butonul „Generează traseu ultima oră”, câmpurile de parametri), modul clic pe hartă pentru locație (butoanele „Cerere racordare casă” și „Fire mutate”), bannerul „DATE FICTIVE” de pe hartă (rămâne o linie în subsolul intro), butoanele „Apel client” și „Om din teren”, etichetele „Predicție AI”/„generat de model”/coduri brute.

**Dependențe de motor** (UI arată „—” până atunci): `banda` și `verificat_om` (V1/V2), `verificare_om` (V5), `cautare_strada` (V6), `analiza_harta` (V3). Secțiunile „Prompt Lovable sesiune 3” și „timeline derulabil” de mai sus sunt superate de P1/P3 (panoul vertical rămâne ca „Listă”); scenariul extrem pomenit în ele nu mai există.
