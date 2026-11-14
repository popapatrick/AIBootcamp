# Panou laptop B

Scrie doar aici. Intrări noi deasupra. Format: ora, gata, în lucru, blocat / am nevoie de la X, contract atins.

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
