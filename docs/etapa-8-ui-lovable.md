# Etapa 8: UI în Lovable (C)

Date FICTIVE (marcaj vizibil „DATE FICTIVE" în UI).

## Ce face
Aplicație frontend (fără DB/auth) construită în Lovable din cele 4 prompturi din `frontend/lovable-prompts.md`: harta GIS colorată după scor cu predicții punctate, timeline cu play, panou „De ce?" + „Evenimente", ecran „Proces raport" (text → extracție → potrivire → scor → decizie) cu 3 exemple clicabile, formular raport nou. UI în română. Dacă API-ul nu răspunde: „API indisponibil, setează API_BASE". `mod` din `/health` apare într-un colț.

Proiect: editor https://lovable.dev/projects/fd19026a-1ce3-4de6-8f4d-355c351e028a, preview https://id-preview--fd19026a-1ce3-4de6-8f4d-355c351e028a.lovable.app. **Nepublicat.** Credite: 1,4 + 0,9 + 1,9 + 2,8 ≈ 7,0.

## Intrări / ieșiri (API, `contracts/api.openapi.yaml`)
`GET /health`, `GET /retea?data=`, `GET /evenimente` (include `decizie`), `GET /element/{id}`, `POST /rapoarte` (răspuns cu pașii extracție, potrivire, scor, `decizie`). Baza: `API_BASE`, setabil în „Setări".

## Cum se verifică
1. Pornește API: `.venv/bin/uvicorn backend.api.main:app --port 8000`.
2. Tunel HTTPS către portul 8000 (ex. `cloudflared tunnel --url http://localhost:8000`).
3. În preview: Setări → `API_BASE` = URL-ul tunelului. Verifică harta, play pe timeline, click pe element, cele 3 exemple din „Proces raport".
Fără tunel: planul B `http://localhost:8000/ui/`.

## Decizii
- Doar frontend; datele vin exclusiv din API (aceleași ponderi/scor ca restul sistemului).
- Listă de evenimente goală → un singur punct (azi); nu se pornește cerere nouă cât una e în curs.
- Praguri afișate în grafic: 0,4 și 0,75.

## Limite
- NETESTAT cu API-ul real. Preview HTTPS cere `API_BASE` HTTPS (mixed content). Pe laptopul C nu există cloudflared/ngrok.
- Publicarea cere confirmarea omului.

## Pentru ceilalți
@A/@B: UI-ul depinde de câmpurile din contract; orice schimbare în `api.openapi.yaml` cere ajustare prin prompt în Lovable (credite). Timeline-ul e gol până există `data/events/events.json`.

## Sesiunea 2

**C2+C3** (mesaj `main:user#00000000000039#usr:KZAKMXA2`, prompt `frontend/lovable-prompt-sesiune2-C2-C3.md`): terminat (completed, commit Lovable `a39cecf`, 5,2 credite). Verificat în cod (grep + diff): `/exemple?sursa=` în `Raport.tsx`, stiluri pe `clasa` (inclusiv `subteran`) în `network-style.ts`, tabel „Schimbări în rețea", „Rețea actualizată la" din `ultima_actualizare` (`/retea` și `/health`), halou cu `selected`, `?api=` păstrat (test `api-din-url.test.ts`), fără URL de tunel hardcodat în cod (doar în teste, valoare dummy). Diff-ul final mai conține retușuri (română la 404/eroare, câmpuri opționale cu „—"). Lipsă: nimic important.

**C4+C8** (prompt `frontend/lovable-prompt-sesiune2-C4-C8.md`, cu paragraful „Corecturi (contract nou)": `verificat_recent`, `scos_din_uz`, `eticheta`/`tip` în evenimente, pasul `trace` / `zona`, coduri decizie 409/404/422/501; benzile din timeline se bazează pe `eticheta`, nu pe EV-X*): trimis, mesaj `main:user#00000000000043#usr:VP42XW43`. Stare la scrierea acestei secțiuni: în lucru, diff nemărginit încă.

**C5+C7** (`frontend/lovable-prompt-sesiune2-C5-C7.md`): netrimis încă.
