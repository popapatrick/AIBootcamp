# Parcurs demo sesiunea 4: CIORNĂ pentru `docs/DEMO.md` (sub 5 minute)

> Ciornă scrisă de C pentru Victor, ca să o integreze în `docs/DEMO.md`. Date FICTIVE. Locurile marcate **[de verificat la repetiție]** nu au fost văzute cap-coadă pe ecran.
> Surse: `docs/plan-sesiune-4-prezentare.md` (secțiunile 6-9), `data/reports/demo-intro.json`, `data/reports/exemple-dummy.json`, `docs/demo-checklist-C.md`.

## Mesajul care trebuie să rămână
- „AI-ul doar standardizează textul (extrage tipul, locul, data). Predicțiile sunt ale modelului nostru, cu aceleași reguli de scor pentru orice informație.”
- Accentul: **căutarea pe stradă**: din „Strada X, lângă nr. 3”, fără coordonate, modelul alege cel mai probabil stâlp și spune cât de sigur e.
- Culorile = cât de sigură e informația. Verde ≥0,80 „Sigur”, galben 0,60–0,80 „Probabil”, portocaliu 0,40–0,60 „Nesigur”, roșu <0,40 „Foarte nesigur”.

## Pregătire înainte (cu 30–60 min înainte)
1. `git pull --rebase origin main`; `backend/api/demo_start.sh --restart` (uvicorn :8000 + tunel). Notează linia „Link de deschis: <preview>/?api=<tunel>” și linia „Plan B”.
2. Laptopul demo: `claude auth login` o dată (abonament). Verifică `curl -s $T/health`: `extractie_cod: ai_cli`, `motor: real`. Fără cheie API în `.env`.
3. Chiar înainte de intrare: `POST /demo/reset` (sau `demo_start.sh --reset-model`, sau butonul „Resetează demo” din intro). Modelul trebuie să fie curat: cardul 1 și cardul 4 depind de starea de start.
4. Deschide linkul cu `?api=`, verifică în intro cele 4 carduri și că harta se colorează (nu totul galben).
5. Încălzește o dată fiecare card („Vezi pe hartă”), apoi resetează din nou. Textele din cache răspund instant; un text nou poate dura 5–20 s.
6. Deschide video-ul de rezervă într-o altă filă; deschide `http://localhost:8000/ui/` (Plan B) într-o filă separată.
7. URL-ul tunelului se schimbă la fiecare repornire a tunelului: nu-l scrie în repo; testează-l cu o oră înainte.

## Parcursul cronometrat

### 0:00–0:30 Intro `/`
- **Apeși:** nimic; pagina de intro e deschisă.
- **Spui:** „Rețeaua electrică se schimbă zilnic, dar harta ei rămâne în urmă. Noi o ținem la zi din rapoartele de teren scrise liber. Totul e demonstrativ, date fictive.”
- **Se vede:** titlul, cele 3 carduri „Cum funcționează”, cele 4 carduri de exemplu, „Intră în hartă”, subsolul „Date fictive, rețea demonstrativă.”.

### 0:30–1:10 Harta GIS: culori și legendă
- **Apeși:** „Intră în hartă”; deschizi Legenda (din `GET /legenda`); un clic pe un element (panoul Identificare).
- **Spui:** „Fiecare element are o acuratețe: verde = sigur, galben = probabil, portocaliu = nesigur, roșu = foarte nesigur. Linia plină e în rețea, cea punctată e predicția modelului.”
- **Se vede:** hartă în mare parte verde (rețeaua de start), nu totul galben; legenda cu 4 benzi și stilurile de linie; în Identificare: ID, tip, sursă („GIS”), bară de acuratețe cu textul benzii.
- **[de verificat la repetiție]** proporția culorilor la 15 nov. (planul vizează ≥ ~90% verde pe rețeaua de start).

