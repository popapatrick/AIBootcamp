# Panou laptop B

Scrie doar aici. Intrări noi deasupra. Format: ora, gata, în lucru, blocat / am nevoie de la X, contract atins.

## B4 gata: decizia omului (Acceptă/Respinge) în motor (Victor/B)
@Claudiu: pentru `POST /predictii/{id}/decizie` (C1) construiești un Event: `echipa_sursa: "om_teren"`, `tip: "verificare"`, `status: "executat"`, `tip_sursa_pondere: "om_teren"`, `incredere_extractie: 1.0`, `forma_sursa: "campuri"`, `data` din cerere sau azi, `text_original` scurt, `referinta: {}`, `detalii: {"decizie": {"tinta_id": id, "decizie": "accepta"|"respinge", "motiv": ...}}`, `event_id` unic (ex. EV-DEC-NNN), și îl dai lui `apply_event`. Dacă trace-ul are `eroare.cod`: `deja_decis` -> 409, `necunoscut` -> 404, `decizie_invalida` -> 400. Pe hartă: `properties.confirmat_de == "om"` = plin cu marcaj „om"; `nivel == "predictie"` = punctat. Decizii noi în timeline: `aplicat`, `respins`. Detalii: `docs/etapa-14-verificare-om.md`.
@Patrick: am nevoie de 1-2 exemple de decizie în `exemple-dummy.json` (A7), doar ca text/scenariu, formatul e cel de mai sus.
Următorul la mine: B5 (mutare_fire). Smoke engine: 36 verificări, API OK. Contract atins: da, aditiv (`respins` în timeline, `eroare` în StepTrace, în interfaces.md).

## B3 gata: `schimbari[]` în StepTrace și `ultima_actualizare` în statistici (Victor/B)
@Claudiu: `apply_event` întoarce acum `schimbari: [{element_id, ce, scor_inainte, scor_dupa, de_ce}]` (ce = adaugat | actualizat | predictie | conflict | de_verificat | retras | neaplicat). `engine.statistici(data)` are `ultima_actualizare`. Trebuie doar trecute prin API (C1): `schimbari` e deja în trace-ul pe care îl primești de la motor; pentru `ultima_actualizare` expune un `GET /statistici?data=` sau pune-l în `/retea`, cum preferi (spune-mi în board). Detalii: `docs/etapa-5-scor-decizie.md`, secțiunea Sesiunea 2.
Următorul la mine: B4 (decizia omului: Acceptă/Respinge). Smoke engine: 25 verificări, API OK. Contract atins: nu.

## B2 gata: `clasa` în snapshot și network.geojson (Victor/B)
@Claudiu: `properties.clasa` (casa | important | origine | post | aerian | ramura | subteran) e pe main, în `/retea`, `/element` și `network.geojson`. Detalii și paleta: `docs/etapa-9-aspect-harta.md`. Poți trimite promptul C2 (simboluri + halou + legendă). Următorul la mine: B3 (`schimbari[]` + `ultima_actualizare`).
Smoke-urile trec. Contract atins: nu (conform celui deja publicat).

## CONTRACT PUBLICAT, putem începe toți (Victor/B, B1 gata)
@Patrick @Claudiu: commit-ul `contract:` e pe main. Faceți `git pull --rebase origin main`, apoi `openspec/changes/<feature>/tasks.md` și tabelul vostru din `docs/plan-sesiune-2-openspec.md` (A1-A8, C1-C9). Ce s-a schimbat:
- Evenimente: tipuri noi `mutare_fire`, `activ_demontat`, `cerere_racordare`; sursa `om_teren` (0,95); `detalii.decizie`, `detalii.centru/raza_m/motiv_mutare`, `detalii.trace`.
- Stare: `clasa`, `confirmat_de`, nivel `scos_din_uz`, metode noi de predicție (`lant_racordare`, `zona_mutata`, `pozitie_din_trace`).
- API: `/exemple`, `/trasee-demo`, `POST /predictii/{id}/decizie`, `locatie` și `trace` în `POST /rapoarte`, `?scenariu=extrem`; `schimbari[]` în StepTrace (vezi `contracts/interfaces.md`).
- Praguri noi în `contracts/weights.yaml`: `decizie_om`, `mutare_fire`, `val_apeluri`, `racordare`, `trace`.
- @Patrick: semnăturile `backend/trace` (`gaseste_opriri`, `localizeaza`) și `backend/racordare` (`prezice_lant`) sunt în `contracts/interfaces.md`. Străzile cu nume vin din `backend.engine.osm.strazi()` (publicat acum, 77 de străzi, 30 cu nume).
- Ordinea mea: B2 (clasa), B3 (schimbari, ultima_actualizare), apoi B4, B5. Anunț aici când fiecare e pe main. Până atunci, @Claudiu poate scrie C1 pe contract (răspunsurile motorului vin după B3).
Smoke-urile mele trec (13, 20, 9, API). Contract atins: DA (vezi `git log -- contracts/`).

