# Checklist demo, partea C (API + UI), după `docs/DEMO.md`

## Înainte
1. `backend/api/demo_start.sh` pornește uvicorn (:8000) și tunelul și afișează linkul. Dacă rulează deja, doar îl afișează.
2. `backend/api/demo_start.sh --reset-model`: model curat, fără rapoartele live ale repetițiilor (tunelul și URL-ul rămân). Fă-l chiar înainte de demo.
3. Deschide linkul `https://id-preview--fd19026a-1ce3-4de6-8f4d-355c351e028a.lovable.app/?api=<URL tunel>`.
4. Verifică colțul `mod`: `retea=motor, evenimente=motor, motor=real`. `extractie=stub` e normal fără `.env` cu cheie.
5. Marcajul „date fictive" se vede; harta arată 530 de elemente.

## În timpul demo-ului (timpii din DEMO.md)
- 0-29 s: harta pe date 4 aug., apoi Play. Se văd: punct violet punctat (predicție), elemente care se înverzesc, un element roșu (conflict, 29 aug.), aplicare 10 sept., închidere la portocaliu în octombrie.
- 29-45 s: pauză, ecranul **Proces raport**; se lipește textul: `Confirm în teren nodul 6925190 din curba străzii, la coordonatele 44.2830311, 26.063942, între nodurile 6513200 și 7824201.` (sursa: mentenanță, data 2026-10-28). Pașii vizibili: text, structură, potrivire, propunere, scor.
- 45-60 s: „Vezi pe hartă": punctul violet devine solid. Rezultat așteptat: `adaugat`, scor 0,95, nodul și 2 legături în model.

## Plan B
- Dacă tunelul sau Lovable pică: `http://localhost:8000/ui/` (UI Leaflet servit de FastAPI, același scenariu).
- Tunelul își schimbă URL-ul la fiecare repornire: refă linkul cu `demo_start.sh` (afișează unul nou) și deschide-l din nou. URL-ul curent e și în `/tmp/claude-1000/tunnel.url`.
- Hărți de bază: plăcile OSM cer internet; fără ele fundalul e gri, liniile rămân.
- Ultima soluție: înregistrare video.

## Ce NU promitem
- Geocodarea adreselor nu e implementată: rapoartele fără coordonate nu se potrivesc pe hartă (apar ca „de verificat").
- Extracția cu Claude cere `.env` cu cheia; fără ea se folosește rezerva stub regex, vizibilă în pas (`metoda` = „stub_regex (rezervă: ...)"), iar tipul poate diferi (ex. „avarie"), dar nodul tot e tratat ca lipsă.
- Proiectul Lovable e nepublicat; se folosește preview-ul.

## Sesiunea 2 (7 features, date FICTIVE)
Valorile de mai jos sunt verificate cap-coadă pe API local cu extracția Claude (board/Claudiu.md, 2026-11-14). Detalii: `docs/DEMO.md` (Sesiunea 2), `docs/plan-sesiune-2-openspec.md`.

### Pornire
1. `backend/api/demo_start.sh --reset-model` (model curat, fără rapoartele repetițiilor).
2. Deschide `<preview>/?api=<tunel>`; URL-ul tunelului îl afișează scriptul (nu se scrie în repo).
3. Colțul `mod`: `motor=real`; pentru valorile de mai jos e nevoie de `extractie=claude` (cache în `data/cache/`).

### Pași în ordine
1. **Fire mutate (sens giratoriu).** Butonul „Fire mutate"; text de mutare, motiv „sens giratoriu"; clic pe hartă la nodul 6513200 (44.2830448, 26.0636533), rază 40 m. Se vede: zonă de 40 m, 19 elemente „de verificat" (galben), 4 trasee propuse punctat pe străzi.
2. **Cerere racordare, fără date în GIS.** Sursa `apel_client`, buton „Cerere racordare casă", clic la 44.2850305, 26.0595998 (Strada Liviu Rebreanu). Se vede: lanț punctat de 2 stâlpi plus casa, scor 0,66-0,69 (predicție, neaplicată).
3. **Acceptă/Respinge.** Pe un stâlp prezis de la pasul 2, „Acceptă": 200, stâlpul devine plin, halou verde, marcaj „om". A doua decizie pe aceeași predicție: 409, mesaj „deja decisă".
4. **Trace tabletă.** „Generează traseu ultima oră" (`trace-1`), adresa „Strada Liviu Rebreanu, în dreptul curții", sursa tabletă, text „Raport tabletă: stâlp nou necartat pe <adresa>, lucrare executată. Am verificat și stâlpii din jur.”. Se vede: pas `trace`, oprire ~22 min fără stâlp, 3 stâlpi verificați (verzi), stâlp prezis la oprire, scor 0,71.
5. **Scenariu extrem.** „Încarcă rețeaua cu evenimente" (`?scenariu=extrem`), Play: 68 de evenimente, cu `eticheta` (ramură, demontat, val de apeluri), halou verde/galben; ținta: sub 45 s.
6. **Demontat și val de apeluri** (opțional, din `docs/DEMO.md`): A-T-014 demontat apoi `scos_din_uz`; 3 apeluri pe A-T-030 scad scorul cu plafon.
7. **Locația operatorului (simulată).** Cerere racordare fără coordonate, text „Cerere racordare: client nou, casă pe Strada Liviu Rebreanu", buton „Folosește locația operatorului (simulată)". Se vede: punct dummy pe stradă cu ±40 m și marcaj „simulată", indicii cu `gasit`, lanț punctat de 4 stâlpi, scor 0,48-0,57 (sub cel cu clic, 0,60-0,71), nivel predicție, „de ce" cu „poziția SIMULATĂ". Verifică și un text negăsit („strada Foo"): eroare 422 clară, fără punct. Încă fără buton în Lovable (prompt separat); până atunci se verifică pe API: `GET /locatie-operator-demo?text=...`.

8. **Sesiunea 3 (degradat până la motor).** `GET /retea` are `zona` (cerc 3000 m); `GET /reguli` arată `weights.yaml`; `GET /geocodeaza?adresa=...` dă 501 până la A1/B2; `POST /rapoarte` acceptă `trace_params`. Banca: `python3 -m backend.api.banc_logica` (schelet, fără `data/golden/`). Promptul Lovable sesiune 3 e netrimis, deci UI-ul nu arată încă origine/slabă/zonă. Detalii: `docs/etapa-18-api-sesiune3.md`, reglaje: `docs/etapa-23-reglaje.md`.

### Riscuri cunoscute (abateri pe board)
- Cererea de racordare pe sursa `racordari` (aceleași coordonate) iese `predictie` 0,738, nu `adaugat` ~0,84 cum scrie DEMO.md (extracție 0,7, sub prag 0,75). Nu promite „adaugat" decât cu raport structurat. @Victor aliniază DEMO.md/pragul.
- Textul tabletei „stâlp nou necartat pe Strada Liviu Rebreanu..." iese `racord_nou`, nu `nod_lipsa`, la extracția Claude (prompt A2). Folosește `trace-1` din „Generează traseu", nu textul liber.
- `mut-01` din `exemple-dummy.json` are coordonate în afara rețelei (44.2799, 26.0594): iese `absent_din_model`. Pune clic/centrul la 44.2830448, 26.0636533.