### 1:10–2:10 Cardul 1: căutare pe stradă (ACCENTUL)
- **Apeși:** înapoi la intro, cardul 1 „Stâlp căzut lângă nr. 3” → „Vezi pe hartă” (14.11).
- **Spui:** „Tehnicianul a scris doar «Strada Orhideelor, lângă nr. 3», fără coordonate. AI-ul doar a extras locul; modelul a căutat pe stradă, într-o fereastră de 112 m, a găsit 3 stâlpi candidați și a ales cel mai apropiat.”
- **Se vede:** panoul „Ce a înțeles AI-ul” (tip, adresă, ce lipsește); pe hartă banda pe stradă, fereastra de 112 m, cei 3 candidați cu contur, cel ales plin (SIM-048), predicția punctată cu bandă mai joasă; fișa evenimentului cu „De ce?”.
- **[de verificat la repetiție]** că vizualizarea ferestrei apare (depinde de pasul `cautare_strada` din API/V6) și că alege tot SIM-048 după `--reset-model`.

### 2:10–3:00 Cardul 4: galben → verde → ✓
- **Apeși:** cardul 4 „Stâlp nou, confirmat pas cu pas” → „Vezi pe hartă”. În timeline, treci pe rând prin cele 3 momente ale lanțului pe `NOU-EV4-023` (Strada Carpati nr. 12): 14.09, 17.09, 10.11.
- **Spui:** „Același stâlp, trei informații. Pe 14 septembrie, doar adresa: galben, 0,615. Pe 17 septembrie vine GPS: verde, 0,80. Pe 10 noiembrie îl verifică un om: 1,0, cu bifă. Fiecare pas are jurnal și «de ce».”
- **Se vede:** elementul se colorează galben → verde → verde cu ✓ („Verificat de om”); în fișă, banda înainte → după și motivul.
- **[de verificat la repetiție]** că cele 3 rapoarte lovesc același element după regenerarea scenariului (ID-ul `NOU-EV4-023` depinde de ordinea rapoartelor) și că „verificat de om” apare ca ✓ în UI.

### 3:00–3:30 Cardul 3: racordare departe de rețea
- **Apeși:** cardul 3 „Casă departe de rețea” → „Vezi pe hartă” (02.09).
- **Spui:** „Casa din Strada Regina Maria nr. 40 e departe de ultimul stâlp. Modelul propune stâlpul casei și legătura pe străzi, dar scorul e mai mic, pentru că e doar o predicție.”
- **Se vede:** predicție punctată pe străzi (casă + legătură), culoare galben/portocaliu.
- **[de verificat la repetiție]** că legătura pe străzi se vede (pasul `analiza_harta` / V3) și banda exactă.

### 3:30–4:15 Raport live de la un buton de echipă
- **Apeși:** butonul „Mentenanță” → alegi din listă `mnt-02`: „Montat stalp nou pe Strada Viilor nr. 9” → Trimite. (Alternative verificate: `inv-02` „Linie nouă executată pe Strada Tineretului, stâlp nou montat între nr. 10 și nr. 20” → element nou galben, fereastră de 60 m, 3 stâlpi în fereastră; `cer-01` „Cerere racord, Strada Bălții nr. 14” → predicție portocalie.)
- **Spui:** „Acum scriu un raport nou, într-o româna obișnuită. AI-ul îl standardizează, modelul îl potrivește în rețea și harta se actualizează pe loc.”
- **Se vede:** progres în 3 pași (Standardizare AI → Potrivire → Decizie), panoul AI completat, zbor spre loc, puls, pop-up cu bandă; eticheta „AI (cache)” (textele din listă sunt în cache; „AI (live)” doar la text nou). Fără „Regex (simplificat)”.
- Verificat pe API (model resetat, 15 nov.): `mnt-02` → căutare pe Strada Viilor, fereastră de 148 m, element nou adăugat, galben (stâlpii din fereastră apar doar informativ). **[de verificat la repetiție]** pe ecran.