## Plan explicit sesiunea 2, muncă împărțită egal (Victor/B)
@Patrick @Claudiu: citiți `docs/plan-sesiune-2-openspec.md`, secțiunile 5-8: fiecare are tabel cu sarcinile lui (A1-A8, C1-C9, B1-B9), ordinea și dependențele. Estimare: B ~9 h, A ~9,5 h, C ~10 h.
- @Patrick: pe lângă date și extracție, primești 2 foldere noi, doar ale tale: `backend/trace/` (opriri din traseul GPS, potrivire cu strada, locul cel mai lung) și `backend/racordare/` (lanț prezis de stâlpi pe străzi pentru o cerere de racordare). Sunt funcții pure; eu le integrez în motor. Semnăturile le scriu în contract.
- @Claudiu: API + tot UI-ul Lovable (C1-C9). Grupează prompturile ca să economisești credite. Nu publici.
- Eu: contractul întâi (B1), apoi motorul. Până apare commit-ul `contract:` pregătiți doar texte, scenarii și prompturi.
Contract atins: nu încă.

## Sesiunea 2: lucrăm cu OpenSpec, 4 features noi (Victor/B)
@Patrick @Claudiu: de acum features noi se planifică și se bifează în OpenSpec. Citiți `docs/plan-sesiune-2-openspec.md` (instalare în 3 comenzi, cine face ce, ordine) și apoi `openspec/changes/*/tasks.md`: sarcinile sunt pe rol. Features: `harta-aspect-kmz`, `interfata-rapoarte-pipeline`, `mutare-fire-sens-giratoriu`, `timeline-cazuri-extreme`.
- @Patrick: exemple dummy pe 4 surse (inclusiv apel call center), texte cu sens giratoriu, apoi `events.extreme.json`.
- @Claudiu: UI în Lovable (contul tău, nepublicat) și API; prompturile le scrii acum, le trimiți după commit-ul de contract.
- Eu fac întâi un singur commit `contract:` (clasa, schimbari, ultima_actualizare, tipuri `mutare_fire` și `activ_demontat`). Până atunci nu scrieți cod care depinde de ele.
**Adăugate după:** încă 3 features în OpenSpec: `verificare-om-predictii` (Acceptă/Respinge după teren), `cerere-racordare-predictie` (buton cerere racordare casă, lanț prezis de stâlpi), `locatie-din-trace-tableta` (trace GPS din ultima oră + adresă dă locul exact al stâlpului).
- @Patrick: `data/reports/trasee-dummy.json` cu cel puțin un traseu realist: operatorul a verificat stâlpi existenți (opriri lângă ei) și a stat mult într-un loc fără stâlp (de aici predicție). Adresa vagă, doar strada (ex. Strada Primăverii, din OSM). Formatul exact îl fixez în contract; până atunci pregătește doar scenariile.
- @Claudiu: la UI se adaugă butoane Acceptă/Respinge, Cerere racordare casă și Generează traseu ultima oră (editabil pe hartă).
Contract atins: nu încă (urmează).

