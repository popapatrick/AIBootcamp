# Prompt Lovable sesiunea 2: C5 + C6 + C7 (grupat, NETRIMIS)

- **Dependențe (pe `main` înainte de trimis):** C2+C3 și C4+C8 trimise și acceptate (halou, `clasa`, „De ce?", Show pipeline, scenariul extrem); B8 (`cerere_racordare`, gata), B5 (`mutare_fire`, gata), B7 (trace în motor, gata), A3/A4 (`backend/trace`, `backend/racordare`, gata), A5 (`data/reports/trasee-dummy.json`, 4 trasee, gata); API C1: `POST /rapoarte` cu `locatie` și `trace`, `GET /trasee-demo` (gata, `docs/etapa-7b-api-sesiunea-2.md`). Rezultatul real depinde de extracție: tipul `mutare_fire`/`cerere_racordare` din text îl recunoaște doar extracția cu Claude (cu `API_EXTRACTIE=stub` textul iese ca alt tip și nu apare zona/lanțul).
- **Cost estimat:** ~4-6 credite (un mesaj, trei butoane noi peste UI-ul existent; C7 e cel mai mare: ~2-3 din ele). Nu se trimite și nu se publică fără confirmarea omului.
- **Verificare după:** `…lovable.app/?api=<tunel>` (tunelul din `demo_start.sh`, nu se scrie în repo): (1) „Cerere racordare casă": clic pe hartă + text generat → lanț punctat de stâlpi cu scor, sau elemente noi pline dacă motorul a aplicat; (2) „Fire mutate": clic → cerc „de verificat" cu raza din răspuns + traseu punctat, în Show pipeline `potrivire` cu `zona`; (3) „Generează traseu ultima oră": alegi un traseu, se vede linia și opririle, muți un punct cu clic, trimiți; în Show pipeline apare pasul `trace`; (4) în scenariul extrem cele 3 butoane sunt dezactivate; (5) câmp lipsă => „—", fără crăpare; tot ce era în „NU SCHIMBA" merge ca înainte.

---

## PROMPT (de lipit în Lovable)

Modifică aplicația existentă (frontend, fără DB/auth, în română). Date FICTIVE. Datele vin doar din API (`API_BASE`). Fă toate cele trei părți într-o singură trecere, peste ce există deja.

### NU SCHIMBA
- Scala continuă/KMZ și comutatorul „Colorare", timeline-ul cu Play și selectarea datei, panoul „De ce?" cu butoanele Acceptă/Respinge, lista „Evenimente", scenariul extrem (comutatorul și `?scenariu=extrem`).
- `?api=<URL>` și „Setări → API_BASE"; bannerul „DATE FICTIVE"; `mod` din `/health`.
- Cele 3 exemple demo, tab-ul „Proces raport", „Show pipeline" (inclusiv tabelul „Schimbări în rețea"), „Rețea actualizată la".
- Haloul de stare și simbolurile pe `clasa`: nu reface logica, doar o refolosești. Elementele noi (stâlpi prezisi, casa) se desenează cu aceleași reguli: `nivel` = `predictie` punctat, `in_model` plin.

### Convenții comune celor trei butoane
- Trei butoane noi în bara de acțiuni: „Cerere racordare casă", „Fire mutate", „Generează traseu ultima oră". Când unul e activ, celelalte două sunt inactive; „Anulează" iese din mod fără să trimită nimic.
- „Mod clic pe hartă" (C5, C6): cursorul devine cruce, un banner mic „Fă clic pe hartă pentru locație (Esc = anulează)". Clicul pune un marcaj temporar și afișează `lat, lon` cu 6 zecimale; un nou clic mută marcajul. Fără clic nu se poate trimite.
- Toate trimit `POST {API_BASE}/rapoarte` cu `Content-Type: application/json`. Câmpurile corpului se numesc exact: `text` (string, obligatoriu), `sursa` (obligatoriu, una din `mentenanta`, `investitii`, `racordari`, `apel_client`), `data` (opțional, `YYYY-MM-DD`, data selectată pe timeline dacă există, altfel se omite), `locatie` (obiect `{"lat": <număr>, "lon": <număr>}`, doar C5 și C6) și `trace` (listă de `{"t": "<ISO>", "lat": <număr>, "lon": <număr>}`, doar C7). Fără alte câmpuri. Nu trimite `locatie`/`trace` dacă nu există.
- Răspunsul e StepTrace: reutilizează Show pipeline existent (pași, `decizie`, `schimbari`). După succes reîncarcă `GET /retea` (data curentă) și `GET /evenimente`.
- Erori: 4xx/5xx → mesaj „Raportul nu a putut fi procesat" + `detail` ca text mic; rețea căzută → „API indisponibil, setează API_BASE". Pe durata cererii butonul „Trimite" e dezactivat.
- **În scenariul extrem** (comutatorul „Scenariu: extrem" activ) cele trei butoane sunt dezactivate, cu textul „Disponibil doar în scenariul normal" (ca la „Trimite raport").
- Orice câmp absent din răspuns => „—", niciodată eroare în consolă sau ecran alb.

### PARTEA 1 (C5): Cerere racordare casă
1. Buton → mod clic pe hartă (vezi mai sus). După clic se deschide un panou lateral „Cerere racordare casă" cu: coordonatele clicului (doar citire), câmpul „Adresă (opțional)" și un câmp text „Textul cererii", precompletat și editabil: `Cerere racordare: client nou, casă la coord <lat>, <lon>` + (dacă adresa e completată) `, <adresa>`; rămâne editabil, iar la schimbarea clicului sau a adresei se regenerează doar dacă omul nu l-a modificat manual.
2. „Trimite cererea" → corp: `{"text": "<textul>", "sursa": "racordari", "locatie": {"lat": <lat clic>, "lon": <lon clic>}}` și `"data"` doar dacă e selectată pe timeline.
3. Rezultat pe hartă, după reîncărcarea `GET /retea`: elementele noi au id `NOU-<event>-S<n>` (stâlpi), `NOU-<event>-casa` (casa), `NOU-<event>-L<n>` (cabluri).
   - Dacă `nivel` = `predictie`: lanțul se desenează punctat, cu scor lângă fiecare stâlp (tooltip și „De ce?", `properties.predictie.metoda` = `lant_racordare`). Fiecare stâlp prezis e o predicție individuală: are propriile butoane Acceptă/Respinge din „Verificare în teren" (există deja).
   - Dacă `nivel` = `in_model` (motorul a aplicat direct): elementele apar pline, fără punctat, iar un mesaj „Racord aplicat în model (scor <scor>)" arată rezultatul.
   - Zoom automat pe elementele din `schimbari[].element_id` (acolo unde `ce` = `adaugat` sau `predictie`).
4. Dacă `decizie` din răspuns e `neaplicat` (scor sub prag): mesaj „Cererea nu a fost aplicată (scor prea mic)" + motivul din pași, fără elemente noi.
5. Afișează în Show pipeline pașii ca la orice raport; nu inventa pași.

### PARTEA 2 (C6): Fire mutate
1. Buton → mod clic pe hartă (clicul = centrul zonei). Panou „Fire mutate" cu: coordonatele clicului, câmpul „Motiv" (implicit „sens giratoriu") și „Textul raportului", precompletat și editabil: `Fire mutate: <motiv>, centru <lat>, <lon>. S-au mutat firele aeriene.`
2. „Trimite" → corp: `{"text": "<textul>", "sursa": "mentenanta", "locatie": {"lat": <lat clic>, "lon": <lon clic>}}` (+ `data` ca mai sus). Nu trimite raza: o decide motorul.
3. Din răspuns, pasul `potrivire` cu `rezultat.status` = `"zona"` conține `centru {lat, lon}`, `raza_m`, `elemente` (număr), `trunchiat`, `motiv_mutare`. Pe hartă: cerc subțire galben-portocaliu cu centrul în `rezultat.centru` și raza `rezultat.raza_m` (metri), etichetă „Zonă de verificat (<elemente> elemente)". Dacă `raza_m` lipsește: nu desena cercul, doar marcajul clicului și „—" la rază. Dacă `trunchiat` e adevărat adaugă „(limitat)".
4. Elementele din zonă vin din `GET /retea` cu `nivel` = `de_verificat` (halou roșu/galben conform regulii existente, scor scăzut): nu schimba redarea. „De ce?" arată motivul.
5. Traseul propus: elementele cu id `MUT-<event>-<n>` (`predictie.metoda` = `zona_mutata`), `nivel` = `predictie`, desenate punctat, cu scor în tooltip și butoane Acceptă/Respinge din „Verificare în teren" (deja existente). Dacă nu există niciunul: mesaj „Nu s-a putut propune un traseu nou, elementele sunt doar marcate".
6. În Show pipeline: pasul `potrivire` cu `status: "zona"` se afișează lizibil: „Zonă: <elemente> elemente în <raza_m> m, motiv <motiv_mutare>" (nu JSON brut), cu „—" la ce lipsește.
7. Dacă `rezultat.status` = `absent_din_model` (nimic în rază): mesaj „Niciun element în zonă, nimic de marcat".

### PARTEA 3 (C7): Generează traseu ultima oră
1. Buton → panou „Traseu ultima oră (simulat)". Încarcă `GET {API_BASE}/trasee-demo` (listă; dacă e goală sau eroare: „Niciun traseu gata făcut", butonul „Desenează traseu" rămâne pentru C7.4). Fiecare traseu are: `id`, `descriere`, `adresa`, `data`, `puncte` (listă `{t, lat, lon}`). Meniu cu `descriere` per `id`. Selectarea unui traseu: desenează `puncte` ca linie subțire albastră cu puncte mici pe hartă și zoom pe ea; marcaj „Start" la primul punct, „Final" la ultimul.
2. **Opriri evidențiate** (calculate în browser, doar pentru afișare, orientativ): puncte consecutive aflate la cel mult 12 m unul de altul și pe cel puțin 3 minute => o oprire; desenează un cerc plin proporțional cu durata, cu eticheta „<min> min". Oprirea cea mai lungă e marcată cu steluță. Calculul exact îl face motorul (pasul `trace`); afișarea din browser e doar previzualizare, așa că nu o folosi în corpul trimis.
3. Panoul arată `adresa` (editabilă, text, implicit cea din traseu: e vagă, doar strada), `data` și textul raportului, precompletat și editabil: `Raport tabletă: control pe <adresa>, lucrare finalizată.`
4. **Editare pe hartă:** buton „Editează traseul" activează: clic pe hartă = adaugă punct la sfârșit (timpul = ultimul `t` + 25 s); clic pe un punct existent îl selectează, apoi clic pe hartă îl mută acolo (sau tragere); „Șterge punctul selectat"; „Resetează la traseul ales". „Desenează traseu" pornește de la o listă goală. Fiecare punct păstrează `t` în ordine crescătoare (ISO `YYYY-MM-DDTHH:MM:SS`). Cu mai puțin de 2 puncte „Trimite" e dezactivat.
5. „Trimite raportul tabletei" → corp: `{"text": "<textul>", "sursa": "mentenanta", "data": "<data traseului YYYY-MM-DD>", "trace": [{"t": "<ISO>", "lat": <număr>, "lon": <număr>}, ...]}`. Nu trimite `locatie`, coordonate sau ID de element: adresa vagă e doar în `text` (motorul folosește traseul doar când raportul nu are ID/coordonate). Trimite toate punctele (traseul din fișier are 7-92 de puncte).
6. Show pipeline, pasul nou `trace` (înaintea `potrivire`), `rezultat` cu: `status` (`gasit` | `ambiguu` | `fara_opriri`), `opriri` (listă `{lat, lon, durata_min, inceput, sfarsit, n_puncte}`), `strada {nume, distanta_m}`, `alegere {lat, lon, durata_min, element_id, distanta_element_m}`, `vizitate [{element_id, durata_min}]`, `ambiguitate` (bool), `calitate`, `motiv`. Afișează lizibil: „Oprirea aleasă: <durata_min> min lângă <strada.nume> (la <strada.distanta_m> m)"; dacă `alegere.element_id` există: „stâlp existent confirmat: <element_id>", altfel „loc fără stâlp: stâlp nou prezis"; „Alte opriri: <număr> (<durate>)"; „Ambiguitate: da/nu" (dacă da, avertisment „două opriri aproape egale, scor redus"); „Stâlpi verificați în plus: <lista `vizitate`>". `status` = `fara_opriri`: „Nicio oprire detectată, locația nu se poate deduce". Câmp lipsă: „—".
7. Pe hartă după răspuns: opririle din pasul `trace` (nu cele din browser) ca cercuri etichetate; `alegere` ca steluță mare; stâlpul nou prezis (`NOU-<event>-…` cu `nivel` = `predictie`) apare punctat cu scor, cu zoom pe el; stâlpii din `vizitate` primesc o scurtă pulsație (confirmați). Linia traseului rămâne vizibilă până la „Șterge traseul".
8. Dacă `trace` lipsește din pași (ex. raportul a avut ID): nu afișa pasul și nu da eroare.

### Reguli generale
- Tot textul în română. Nu hardcoda URL-uri de API, tunel sau chei; doar `API_BASE`.
- Orice câmp absent din răspuns (`locatie`, `raza_m`, `elemente`, `centru`, `alegere`, `opriri`, `vizitate`, `strada`, `schimbari`, `scor`, `predictie`) => afișează „—", niciodată eroare în consolă sau ecran alb.
- Nu adăuga autentificare, bază de date sau alte pagini în afară de cele descrise.