### 4:15–4:45 Timeline
- **Apeși:** derulezi timeline-ul orizontal înapoi la 1 august, apoi înainte la „acum”.
- **Spui:** „În trei luni, ~55 de rapoarte au adăugat, mutat, scos și confirmat elemente. Rețeaua s-a schimbat vizibil, fără ca cineva să redeseneze harta.”
- **Se vede:** puncte colorate (culoare și formă) pe timeline, harta la data aleasă, benzi înainte → după în fișă.

### 4:45–5:00 Cardul 2: sens giratoriu (DOAR dacă V4 e gata)
- **Apeși:** cardul 2 → „Vezi pe hartă” (19.09).
- **Spui:** „La sensul giratoriu firul a fost mutat: traseul nou apare, cel vechi se scoate.”
- **Se vede:** traseu nou prezis, cel vechi gri punctat („demontat probabil”).
- **ATENȚIE:** azi cardul iese `neaplicat` (depinde de V4 al lui Victor). Dacă V4 nu e gata la repetiție: **sari peste** și încheie la timeline; nu îl arăta.

### Final
- „Resetează demo” (confirmare) sau `POST /demo/reset`.
- Spui: „Același calcul de scor pentru orice informație: GIS, raport sau apelul unui client.”

## Dacă ceva pică
| Problemă | Ce faci |
|---|---|
| Tunelul sau Lovable nu răspunde | Plan B `http://localhost:8000/ui/` (Leaflet); sau `demo_start.sh --restart` pentru link nou |
| Model „murdar” după repetiții | `POST /demo/reset` / butonul „Resetează demo” / `--reset-model` |
| `/health`: `extractie_cod` ≠ `ai_cli` | `claude auth login`, `--restart`; textele din cache merg oricum |
| Text nou lent (5–20 s) | Normal; folosește textele din cache (carduri, butoane echipe) |
| Fundal gri pe hartă | Plăcile OSM cer internet; liniile rămân; comutator „Gri deschis” |
| Ultima soluție | Video-ul de rezervă (3 min) |

## Întrebări probabile ale juriului
1. **„Ce face AI-ul și ce face modelul?”** AI-ul doar standardizează textul (tip, loc, dată). Decizia, potrivirea și scorul sunt calculate de modelul nostru, cu reguli fixe din `weights.yaml`.
2. **„De unde știți că rezultatul e corect?”** Nu pretindem asta: fiecare element are scor și „De ce?”. Ce e nesigur rămâne predicție punctată, neaplicată, până îl verifică un om (✓, 1,0).
3. **„Ce se întâmplă dacă lipsesc date?”** Nu inventăm: marcăm „lipsă” sau „de verificat”. Cu doar o stradă, modelul propune un punct cu acuratețe mică (portocaliu/roșu); fără niciun indiciu de loc sau în afara zonei, nu aplică.
4. **„Funcționează cu date reale?”** Aici sunt date fictive (rețea demonstrativă). Aceeași logică merge pe orice rețea cu coordonate; pasul următor ar fi un test pe un extras real, cu acordul PPC.
5. **„Dacă AI-ul greșește la standardizare?”** Panoul „Ce a înțeles AI-ul” arată ce a extras; o greșeală de extracție se vede acolo, iar scorul scade dacă datele sunt vagi. Rezerva fără AI e marcată „Regex (simplificat)”.

## Ce trebuie verificat la repetiție (rezumat)
- V6 (`cautare_strada` în API) pentru cardul 1 și `mnt-02`; V3 (`analiza_harta`) pentru cardul 3; V4 pentru cardul 2; V5 (`verificare_om`) pentru ✓ din cardul 4.
- Stabilitatea `NOU-EV4-023` după regenerarea `events.json`.
- Durata totală cu cronometru (țintă <5 min); dacă depășește, taie cardul 3 sau cardul 2.
