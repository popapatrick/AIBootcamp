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

**C4+C8** (prompt `frontend/lovable-prompt-sesiune2-C4-C8.md`, sincronizat cu textul trimis efectiv; benzile folosesc `eticheta`, nu EV-X*): terminat (completed, mesaj `main:user#00000000000043#usr:VP42XW43`, commit Lovable `9d9fb83`, 5,3 credite). Verificat prin diff + grep: POST `/predictii/{id}/decizie` (`src/routes/index.tsx`), mesaje 501/409/404/400+422 în română (`src/lib/decizii.ts`, testate), „✓ om" în `DeCe.tsx` și `ReteaMap.tsx`, halou din `verificat_recent`/`confirmat_de`, `scos_din_uz` gri (`retea.ts`, `network-style.ts`), `scenariu=extrem` doar în `urlRetea`/`urlEvenimente` (`src/lib/scenarii.ts`), scriere dezactivată în extrem, benzi după `eticheta` (`TimelineBands.tsx`), Play cu țintă 38 s (limita ≤40 s; Lovable a măsurat ~39 s). Fără URL de tunel hardcodat (doar valori dummy în teste). Lipsă: API-ul real neverificat (doar simulat).

**C5-C7** (`frontend/lovable-prompt-sesiune2-C5-C7.md`): în draft `drft_01m7dyj7a0fx99y360qeaz4hz2` (thread `thr_y7v0efvepw7n`, commit `eaf54d3`, baza `a39cecf`), NEUNIT pe `main`, nepublicat. Terminat (completed, 11,6 credite). Verificat în diff: 3 acțiuni (Cerere racordare casă, Fire mutate, Generează traseu ultima oră) în `src/components/actiuni/`, mod clic pe hartă (`use-clic-harta.ts`), corp `/rapoarte` cu `locatie {lat,lon}` / `trace [{t,lat,lon}]` (`src/lib/actiuni.ts`), `/trasee-demo`, cerc zonă din `raza_m`, pas `trace`/`zona` în pipeline, fără URL hardcodat. Lipsuri raportate de Lovable: fluxul racordare netestat în browser; previzualizarea nu a fost redeschisă după fix-ul de tipuri; acțiunile nu sunt dezactivate în scenariul extrem (așteaptă ramura A); panoul de traseu lasă traseul pe hartă până la „Șterge traseul"; zoom pe stâlp prezis poate scoate traseul din cadru. Fișiere existente atinse de C5-C7: `AGENTS.md`, `roadmap.md`, `src/components/Raport.tsx`, `src/components/ReteaMap.tsx`, `src/lib/rapoarte.ts`, `src/routes/index.tsx`, `src/styles.css`. Se suprapun cu C4+C8 (risc de conflict la unire): `AGENTS.md`, `roadmap.md`, `Raport.tsx`, `ReteaMap.tsx`, `rapoarte.ts`, `index.tsx`. După unire trebuie dezactivate acțiunile în scenariul extrem (`scrierePermisa`).

**Unire C5-C7 + corectură** (draft `drft_01m7dyj7a0fx99y360qeaz4hz2`): `merged` în main (commit Lovable `dae4bce`, peste C4+C8 `9d9fb83`). Grep pe main: prezente împreună „Verificare în teren" + POST `/predictii/{id}/decizie`, `scenariu=extrem`, cele 3 butoane C5-C7, `trasee-demo`, `locatie`, `trace`; fără markeri de conflict. Corectură (mesaj `main:user#00000000000047#usr:E6SS75PD`, commit Lovable `3debf5b`, 2,7 credite): cele 3 butoane + panourile se dezactivează în extrem cu „Disponibil doar în scenariul normal" (aceeași condiție `scrierePermisa` ca Trimite raport / Acceptă-Respinge, prin `poateScrie`); la schimbarea scenariului se anulează modul clic și se șterg traseul/zona; la focus pe stâlpul prezis `fitBounds` include și traseul (fără zoom minim 15 când există traseu); teste noi `actiuni-scenariu.test.tsx`, `traseu-focus.test.tsx`; exemplele de tunel din teste înlocuite cu `api.example.test`. Lovable raportează: build OK, 56 teste trecute, verificare în browser cu API simulat fără erori în consolă. Credite sesiunea 2: 5,2 + 5,3 + 11,6 + 2,7 = 24,8.
Rămâne: test cu API-ul real (tunel), nepublicat (cere confirmarea omului).