## Cerere pentru Claudiu: verifică publicarea Lovable și spune dacă e ok (Victor/B, la cererea lui Victor)
@Claudiu: Victor îți cere să verifici publicarea aplicației Lovable și să scrii aici (board/Claudiu.md) dacă e ok. Pași, în ordinea asta, fără să publici până nu spune Victor „da" în chat:
1. Trimite Prompt 5 (culori continue, panou „De ce?" pe data aleasă, zile UTC) din nota mea anterioară; spune câte credite consumă.
2. Reia cache-ul demo pentru cele 2 texte noi din docs/DEMO.md (vezi nota mea), actualizează exemplele din Lovable.
3. Test cap-coadă pe PREVIEW (nepublicat), cu tunelul pornit (`backend/api/demo_start.sh`): hartă la încărcare pe rețea, slider + Play (~30 s), click pe un element („De ce?" se schimbă cu data), tab „Proces raport" cu cele 2 texte (1 = predicție ~0,65, 2 = adaugat ~0,95, „Vezi pe hartă"), consola fără erori, bannerul „DATE FICTIVE" vizibil.
4. Abia apoi, dacă Victor confirmă, publică și verifică linkul public: aceeași listă, plus că `API_BASE`/`?api=` nu e scris în cod sau în repo și că proiectul nu expune altceva decât demo-ul.
5. Scrie aici: ok / nu e ok, ce a mers, ce nu, credite folosite, linkul final (fără URL-ul tunelului în repo).
Contract atins: nu

## Răspuns pentru Claudiu și Patrick: textele live (Victor/B)
Mulțumesc, Claudiu: ai prins corect că cu extracția Claude primul text iese direct `adaugat` și povestea „predicție -> promovare" dispare. Aleg varianta (a), fără să mut praguri. Texte noi în docs/DEMO.md (verificate prin simulare cu extracție Claude 0,75-0,9: 1 = predicție 0,60-0,65, 2 = adaugat 0,90-0,95):
1. (mentenanță, 2026-10-29) „Lipsește din GIS un stâlp nou la coordonatele 44.281738, 26.064996, pe strada din colț."
2. (racordări, 2026-10-31) „Nod lipsă din GIS: stâlpul nou 7011223 la coordonatele 44.281738, 26.064996, între nodurile 7322194 și 7456900. Lucrare executată."
@Claudiu: trebuie reluat cache-ul demo pentru aceste 2 texte (sursă + dată incluse în cheie), ca în Lovable să se completeze exact aceste texte; tu ai cheia. Apoi actualizează exemplele din Lovable la aceleași texte. Textele vechi din cache pot rămâne.
@Patrick: EV-010 (racordari_02, A-T-021) nu are încă `detalii.sectiune_noua` = "TYIR 3x50+54,6 OL-Al": fără ea scenariul 5 nu mai dă conflict (singura linie rămasă din cererea mea).
Teste B (smoke_network, match, engine, osm): OK după ultimele commit-uri.
Contract atins: nu

## Pentru Claudiu (C): verificat API-ul pe datele curente (29 ev.) și ce ar bloca demo-ul (Victor/B)
Verificat de mine (B) pe laptopul meu: `/health` (sursa_evenimente=events.json), preflight CORS pentru POST JSON de la origin-ul preview-ului Lovable: ok; POST /rapoarte ~1,7 s la primul apel (încărcare model), apoi instant. Nu am acces la proiectul tău Lovable (e în contul tău; din contul lui Victor dă 404), deci nu l-am testat.
**1. Exemplele din Prompt 4 nu mai dau rezultat bun:**
- „stâlp nou 44.2849717, 26.0601908" e acum la câțiva metri de un nod existent, deci rezultatul e doar „confirmare". Înlocuiește cu: „Nod lipsă din GIS: stâlpul nou 7011223 la coordonatele 44.281738, 26.064996, între nodurile 7322194 și 7456900. Lucrare executată." (mentenanță): rezultat predicție 0,72; al doilea raport (racordări, același nod) îl promovează în model. Textele exacte sunt în docs/DEMO.md.
- „apel client str. Florilor nr. 12" iese „neaplicat": fără coordonate apelul nu se poate plasa. Folosește un apel cu coordonate, ex. „Nu am curent, coordonate 44.2829, 26.0646, client C-10234".
**2. Culori:** Lovable folosește 3 trepte (verde ≥ 0,75, galben 0,4-0,75, roșu): toată rețeaua rămâne galbenă pe tot timeline-ul, nu se vede nimic. În plan-b am pus scală continuă. Prompt 5 de trimis în Lovable (~1 credit), gata de lipit:
> Schimbă culorile elementelor in_model într-o scală continuă după scor: hue = 120 × clamp((scor − 0,3) / 0,5, 0, 1) în HSL (saturație 78%, luminozitate 42%), deci 0,3 = roșu, 0,55 = galben, 0,8 = verde. Nivelul de_verificat rămâne roșu #dc2626, predicție violet punctat. Legenda devine un gradient „scor 0,3 → 0,8" + „de verificat" + „predicție". Panoul „De ce?" trebuie să se refacă la fiecare schimbare de dată din timeline (și în Play): ia scorul, nivelul și motivele elementului selectat din feature-ul GeoJSON de la `GET /retea?data=` curent, nu din ultimul răspuns de la `/element`; istoricul vine tot de la `/element/{id}`. Calculează zilele timeline-ului în UTC (altfel fusul orar arată ultima zi cu o zi înainte). Noduri mici (rază 2,5, contur alb 1 px).
**3. Conflictul din scenariul 5** lipsește acum din timeline până pune Patrick `detalii.sectiune_noua` la EV-010 (i-am scris).
**4. Pe Lovable la demo:** testul cap-coadă îl poți face doar tu (proiectul e în contul tău). Verificarea minimă: slider + Play (~30 s), click pe un element, tab „Proces raport" cu cele 2 texte de mai sus, „Vezi pe hartă".
Contract atins: nu

## Răspuns pentru Patrick (A) după events.json cu 29 (B/Victor)
Scenariul 1 e închis: EV-028 (`nod_lipsa`, status „semnalat", cu coordonate și vecini) intră în model pe 23 oct. cu scor 1,0; `6925190` e predicție până la 22 oct. și `in_model` de pe 24 oct. „Semnalat" nu mai plafonează o propunere (doar „planificat"). Teste B: toate OK.
@Patrick: PIERDERE la re-extragere: EV-010 (2026-08-29_racordari_02, A-T-021) nu mai are `detalii.sectiune_noua` (textul spune „Pe A-T-021 este montat conductor TYIR 3x50+54,6 OL-Al"), deci nu mai apare CONFLICTUL cu EV-009 (3x70) și scenariul 5 dispare din demo. Pune înapoi `detalii.sectiune_noua = "TYIR 3x50+54,6 OL-Al"` (la orice tip; motorul îl tratează ca observație și compară cu EV-009).
Contract atins: nu

## Repetiție demo (B, cu events.json real al lui A)
Gata: docs/DEMO.md (scenariu de 60 s, text de lipit, riscuri). Rulat în browser: Play ~29 s, raport live prin „Proces raport": predicția nodului 6925190 devine în model (scor 0,95, 2 legături).
Calibrare pe extracția REALĂ (28): 13 scor actualizat, 9 neaplicat, 2 predicție, 2 fără efect, 1 conflict, 1 aplicat. Multumesc A: element_id 28/28 și `id_partial` ajută.
Schimbări noi de motor: (1) `detalii.id_partial` (T-002) + nodurile din text aleg categoria tronsonului (A-T-002 se potrivește acum la raportul din 22 sept.); (2) un raport de teren cu un nod numeric inexistent în model + coordonate e tratat ca nod lipsă, oricare ar fi tipul; (3) „semnalat" nu mai plafonează o propunere la predicție (doar „planificat").
@A: (1) pentru scenariul 1, un raport cu coordonatele nodului (44.2830311, 26.063942) într-o dată din toamnă ar închide povestea direct în timeline. (2) Rapoartele cu coordonate fără etichete (4427960, 2606510): pune numerele în `referinta.coordonate` și marchează în `campuri_lipsa`; motorul repară punctul zecimal și inversările și le marchează „de verificat", așa nu pierdem racordul.
@C: am schimbat în frontend/plan-b/index.html culoarea elementelor într-o scală continuă după scor (0,3 roșu -> 0,8 verde) + legendă gradient: cu 3 trepte toată rețeaua rămânea portocalie pe tot timeline-ul. Nu am atins altceva.
Contract atins: nu.

## UI plan B reparat de B, cu acordul lui Victor (B)
@C: am modificat ÎN FOLDERUL TĂU `frontend/plan-b/index.html` (doar acest fișier), la cererea lui Victor, pentru cele 4 probleme din nota anterioară: (1) `map.invalidateSize()` înainte de `fitBounds` + la resize, deci harta pornește pe rețea; (2) noduri mici (raza 2,5) cu contur alb de 1 px, fără contur gros; (3) panoul „De ce?" se reface la fiecare schimbare de dată (scorul și motivele la data din timeline, „la <dată>" lângă scor), istoricul vine din /element; (4) zilele timeline-ului în UTC (`setUTCDate`), slider-ul nu mai arată cu o zi înainte. Verificat în browser: harta pe zoom 15 la încărcare, panoul urmează slider-ul (R-T-012: 0,488 la 7 oct. -> 0,565 la 22 aug.), ultimul eveniment live (14 nov.) = ultima zi, consola fără erori.
Dacă ai modificări necomise în acest fișier, fă `git pull --rebase` și rezolvă; nu am atins altceva din frontend/ sau backend/api/.
Contract atins: nu.

## Verificare UI plan B (B, în browser, motor real + rezervă)
Cum am verificat: am pornit `uvicorn backend.api.main:app`, am deschis /ui/ în browser, am apăsat pe elemente, Play și am procesat un raport live.
Merge: harta cu OSM și rețeaua, culori după scor, predicțiile violet, panoul „De ce?" cu istoric și motive, timeline cu Play (data avansează, harta se reîncarcă), ecranul „Proces raport" (un raport live trece prin 5 pași: text original, structură, potrivire, predicție, scor și decizie, cu butonul „Vezi pe hartă"). Fără erori în consolă.
@C probleme găsite (în frontend/plan-b/index.html):
1. **La încărcare harta e pe zoom 0 (toată lumea), rețeaua e un punct.** `map.getSize()` dă 644x643 deși zona vizibilă e ~503 px: `fitBounds` rulează înainte de layout. Soluție: `map.invalidateSize()` înainte de `fitBounds` (și la `window.onload`/resize). Verificat în pagină: cu `invalidateSize()` + `fitBounds` ajunge la zoom 15 și se vede rețeaua.
2. Markerele de noduri sunt prea mari și acoperă liniile (la zoom 15 rețeaua arată ca un nor de puncte). Micșorează raza (ex. 2-3 px) sau desenează nodurile doar la zoom ≥ 17.
3. Panoul „De ce?" rămâne pe data la care ai selectat elementul: la schimbarea datei din timeline (sau Play) afișează text vechi („Neverificat de 87 zile" la o dată mai veche). Reîncarcă `/element/{id}` sau recalculează la schimbarea datei.
4. După un raport live, slider-ul arată 2026-11-13 deși evenimentul e 2026-11-14 (probabil `toISOString()` în UTC vs dată locală).
5. Extracția e încă „stub_regex" (încredere 0,45): backend/extract nu e activ pe acest laptop (lipsește cheia OpenRouter). Pe laptopul lui A ar fi „claude".
Reparat de mine (B): `urmeaza_strada` din predicții e acum pe fiecare legătură (avea media tuturor, deci arăta „linie_dreaptă, urmează strada 0,67" pentru o legătură fără stradă).
Contract atins: nu.

## Calibrare pe cele 28 de rapoarte (B)
Gata: calibrare politica de scor. Doc: docs/calibrare.md. Rulare: `.venv/bin/python -m backend.engine.calibrare` (folosește data/events/events.json dacă există; acum „oracol" = adevărul tău din index.json + regex, pentru că events.json nu e pe main și n-am cheia OpenRouter).
Rezultat pe 28: 12 scor actualizat, 9 neaplicat, 3 predicție, 2 fără efect (planificat), 1 conflict, 1 aplicat. Scenariile 1-6 se comportă cum scria planul; scenariul 7 (doar adresă) rămâne neaplicat (geocodarea nu e implementată).
Schimbări de motor: nod_lipsa lângă un vecin (3,9 m) = element nou, nu confirmare; nod fără coordonate cu 2 vecini în text = doar predicție la mijlocul dintre vecini; punct zecimal pierdut reparat; conflict între observații de secțiune; raport de teren „semnalat" confirmă la jumătate; rază 40 m pentru apeluri; scădere în timp rămâne −0,05/30 zile (−0,07 făcea 97 % din rețea „de verificat" într-o singură zi).
Contract atins: DA, `contract:` weights.yaml (praguri noi de potrivire, factor_semnalat_teren, scădere −0,05) + `verificare` în schemă (deja anunțat).
@A IMPORTANT: am FIXAT nodul lipsă pe 6925190 (ca în rapoartele tale; defects.json înapoi la valorile vechi: vecini 6513200 și 7824201, tronsoane lipsă A-T-054 și A-T-057). Ignoră nota mea anterioară cu 6948201. În raportul mentenanta_01/04 nu ai coordonate pentru nod: motorul îl pune doar ca predicție (poziție deduse din vecini). Dacă vrei să-l vedem aplicat, adaugă într-un raport coordonatele nodului din defects.json (44.2830311, 26.063942).
@A: când împingi events.json rulez din nou calibrarea pe extracția reală și îți spun unde cade scorul din cauza erorilor de tip/ID.
@C: ID-urile s-au întors la 6925190 (predicțiile NOU-<event> se promovează pe el); eșantionul din data/model/sample/ și rezerva sunt regenerate.

## Răspuns pentru A: `tip: verificare` acceptat (B)
Da, de acord. Am adăugat `verificare` în `tip` (contracts/event.schema.json, commit `contract:`). Motorul îl tratează ca inspecție în teren fără modificări: dacă echipa e de teren și status=executat, elementul primește confirmare (+ scor, `ultima_verificare` = data raportului). Verificat: un `verificare` pe un nod îl duce de la 0,6 la 0,715. Util pentru scenariul 6 (zone verzi vs roșii în timp).
@A: EV-S05 (linie_planificata) iese „neaplicat": motorul are nevoie de `detalii.noduri` cu 2 ID-uri de noduri existente ca să deseneze linia planificată. Pune-le dacă raportul le cunoaște; dacă nu, rămâne în jurnal fără geometrie.
@A: pentru rapoartele doar cu coordonate lasă `element_id: null` (corect); potrivirea o face match_event. Codurile T-054 / T-002 fără prefix sunt tratate ca ambigue (A-/R-/S-): nu le inventa prefixul.
@A: cât lipsește events.json, motorul folosește events.stub.json (5 evenimente), apoi rezerva mea. Când împingi events.json (28), preia automat locul.

## Verificare integrare B <-> API (B)
Rezultat: API-ul lui C se leagă de motorul real (`/health`: motor real, retea motor, evenimente motor), `smoke_api` trece.
Problemă găsită și reparată de mine: fără evenimente de la A, `/evenimente` era gol. Am adăugat evenimente de REZERVĂ sintetice ale lui B în data/model/events.fallback.json (11, scenariile 1-4 + linie planificată); motorul le folosește doar dacă lipsesc data/events/events.json și events.stub.json. `engine.sursa_evenimente()` zice care s-a folosit. Alte reparații: `snapshot()` fără dată merge pe ultima dată; predicția unui nod lipsă se promovează pe ID-ul real când vine al doilea raport; câmpul `forma_sursa` are valorile `campuri` / `text_liber` (nu „formular").
@A: când împingi data/events/events.json, preia automat locul rezervei. Folosește `forma_sursa` = `campuri` sau `text_liber` (nu „formular").
@C bug în extracția stub (backend/api/pipeline.py): RE_NOD `\d{7}` prinde cifrele din coordonate (ex. „44.2849717" -> element_id 2849717) și raportul pică pe „absent_din_model" cu ID fals. Cere cuvânt-cheie („nod"/„stâlp") sau exclude cifrele precedate de „." sau urmate de cifre. Pot verifica după ce repari.
@C: /health ar putea arăta și `engine.sursa_evenimente()` ca să se vadă când rulăm pe date de rezervă. Atenție: ID-urile elementelor prezise sunt `NOU-<event_id>` (nod) și `NOU-<event_id>-<vecin>` (legături); după promovare apar cu ID real.
Contract atins: nu.

## Etapa 6 gata (B)
Gata: traseu pe stradă din OSM (cache local în data/model/osm/, rutare fără internet). Doc: docs/etapa-6-traseu-osm.md. Test: `.venv/bin/python -m backend.engine.smoke_osm` (9 verificări). `get_model()` îl activează singur.
Rezultat onest: pe nodul lipsă, o legătură urmează strada (0,96), cealaltă rămâne linie dreaptă (nicio stradă credibilă aproape). Traseul NU ridică scorul față de linia dreaptă (0,88 -> 0,85), dar propunerea trece oricum pragul. KMZ-ul e fictiv și nu urmează străzile, deci nu putem măsura precizia, doar arăta mecanismul.
În lucru: calibrare pe rapoartele lui A când apar în main; verific integrarea cu API-ul lui C.
Contract atins: nu (pasul „predicție" din StepTrace are în plus `rezultat.legaturi`).
@C: pentru hartă de bază folosește OSM cu atribuire „© OpenStreetMap contributors". Predicțiile au `predictie.metoda` = traseu_strada_osm sau linie_dreapta.
@A: nimic nou pentru tine.

## Etapa 5 gata (B)
Gata: scor, decizie și model în timp. Doc: docs/etapa-5-scor-decizie.md. Test: `.venv/bin/python -m backend.engine.smoke_engine` (16 verificări, pe evenimente sintetice).
În lucru: etapa 6 (traseu OSM), apoi calibrare pe rapoartele lui A.
Contract atins: DA, `contract:` (state.schema: `predictie.propunere` și `scor_propunere`; weights.yaml: secțiunea `propunere`, scădere −0,07/30 zile; interfaces: modulul și `statistici`).
@C: modulul se importă așa: `from backend.engine.engine import apply_event, snapshot, timeline, statistici, reset, jurnal` (modul `backend/engine/engine.py`). La prima folosire reia evenimentele din data/events/events.json (altfel events.stub.json). `snapshot(data)` întoarce GeoJSON cu `nivel` (in_model / predictie / de_verificat), `scor`, `motive` („de ce"), `predictie`. `timeline()` are acum câmpul `decizie`. `statistici(data)` dă procentele pe niveluri.
@A: pentru ca scorul să iasă corect, în Event completează `tip_sursa_pondere`, `forma_sursa`, `incredere_extractie`; pentru înlocuiri `detalii.sectiune_noua`; pentru nod lipsă `detalii.noduri_vecine` (2 ID-uri; altfel se deduc și scorul scade); pentru linie planificată `detalii.noduri` (2 ID-uri). Regula: tableta și formularul cu ID intră în model, textul liber cu extracție slabă rămâne predicție. Apelurile de clienți scad puțin încrederea, nu șterg nimic.

## Etapa 4 gata (B)
Gata: potrivirea evenimentelor pe rețea (`match_event`, ID -> coordonate -> adresă), 13 cazuri verificate. Doc: docs/etapa-4-potrivire.md. Test: `.venv/bin/python -m backend.engine.smoke_match` (venv: `python3 -m venv .venv && .venv/bin/pip install -r backend/engine/requirements.txt`).
În lucru: etapa 5 (scor și decizie), apoi 6 (OSM).
Contract atins: DA, `contract:` adaug `match_event` în interfaces.md.
**@A IMPORTANT, defectele din data/model/defects.json s-au SCHIMBAT față de nota anterioară** (prima alegere avea un nod vecin la 3,9 m). Folosește doar valorile din fișier:
- scenariul 1: nod lipsă 6948201 (tronsoane lipsă A-T-017 și A-T-133, vecini 6166490 și 6396507, colț de ~109 de grade);
- scenariul 2: A-T-002, în model TYIR 3x35+54,6 OL-Al, în teren TYIR 3x70+54,6 OL-Al (neschimbat).
@A: ID-uri de tronson cu prefix (A-T-002); fără prefix (T-002) sunt ambigue. Geocodarea adresei nu e implementată, deci scenariul 7 (doar adresă) iese „nepotrivit".
@C: eșantionul din data/model/sample/ a fost regenerat cu noul nod lipsă; structura e aceeași.

## Etapa 1 gata (B)
Gata: rețeaua în graf (1 post, 265 noduri, 264 tronsoane, toate capetele legate), defecte introduse, eșantion fals pentru C. Documentație: docs/etapa-1-retea-graf.md. Smoke test: `python3 -m backend.engine.smoke_network`.
În lucru: etapa 4 (potrivire) cu events.stub.json; apoi etapa 5 (scor).
Blocat: -
Contract atins: DA, `contract:` ID-uri tronson. Codurile T-001 se repetă în 3 categorii, deci id-ul unic e A-T-001 / R-T-001 / S-T-001; nodurile sunt coduri numerice (ex. 6925190), nu 6-031.
@A: pentru rapoartele dummy folosește ID-urile reale din data/model/network.geojson și defectele din data/model/defects.json (scenariul 1: nod lipsă 6925190, vecini 6513200 și 7824201, colț de ~121 de grade; scenariul 2: tronsonul A-T-002 are în model secțiunea veche TYIR 3x35+54,6 OL-Al, în teren TYIR 3x70+54,6 OL-Al).
@C: eșantion fals dar valid în data/model/sample/ (3 date + timeline.json, niveluri in_model / predictie / de_verificat). Se generează cu `python3 -m backend.engine.sample`.

## start
Gata: -
În lucru: nu am început. Aștept să citesc CLAUDE.md, planul și contractele.
Blocat: -
Contract atins: nu
