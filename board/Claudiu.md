# Panou laptop C

## 2026-11-15, logic-v2 pus, prototip PUBLICAT (Claudiu, C)
- Tag `logic-v2` pe 2c42106 (DEMO_DATA inclus), pus de Claudiu la cererea lui. `verifica_tot.sh` TOT VERDE. De acum: fără schimbări în motor/API/cache până după demo.
- Lovable publicat: **https://retea-jt-demo.lovable.app/?api=<tunel>** (fără login). Codul Lovable n-are URL de tunel sau chei hardcodate (verificat cu grep).
- Test local al tab-ului Tracking (Playwright): merge generare, viteză x30/x60/x120, „Sari la sfârșit”, „Aplică în model” (4 confirmați, 1 presupus), „Șterge” doar pe stergibil. Defecte UI în lucru (P5, apoi republicare): fișa evenimentului acoperă butoanele din Identificare; fișa turei arată `tracking_tura` brut; tura nouă „—” în loc de „Neaplicată”; zoom 8 la intrarea în tab.
@Victor: pasul 5 (test din fereastră privată) îl fac după P5.
Contract atins: nu

## 2026-11-15, DEMO_DATA gata (Claudiu, C)
@Victor: DEMO_DATA gata pe eedc520, gata pentru logic-v2. `pipeline.data_demo()` = env `DEMO_DATA`, implicit 2026-11-15, în loc de `date.today()` la cheia de cache (2 locuri). Smoke simulează altă zi: 3 texte din `docs/demo-texte-live.md` dau `ai_cache`. verifica_tot: TOT VERDE. Notă: `backend/extract/extract.py:168` mai are `date.today()` pentru data evenimentului când modelul n-o dă (nu intră în cheie; nu am atins).

## 2026-11-15, P4 trimis la Lovable; demo stabil (tunel, texte live, checklist) (Claudiu, C)
Gata:
- **P4 trimis** (decizia lui Claudiu): commit Lovable `0e79a4d` (tab „Tracking echipe” + buton „Șterge” doar cu `stergibil`, 409 tratat); repo `a71efc1`. Neverificat încă în browser (viteza x30/x60/x120, animația, reset).
- **`demo_start.sh`** (`caea122`): dacă tunelul salvat nu răspunde la `/health`, oprește cloudflared-ul vechi și pornește unul nou; `--tunel-nou` forțează. Azi tunelul căzuse cu procesul încă viu.
- **Texte live în cache** (`456aaf6`): 10 texte scrise de mână pe cele 3 echipe, lista în `docs/demo-texte-live.md`. ATENȚIE: cheia cache-ului conține data de azi (`date.today()`), deci în ziua demo-ului se refac dimineața (POST /rapoarte o dată pe fiecare).
- **Checklist** `docs/demo-checklist-C.md` §8 „Ziua demo: stabilitate”; cadre video de rezervă `docs/demo-video-cadre.md`.

@Victor:
1. Pune tag-ul `logic-v2` când închizi motorul; laptopul de demo rulează `git checkout logic-v2`, fără pull în ziua demo-ului.
2. După repetiția finală nu mai trimitem prompturi Lovable.
3. Publicarea proiectului Lovable (URL fix, fără login, dar public) rămâne decizia ta; altfel preview cu login + `?api=`.
4. Intrarea de mai jos (P4 „așteaptă decizia”) e depășită: P4 e trimis.
Contract atins: nu

## 2026-11-15, API tracking + ștergere gata, prompt Lovable P4 scris (Claudiu, C)
Gata: `POST /tracking/genereaza`, `GET /tracking/ture`, `POST /tracking/aplica` (`tracking[]` cu `t_ajungere` în secunde + `eticheta` română + `focus`), `POST /element/{id}/stergere` (409 `nu_se_sterge_retea_start`/`deja_sters`, 404 `necunoscut`), `eticheta_text` pe `/evenimente` („Tracking echipă”, „Ștergere”), `DECIZII["sters"]` = „Șters de om”; `/demo/reset` golește turele. Teste în `smoke_api.py` (OK: API), `verifica_tot.sh` TOT VERDE, banc_logica 0 erori. Doc: `docs/etapa-35-api-tracking-stergere.md`. Tasks 3.1 și 4.1 bifate (`tracking-echipe`).
@Victor: **P4 gata de trimis, așteaptă decizia ta** (`frontend/lovable-prompt-sesiune4-P4.md`: tab „Tracking echipe” + buton „Șterge”, ~5 credite, cu exemple JSON reale). Netrimis la Lovable.
Observație: o ștergere refuzată (409) e jurnalizată de motor ca „Ștergere neaplicată” și apare în timeline; dacă nu vrei asta, e de oprit în motor (B).
Contract atins: nu

## 2026-11-15, cardul 2 mutat (Crinului × Rebreanu) + localizarea în prezentare reparată (Claudiu, C)
Gata, după cererea lui Victor:
- `data/reports/2026-10-10_mentenanta_29.txt`, cu textul tău; intrarea e în `index.json` după `2026-10-08_mentenanta_20` (57 de rapoarte). Cache Haiku: `mutare_fire`.
- `demo-intro.json` intro-2: `text` = fișa, `data_moment` 2026-10-10, `focus` {44.283675, 26.062802, 17} și descrierea ta.
- `prezentare.py`: `_pas` ia acum ULTIMUL pas cu numele dat (a doua geocodare = intersecția). Localizarea apare „Intersecția Strada Crinului cu Strada Liviu Rebreanu, ±15 m”, cu `sursa: intersectie` și plafonul 0,6; „Coordonate (dedus)” = 44.283675, 26.062802. Test prin API: decizie `aplicat`.

`verifica_tot.sh` TOT VERDE.
@Victor:
1. Poți regenera `events.json`. ID-urile de după 10.10 cresc cu 1 (cardul 1 devine `EV4-057`); `NOU-EV4-023` din cardul 4 rămâne stabil.
2. Raportul vechi al cardului 2 (`2026-09-19_mentenanta_16`, Șoseaua Principală) e încă în scenariu. Spune dacă îl scot.
3. **Verificarea UI cap-coadă:** aștept să deschidă Claudiu preview-ul logat în Lovable (de pe laptopul C, browserul nu e conectat la agent).
Contract atins: nu

## 2026-11-15, ciornă parcurs demo + exemple de echipă reparate (Claudiu, C)
Gata:
- **`docs/demo-parcurs-sesiune4-ciorna.md`:** parcurs de 5 minute, cronometrat. Are pregătire, rezerve și întrebările juriului. E ciornă pentru `docs/DEMO.md` (al lui Victor), cu pașii nesiguri marcați „de verificat la repetiție”.
- **Exemplele de echipă:** le-am rulat pe toate 15 prin API, pe model resetat.
  - `inv-02` (linie planificată) și `inv-05` (stâlp lângă PTAB 7812) ieșeau `fara_efect` / `neaplicat`. Le-am înlocuit cu stradă + indiciu: acum ies element nou galben / portocaliu (cache Haiku).
  - `mnt-03`, `inv-03` și `inv-04` ies `de_verificat`, cu 0 stâlpi în fereastră. Le las: arată corect cazul „nu găsesc, marchez de verificat”.
- **`prezentare.py`:** precizia din textul de localizare e rotunjită („±127 m”, nu „±127.4775…”).

`verifica_tot.sh` TOT VERDE.
@Victor: un raport `linie_planificata` din API (cu adresă, cu ID sau cu 2 puncte GPS) iese `fara_efect` sau `neaplicat`, fără predicție punctată pe hartă. În rețeta 7.1, „linie planificată” = predicții punctate. Verifică dacă e intenționat.
Contract atins: nu

## 2026-11-15, cardul 4 refăcut (lanț galben → verde → verificat de om), preview (Claudiu, C)
Gata, după propunerea (a) a lui Victor:
- **Cardul 4**, lanțul pe același element `NOU-EV4-023` (Strada Carpati nr. 12), verificat cu `genereaza_scenariu.py --out` (copie în scratchpad) + `engine.timeline()`:
  1. `2026-09-14_mentenanta_14`: stâlp nou montat, doar adresa → `EV4-023` adăugat, 0,615 galben;
  2. `2026-09-17_mentenanta_15`: verificare cu `Cod element: NOU-EV4-023` + GPS → 0,80 verde;
  3. `2026-11-10_mentenanta_27`: `verificare_om` pe `NOU-EV4-023` → 1,0.

  Cache: doar cele 3 texte noi (Haiku). `index.json` actualizat. Cardul are `data_moment` 2026-09-14 și titlul „Stâlp nou, confirmat pas cu pas”.
- **API prin tunel:** toate endpointurile răspund. `POST /element/{id}/verificare` merge (V5 e în motor).
- **Preview Lovable neverificat vizual:** extensia Chrome nu e conectată, iar preview-ul cere login Lovable. Rămâne verificarea manuală după `docs/demo-checklist-C.md`.

`verifica_tot.sh` TOT VERDE.
@Victor:
1. Commitul tău cu `events.json` trebuie să includă textele acestea (`event_id` stabil: `NOU-EV4-023` depinde de ordinea rapoartelor). Dacă adaugi rapoarte înainte de 14.09, ID-ul se schimbă și pică rapoartele 2 și 3.
2. Pentru o cerere de logică, dacă vrei: un raport `verificare` doar cu coordonate (fără ID), la 0,6 m de un stâlp nou, s-a potrivit pe tronsonul `NOU-EV4-023-6747737` (0,6 m), nu pe nodul `NOU-EV4-023` (0,7 m). La „stâlp verificat” ar trebui preferat nodul. L-am ocolit punând ID-ul în text.
Contract atins: nu

## 2026-11-15, Lovable P3 aplicat (Claudiu, C)
Gata: P3 aplicat: timeline orizontal, vizualizarea căutării pe stradă (fereastra din `linie`, candidații, cel ales) și a analizei hărții (apare când vine V3). 154 de teste, 5,9 credite, commit Lovable `f54b58c`, nepublicat. Total P1–P3: 17,9 credite (estimat 15–20).
În lucru: verificarea preview-ului cu API-ul real, prin tunel.
Contract atins: nu

## 2026-11-15, P2 aplicat, P3 trimis; texte corectate; cardurile de intro legate de timeline (Claudiu, C)
Gata:
- **Lovable P2** aplicat: intro pe `/`, harta pe `/harta`, 3 butoane de echipă, panoul „Ce a înțeles AI-ul”. 133 de teste, 5,7 credite, commit `34da2bf`.
- **P3** trimis (timeline orizontal + căutarea pe stradă). Fereastra se desenează din `rezultat.linie`.
- **Cele 3 texte semnalate de Victor** sunt corectate și re-extrase cu Haiku; toate 3 ies acum cu `tip_asteptat`:
  - `2026-08-13_mentenanta_06` → `activ_inlocuit`;
  - `2026-09-10_investitii_03` → `nod_lipsa`;
  - `2026-11-06_investitii_10` → `nod_lipsa`.

  Cache: doar cele 3 intrări noi. `fill_cache --lipsa` dă 0.
- **Cardurile de intro:** P2 caută evenimentul cardului în `GET /evenimente` după `text_original` == `text`. Înainte, niciun card nu avea textul în rapoarte.
  - Acum `text` din `demo-intro.json` e exact conținutul fișierului de raport: intro-2 = `2026-09-19_mentenanta_16`, intro-3 = `2026-09-02_racordari_03`, intro-4 = `2026-09-14_mentenanta_14`.
  - Cardul 1 („stâlp căzut lângă nr. 3”) e raportul nou `2026-11-14_mentenanta_28.txt` (Strada Orhideelor), adăugat în `index.json` (56 de rapoarte).
  - Pe „Viilor nr. 15” motorul dădea 8 candidați (`de_verificat`); pe „Orhideelor lângă nr. 3” dă 3 candidați → predicție pe `SIM-048`, cum cere planul.

`verifica_tot.sh` TOT VERDE.
@Victor:
1. La `genereaza_scenariu.py`: `text_original` din `events.json` trebuie să fie conținutul exact al fișierului `.txt`, altfel cardurile de intro nu-și găsesc evenimentul.
2. Cardul 1 e verificat pe un model gol (3 candidați). La 14 nov. în timeline, ancorele pot schimba numărul; verifică după ce generezi `events.json`.
3. Cardul 4 (Carpati nr. 12): lanțul înlocuit → confirmat cu GPS → verificat de om depinde de rapoartele `2026-09-17_mentenanta_15` și `2026-11-10_mentenanta_27`, care trebuie să lovească același element. Verifică în scenariu.
Contract atins: nu

## 2026-11-15, Lovable P1 aplicat, P2 trimis (Claudiu, C)
Gata: P1 aplicat de Lovable: hartă tip GIS (Straturi, Legendă din `/legenda`, Identificare, bara de jos), culori doar din `banda`, butonul „Marchează verificat de om”. Scoase: scenariul extrem, `trace_params`, bannerul „DATE FICTIVE”. 116 teste trecute, 6,3 credite, commit Lovable `966a24e`, nepublicat. Am verificat diff-ul, nu încă preview-ul cu API-ul real. P2 (intro + echipe + „Ce a înțeles AI-ul”) e trimis acum.
În lucru: P2. P3 îl trimit după V6 (`cautare_strada` în `pasi`).
Contract atins: nu

## 2026-11-15, sesiunea 4: C1–C5 gata, P1–P3 scrise (Claudiu, C)
Gata:
- API (C1–C3, C5): scoase extrem/`/trasee-demo`/`trace_params`/`trace`; `GET /exemple` doar 3 echipe; noi `GET /legenda`, `GET /demo/exemple`, `POST /demo/reset`, `POST /element/{id}/verificare`; `standardizare` + `focus` în `POST /rapoarte` și `GET /evenimente`; `banda`/`verificat_om`/`sursa_locatie`/`t0`/`eticheta_origine` în `/retea`; banca are coloanele noi. Doc: `docs/etapa-30-api-sesiune4.md`.
- Texte (C4): 55 de rapoarte noi în `data/reports/` după rețeta 7.1 (cele 41 vechi înlocuite), doar cele 24 de străzi; 21/55 doar stradă + indiciu; `exemple-dummy.json` 5/echipă; `demo-intro.json` 4 carduri. Cache AI umplut cu `ai_cli` (Haiku, abonament): 70 texte, 0 lipsă.
- Prompturi Lovable P1, P2, P3 în `frontend/lovable-prompt-sesiune4-P*.md`. Claudiu a decis să le trimit fără să aștept (le trimit pe rând, după verificare prin tunel).
`scripts/verifica_tot.sh`: TOT VERDE; banca 20/20.
@Victor:
1. Până le dă motorul, API-ul trece null pentru `banda`, `verificat_om`, `sursa_locatie`, `t0` și `banda_inainte`/`banda_dupa`. `POST /element/{id}/verificare` dă 501 până apare `verificare_om` în motor (V5); după aceea merge fără schimbări în API.
2. Cele 4 texte „verificat de om” din scenariu: extracția Haiku nu le dă încă `tip: verificare_om` (promptul nu știe tipul). Trebuie adăugat în prompt la V5, apoi refăcut cache-ul doar pentru ele.
3. `events.json` nu e regenerat din textele noi (pasul tău 7.3/3, `genereaza_scenariu.py`).
4. P3 are nevoie în pasul `cautare_strada` de: `indiciu{tip,numar,numar_2,text}`, `ancore[{numar,lat,lon}]`, `candidati[{element_id,distanta_m}]`, `ales`, `punct{lat,lon}`. Ideal și o polilinie `fereastra_traseu` pentru fereastra pe stradă (altfel UI-ul desenează un cerc). În `analiza_harta`: `alternative[{de_la,lungime_m,motiv,traseu}]` și pozițiile stâlpilor noi.
5. „Elemente de verificat” în UI = `banda` portocaliu sau roșu. Spune dacă vrei alt criteriu.
Contract atins: nu

## 2026-11-15, Lovable timeline derulabil trimis și aplicat (Claudiu, C)
Gata: `frontend/lovable-prompt-timeline-derulabil.md` trimis. Lovable: Play/slider scoase, panou vertical „Evenimente”, scroll mută harta (debounce 150 ms, cache pe scenariu+dată), contur portocaliu pe elemente atinse, „De ce?” din `pasi`; 108 teste trecute, build OK; 4,7 credite; commit Lovable `7bc0a2e`. Nepublicat; preview neverificat de mine cu API-ul real.
Contract atins: nu

## 2026-11-15, timeline derulabil: 2.1 API + prompt scris (Claudiu, C)
Gata: 2.1: `GET /evenimente` (normal 29 intrări, `?scenariu=extrem` 70) trecea deja `schimbari`, `pasi`, `eronat_prototip` neatinse (API nu filtra); adăugat test în `smoke_api.py` (ambele scenarii), smoke_api și cu `API_EXTRACTIE=stub`: OK. Prompt scris: `frontend/lovable-prompt-timeline-derulabil.md`, **NETRIMIS până decide omul**, ~4-6 credite; câmpurile verificate pe răspunsul real. Docs: etapa-24 (secțiunea „Timeline derulabil, 2.1”), frontend/README.
@Victor: (1) `eronat_prototip` e `false` pe toate cele 29/70 intrări de start, deci insigna se vede doar după un raport la ~40 km; verifică că intrarea live din `GET /evenimente` îl poartă. (2) pe intrările de start `pasi` nu conține `geocodare` (doar extractie, potrivire, predictie, scor), ok, promptul tratează pasul ca opțional. (3) în `tasks.md` rămân 3.2 (plan-B), 3.3, 4.1.
Contract atins: nu

## 2026-11-15, Lovable sesiunea 3 trimis și aplicat (Claudiu, C)
Gata: promptul `frontend/lovable-prompt-sesiune3.md` trimis la cererea omului, cu corecturile din C3 (pas `geocodare` separat, `pasi[trace].rezultat.sursa`, `trace_params` cu `zgomot_m`/`durata_oprire_min`/`acoperire`/`decalaj_m`/`dezactivat`). Lovable: toate 8 puncte, 100 teste trecute, build OK; 3,4 credite; commit Lovable `3bf19ad`. Nepublicat; nu am verificat încă preview-ul cu API-ul real (tunel).
Contract atins: nu

## 2026-11-15, C1–C5 gata (Claudiu, C)
Banc pe golden 19/20; singura diferență `g-06-ortografie` (cu ai_cache iese `neaplicat`, golden cere predicție): @Patrick. Ghidul de reglaje (`docs/etapa-23-reglaje.md`) actualizat pe B6/`logic-v1`. Prompt Lovable sesiune3 scris și NETRIMIS (decide omul). `verifica_tot.sh` TOT VERDE.
Contract atins: nu

## 2026-11-15, C3 runda 3b: banc golden cu AI (`--cu-ai`, ai_cli din abonament) (Claudiu, C)
După golden-ul regenerat (da927ab), tot 14/20, dar alte cazuri. Cu AI: `g-06` (ortografie) iese `predictie` 0,477 și `r-07` iese corect, deci erau doar lipsă de cache. Rămân: `g-05`, `g-07`, `g-08`, `r-02` (motor, @Victor, ca mai jos) și nou **`g-02-coordonate`**: AI extrage `activ_inlocuit` -> `neaplicat` (@Patrick: prompt sau așteptat?).
@Patrick: textele golden nu au cache comis (fără AI totul iese `regex`). Rulează `fill_cache --lipsa` pe golden și comite cache-ul; cache-ul `ai_cli` generat la mine rămâne necomis.
Contract atins: nu

## 2026-11-15, C3 runda 3: banc pe data/golden (Claudiu, C)
Gata: banca rulează pe `data/golden/` (20 cazuri): **14 ok, 6 diferite, 0 erori**; pe exemple-dummy 27/29 (`om-01/02`). Reparat în banc: `eronat_prototip` absent = false (8 diferențe false), coloană `nivel`. Smoke API (și stub), engine 36, `verifica_tot.sh` verzi. OpenSpec reglaje 3.1 bifat. Doc: „C3 runda 3" în `docs/etapa-24-api-sesiune3.md`.
@Victor: (1) `g-05` stradă fără număr se potrivește cu linia `SIM-L30` -> `in_model` (așteptat predicție); (2) `g-07/g-08` (geocodare necunoscută) iese `neaplicat` fără `nivel`, golden zice `de_verificat`: aliniezi decizia/nivelul sau golden; (3) `r-02` treapta 1 (nod `SIM-020` din B3), golden 2: reglaj de distanță treaptă sau golden de recalculat.
@Patrick: `g-06` („liviu rebrianu") și `r-07` („cerere de racordare pentru o casa noua", iese `racord_nou`) cer cache AI/prompt; pe regex nu ies. `om-01/02`: ținta `NOU-EV-012` nu e în model la rulare izolată și regex n-o extrage.
Contract atins: nu

## 2026-11-15, C3 runda 2: geocodare + trace pe motor (Claudiu, C)
Gata: (a) pasul `geocodare` vine din motor, imediat după `extractie` (ex. „Strada Regina Maria 5" -> gasit, 25 m, acuratețe 0,55); `pipeline._pas_geocodare` nu dublează, nu a fost nevoie de reparație. `detalii.geocodare` nu e în Event-ul pasului `extractie`, doar în pasul `geocodare`. (b) `trace_params` ajunge la motor: pas `trace` cu `sursa: simulat`, `opriri`, `factor_trace`; zgomot 2 m 1,13 > implicit 1,10 > zgomot 40 m 0,75; acoperire 0,2 -> 0,65. Reparat în API: `TraceParams` nu avea `dezactivat` (era ignorat, traseul se genera oricum). (c) plafon standardizare ok pe cache AI (stradă+număr 0,7, doar stradă 0,5, reper 0,4). Smoke API (și stub), engine 36 verzi; banca 28/29 (doar `inv-05`); bancă `--json` are acum `geocodare_status`, `precizie_m`, `trace_sursa`. Doc: secțiunea „C3 runda 2" din `docs/etapa-24-api-sesiune3.md` (redenumit din etapa-18-api-sesiune3, ciocnire cu etapa-18-geocodare-adresa).
Nu iese: `trace_sursa` nu e câmp de nivel superior (se citește din `pasi[trace].rezultat.sursa`); `data/golden/` lipsește; pe regex (fără cache) nu există `adresa_structurata`, deci nici plafon.
@Victor: (1) traseul generat e determinist pe `event_id`; cu `API_EXTRACTIE=stub` același punct (44.2849717, 26.0601908), `acoperire 1.0`, a dat `fara_opriri` (factor 0,75) la unele id-uri, deși cere oprire de 12 min; verifică dacă e intenționat. (2) `detalii.geocodare` și `trace_sursa` nu ies în Event-ul întors în `pasi[extractie]`; dacă UI-ul le vrea acolo, trebuie puse de motor. (3) `api.openapi.yaml` tot nu descrie `trace_params`, `/geocodeaza`, `/reguli`.
@Patrick: `data/golden/` (A6) lipsește; `geo` dă 150 m pentru „Strada Viilor" fără număr (inv-05, mnt-06/07), ok ca precizie (fals pozitivul „Calea Victoriei" din runda 1 nu l-am reverificat).
Contract atins: nu

## 2026-11-15, C3 runda 1 (Claudiu, C)
Gata: banc pe fallback exemple-dummy: 29 cazuri, **28 ok, 1 diferit** (era 22/7). Cauze: 6 din 7 erau în banc (`element_id` citit din `modificari[0]`; acum element referit: potrivire, apoi `referinta`, apoi modificat; `element_modificat` în JSON); `inv-05` e extracție. `origine` (B3) apare, nu a fost nevoie de ajustare. Smoke API (și stub) și engine 36 verzi. Detalii în `docs/etapa-24-api-sesiune3.md`.
@Patrick (prompt/cache/geo): (1) `inv-05` „Investitie: stalp nou pe Strada Viilor, langa scoala. fara coordonate inca" iese `linie_planificata` (0,4), așteptat `nod_lipsa`; fie promptul, fie așteptatul din exemple-dummy. (2) geo: „Calea Victoriei 10 Bucuresti" se potrivește pe „Strada București" (gasit, 150 m, 0,4), fals pozitiv; „strada" și „Strada Inexistenta 99" -> necunoscut corect. Nu am găsit text care să dea `in_afara_zonei` (doar coordonate). (3) `om-01/02` au `tinta_id` exemplu (NOU-0001/2), fără predicție în memorie -> `neaplicat`; pune ținte reale în golden.
@Victor (logică): (1) `cer-02` „cerere racordare: casa langa nodul 7101969 ... 12.11.2026" iese `predictie` 0,787 (lanț 1 stâlp, `NOU-EV-LIVE-004-S1`), nota așteptatului zice „actualizare directă"; decide care e corect. (2) Motorul nu cheamă `geocodeaza` (doar `match.py` pomenește geocodarea): pasul `geocodare` din API nu apare la niciun caz; contractul zice că motorul pune `detalii.geocodare`? Dacă da, lipsește. (3) `mnt-04/rac-04/apl-04` (ID 9999xxx inexistent) -> `absent_din_model`, `neaplicat`, ok.
Contract atins: nu

## 2026-11-15, sesiunea 3: C1, C2 schelet, C4 scris (Claudiu, C)
Gata: C1 (API pass-through): `trace_params` în `POST /rapoarte`, pas `geocodare`, `zona` în `GET /retea`, `GET /geocodeaza` (501 până la A1/B2), `GET /reguli`; C2 schelet: `python3 -m backend.api.banc_logica` (fallback pe `exemple-dummy.json`: 29 cazuri, 22 ok, 7 diferite, 0 erori, cauza necercetată, `asteptat` e orientativ); C4: `frontend/lovable-prompt-sesiune3.md` scris. Docs: `docs/etapa-24-api-sesiune3.md`, `docs/etapa-23-reglaje.md`. Smoke-uri OK: API (și cu `API_EXTRACTIE=stub`), engine 36. Bifate în OpenSpec: geocodare 4.1, racordare 4.1, retea-start 4.1+4.2, safeguard 4.1, traseu 4.1, reglaje 3.2 (nu 3.1: banca e schelet până la `data/golden`).
Degradat: `/geocodeaza` 501 până la `backend.geo` (A1/B2); `zona` din centroid + weights până la `engine.zona` (B1); `origine`, `slaba`, `treapta`, `eronat_prototip` apar doar când motorul le produce.
@Victor: `api.openapi.yaml` nu descrie `trace_params` în `POST /rapoarte`, nici `GET /geocodeaza`, `GET /reguli`; `zona` doar în summary `/retea`; contractul zice „/stare", endpoint-ul real e `/retea` (zona e acolo). Banca citește `modificari[0].origine`, `predictie.slaba/treapta`, `out.eronat_prototip`; spune dacă le pui altundeva.
@Patrick: format `data/golden` propus de banc: listă JSON `{id, sursa, text, data?, asteptat?}`; chei comparate din `asteptat`: `tip, decizie, nivel, origine, slaba, treapta, eronat_prototip, element_id`. Banca citește `data/golden/*.json` fără `calibrare-referinta.json`.
Lovable: prompt netrimis.
Contract atins: nu

## 2026-11-15, locația operatorului (simulată) pentru cerere de racordare (Claudiu, C)
Gata, făcut de C la cererea omului („fă tu totul"): schimbarea OpenSpec `locatie-operator-racordare` + `docs/etapa-17-locatie-operator-racordare.md`. `GET /locatie-operator-demo?text=` (alias `adresa`) generează determinist o poziție GPS dummy din textul operatorului (stradă, colț, cartier `is_in`, combinații; `indicii` cu `gasit`, `zona`, `precizie_m`, `simulata: true`; 422 clar dacă nu se găsește nimic, fără punct inventat). `POST /rapoarte` acceptă `locatie_operator`; pașii au `sursa_locatie` (text | clic | operator_simulat). Scor: x`racordare.factor_locatie_operator` 0,8, mereu predicție (ex. 0,57 vs 0,713 cu clic). Smoke-uri OK (racordare 20, sesiune2 30, engine 36, API cu și fără `API_EXTRACTIE=stub`).
@Patrick: am atins `backend/racordare/` (fișier nou `operator_demo.py`, export în `__init__.py`, teste în `smoke_racordare.py`, README), la cererea omului; `prezice_lant` neschimbat. Fișierele `data/cache/*.json` neurmărite de pe laptopul meu nu le-am comis; unul (tableta „lucrare finalizată") schimbă tipul și pică o aserțiune veche din `smoke_api`.
@Victor: am atins, la cererea omului, `backend/engine/sesiune2.py` (`_cerere_racordare`: `detalii.locatie_operator`, factor, `sursa_locatie`), `backend/engine/osm.py` (`strazi()` are și `zona`, aditiv), `contracts/weights.yaml` (5 chei noi sub `racordare`), `smoke_sesiune2.py`. Comportamentul vechi e neschimbat. Verifică, te rog, că factorul 0,8 și precizia pe tip (10/15-40/60 m) ți se par rezonabile.
Lovable: nu am atins `frontend/`; promptul pentru buton („Folosește locația operatorului (simulată)") urmează, îl scrie omul/Claude separat.
Contract atins: DA (aditiv): `GET /locatie-operator-demo`, `locatie_operator` în `POST /rapoarte`, `sursa_locatie`, `osm.strazi().zona`, `racordare.factor_locatie_operator` etc. (commit `contract:`, `contracts/interfaces.md` + `api.openapi.yaml` actualizate).

## 2026-11-14, metoda_cod în API + regex pentru butoanele C5-C7; Lovable C4+C8 și C5-C7 (Claudiu, C)
@Victor: făcut (1) din cererea ta (05d0d49): `pasi[extractie].metoda_cod` (`ai_cache` | `ai_api` | `regex`) + `/health.extractie_cod`; `CacheMiss` prins explicit -> regex, cu motivul „text nou, fără cache: extracție simplificată (regex)". (2) Lovable (etichetele AI/Regex/Predicție AI) urmează într-un prompt mic, după corectura de unire.
Fără cheie, textele generate de butoanele noi (coordonatele clicului) nu au cache. Le-am dat reguli regex fixe în `backend/api`: „Cerere racordare: ..." -> `cerere_racordare`, „Fire mutate: ..." -> `mutare_fire` (centru, sens_giratoriu), „Raport tabletă: control pe ..." + `trace` -> `nod_lipsa` executat. Încrederea regex rămâne max 0,6; nu am atins ponderi.
@Victor, de verificat: pe regex, traseul `trace-1` izolat dă stâlpul la **0,774 -> `in_model`** (cu AI era 0,71 -> predicție); racordarea 0,60-0,71 (predicție), fire mutate 19 de verificat + 4 trasee (ca la AI). E ok ca o extracție regex să bată pragul de aplicare prin trace? Dacă nu, spune ce factor ajustezi (nu umblu la praguri).
@Patrick: am văzut CacheMiss + cheia `agent-haiku`; cache-ul meu bce63df (cheie veche) poate fi scos odată cu celelalte ~91 vechi, nu mă deranjează.
Lovable: C2+C3 (5,2 credite) și C4+C8 (5,3) pe main; C5-C7 (11,6) făcut în draft paralel, unit în main acum (aprobat de Claudiu), urmează o corectură (conflicte + butoanele C5-C7 dezactivate în scenariul extrem). Nepublicat.
Contract atins: nu

## 2026-11-14, API pe contractul B5-B8 + test cap-coadă cu extracția Claude (Claudiu, C)
Gata: C1c (30ce218): `model_scenariu("extrem")` în API (shortcut scos), câmpurile noi trec neatinse (`tip`/`eticheta`, `verificat_recent`, `scos_din_uz`, pas `trace`, `potrivire.status: zona`). `smoke_api` nu mai depinde de extracție (predicția se pregătește cu un Event `nod_lipsa` direct); trece cu Claude și cu `API_EXTRACTIE=stub`. Decizia rămâne pe `apply_event` + `trace.eroare.cod` (`aplica_decizie` ridică același ValueError pentru 409 și 400).
Test cap-coadă pe API local (port 8011, Claude real): giratoriu cu clic OK (zonă 40 m, 19 elemente de verificat, 4 trasee propuse); cerere racordare fără GIS OK (lanț 2 stâlpi + casă, 0,66-0,69); trace-1 + „Strada Liviu Rebreanu" OK (pas `trace`, oprire 21,7 min, 3 stâlpi vizitați actualizați, stâlp prezis 0,71); apel + Acceptă 200, a doua 409; extrem 68 ev. cu `eticheta`. Cache Claude comis (fb422a1).
@Victor: cererea de racordare pe sursa `racordari` (aceleași coordonate, 44.2850305, 26.0595998) iese `predictie` 0,738, nu `adaugat` ~0,84 ca în DEMO.md (extracție 0,7). Aliniezi DEMO.md sau pragul/factorii?
@Patrick: (1) textul „Raport tabletă: stâlp nou necartat pe Strada Liviu Rebreanu, în dreptul curții, executat. Am verificat și stâlpii din jur." iese `racord_nou`, așteptat `nod_lipsa` (promptul extract, A2). (2) `mut-01` din exemple-dummy.json are coordonatele 44.2799, 26.0594, în afara rețelei demo: iese `absent_din_model`. Pune un centru din rețea (ex. 44.2830448, 26.0636533, cum a cerut Victor).
Lovable: C2+C3 în lucru, urmează C4+C8 și C5-C7 (prompturi în `frontend/`). Nu public.
Contract atins: nu

## 2026-11-14, C1 complet pe main; prompturi Lovable (Claudiu, C)
Gata: C1 (1c86d51) + C1b (e740bf0). `schimbari` în `POST /rapoarte`; `ultima_actualizare` la nivel superior în `GET /retea`, `/health`, `POST /rapoarte` (răspuns la întrebarea ta din B3, nu fac `/statistici` separat). `POST /predictii/{id}/decizie` prin `apply_event` (Event `om_teren`, `EV-DEC-NNN`): 200 / 409 `deja_decis` / 404 `necunoscut` / 422 corp invalid. `?scenariu=extrem` pe `/retea` și `/evenimente` (68 ev.). `/exemple` și `/trasee-demo` citesc fișierele lui Patrick. Smoke API și engine OK.
Lovable: promptul C2+C3 trimis; C4+C8 scris (`frontend/lovable-prompt-sesiune2-C4-C8.md`), îl trimit după ce termină C2+C3. Nu public.
@Victor, nepotriviri de contract (aditiv, la tine):
- `api.openapi.yaml`, decizie: lipsesc 422 (corp invalid) și 501 (fără motor real).
- `scenariu` e declarat ca path `/evenimente?scenariu` (greșit) și lipsește la `/retea`.
- `engine.get_model()` nu are sursa `extreme`; scenariul e construit în API (`sources.model_extrem()`, marcat `shortcut:`). Când ai B6/3.3, îl mut pe motor.
- Timeline-ul nu are câmp care să marcheze ramura/demontat/val; UI-ul le recunoaște după `event_id` EV-X01..X10. Un câmp (ex. `eticheta`) ar fi mai sigur.
Aștept: B5+B8 (C5, C6), B7 (C7), B6 (C8 complet).
@Patrick: `exemple-dummy.json` are cheia `om_teren`, pe care `/exemple?sursa=` nu o expune (sursele UI sunt cele 4); spune dacă o vrei în UI.
Contract atins: nu

## 2026-11-14, ce mai aștept de la Victor (și Patrick) pentru C1-C8 (Claudiu, C)
@Victor: am văzut B3 (ea24eeb), îl leg acum în API (C1). Mai aștept, în ordinea în care mă blochează:
1. **B4**: funcția de decizie a omului (acceptă/respinge, `confirmat_de: om`). Până atunci `POST /predictii/{id}/decizie` întoarce 501. Blochează C4.
2. **B5 + B8**: zona „de verificat" la `mutare_fire` și lanțul de racordare. Blochează C5 și C6.
3. **B6**: încărcarea scenariului `extrem`. Blochează C8 (`?scenariu=extrem` dă 404 până atunci).
Întrebări pentru contract:
- Pragul de 45 de zile pentru haloul verde („verificat recent") e în `weights.yaml`? API-ul nu îl expune, deci deocamdată e scris direct în UI. Vrei să-l expun (ex. în `/health` sau `statistici`)?
- Formatul unui element din `GET /exemple` nu e fixat în contract. Propun `{sursa, text, data?}`; confirmi?
@Patrick: **A1** `data/reports/exemple-dummy.json` (lipsește încă), pentru butonul „Generează exemplu"; format ca mai sus.
Contract atins: nu

## 2026-11-14, sesiunea 2 pornită (Claudiu, C)
@Victor: am văzut contractul (c4e6b88) și B2 (`clasa`). În lucru: C1 (API: `schimbari`, `/exemple`, `/predictii/{id}/decizie`, `/trasee-demo`, `?scenariu=extrem`, `locatie`/`trace` în POST /rapoarte) pe contract; ce depinde de B3/B4/B6 întoarce `[]`/501 până apar în motor. În paralel scriu promptul Lovable C2+C3 (nu îl trimit încă).
Contract atins: nu

### 2026-11-14, @Patrick: am reparat (cu acordul omului) data inventată în extract_event când data lipsește (ex. 2025-01-01): se păstrează doar dacă apare în text, altfel azi + campuri_lipsa. Promptul neschimbat, cache-ul valid. Teste adăugate. Poți relua lucrul; fă git pull. Hash: vezi git log (`[A] data inventată`). Contract atins: nu.






## 2026-11-14 21:00, PREDARE către Victor (Claudiu, C)
@Victor: Claudiu îți predă de aici partea de demo și publicarea. Stare la predare, toată verificată:
- **Backend** (laptopul lui Claudiu): `backend/api/demo_start.sh` pornește uvicorn (:8000) și tunelul cloudflared și afișează linkul gata făcut. `--reset-model` curăță rapoartele live (tunelul rămâne). `--restart` repornește uvicorn. URL-ul tunelului se schimbă doar dacă repornește cloudflared; e în /tmp/claude-1000/tunnel.url, nu în repo. Acum: extracție claude, motor real, 29 de evenimente (conflictul EV-010 inclus), model curat.
- **Lovable** (în contul lui Claudiu, NEpublicat, preview privat): linkul e `<preview>/?api=<URL tunel>`; parametrul `?api=` setează API_BASE. Ecrane: hartă (scală continuă, noduri mici), timeline cu Play, „De ce?" pe dată, „Proces raport" cu 3 exemple (textele tale 1 și 2 + apelul cu coordonate), toate cu cache Claude în data/cache/. Detalii în frontend/README.md și docs/etapa-8-ui-lovable.md.
- **Demo:** docs/DEMO.md + docs/demo-checklist-C.md. Textul 1 dă predicție 0,58, textul 2 dă adaugat 0,95 (7011223 plus 2 legături).
- **Patrick:** data inventată în extract_event e reparată (31b0847); poate relua lucrul.
- **Rămâne:** (1) decizia de publicare: Lovable e în contul lui Claudiu, deci el apasă „Publish" sau îți dă acces; (2) repetiția de 60 s în browser (eu nu am browser). Credite Lovable folosite azi: ≈ 16,9.
Contract atins: nu

## 2026-11-14 20:50, verificare înainte de publicare: OK pe preview (Claudiu, C)
@Victor: rezultatul pașilor din cererea ta.
1. Prompt 5: nu a mai fost nevoie de el. Culorile continue (0,3 → 0,8), „De ce?" pe data din timeline (zile UTC) și nodurile mici (2,5 px, contur alb; predicții 5 px) sunt în Lovable, verificate cu Playwright pe API-ul real, fără erori în consolă.
2. Cache Claude pentru cele 2 texte noi: comis (9a75c47). Exemplele din Lovable au exact aceleași texte, surse și date (1 = mentenanță 2026-10-29, 2 = racordări 2026-10-31, 3 = apelul cu coordonate 2026-10-30).
3. Test prin tunel, pe backend-ul curent (main f3792ff, cu fix-ul EV-010 al lui Patrick): `/health` arată extracție claude și motor real. 29 de evenimente, cu conflictul EV-010 înapoi în timeline. Textul 1 dă `predictie` 0,58 (EV-LIVE-001); textul 2 dă `adaugat` 0,95, nodul 7011223 plus 2 legături în model (EV-LIVE-002). Ambele vin din cache, sub 0,3 s. Reparat: rapoartele live primesc acum ID unic EV-LIVE-NNN (0583625; înainte venea „EV-001" din cache). Verificat în testele Lovable: hartă (265 noduri, 264 tronsoane), slider, Play, „De ce?", „Vezi pe hartă", banner „DATE FICTIVE"; 86 de cereri prin tunel, toate 200.
4. URL-ul tunelului nu e scris nicăieri în repo. Preview-ul e privat (401 fără cont Lovable), de aceea tu ai primit 404.
Concluzie: OK pe preview. NU am publicat. Public doar după „da" de la tine și de la Claudiu.
Credite Lovable folosite azi: ≈ 16,9.
Contract atins: nu

## 2026-11-14 20:35, textele demo noi: cache + exemple Lovable (Claudiu, C)
@Victor: am preluat varianta (a). Cache-ul Claude e comis în `data/cache/` pentru cele 2 texte noi din docs/DEMO.md, cu sursa și data din DEMO.md. Rezultat cu extracția Claude, pe motorul de pe main: (1) mentenanță, 29 oct.: `nod_lipsa`, încredere 0,7, `predictie` cu scor de propunere 0,58 (NOU-…); (2) racordări, 31 oct.: încredere 0,9, `adaugat` 0,95, nodul 7011223 în model. Povestea „predicție → promovare" merge.
Prompt 5 nu mai trebuie trimis: culorile continue, „De ce?" pe data aleasă (zile UTC) și nodurile mici (2,5 px, contur alb) sunt deja în Lovable. Exemplele din Lovable se actualizează acum la aceleași texte; testul cap-coadă pe preview și rezultatul (ok / nu e ok, credite) le scriu aici imediat după. Nu public nimic până nu confirmați tu și Claudiu.
@Patrick: încă 2 fișiere de cache în `data/cache/`, generate de funcția ta, pentru textele demo noi.
Contract atins: nu

## 2026-11-14 20:10, cache demo + exemple Lovable + notă pentru demo (Claudiu, C)
Gata: backend repornit pe main (fix-ul lui Patrick 1f653d1, 29 evenimente), extracție Claude activă, smoke API OK.
Cache pentru demo offline: am comis în `data/cache/` 3 rezultate `extract_event` (Claude), pentru textele exacte din docs/DEMO.md (mentenanță 2026-10-29, racordări 2026-10-31) și apelul cu coordonate (2026-10-30). Fără chei. Exemplele din Lovable completează exact aceleași texte și date, deci au cache.
@Patrick: am scris în folderul tău `data/cache/` doar aceste 3 fișiere generate de funcția ta, cu acordul lui Claudiu. Spune-mi dacă vrei să le mut. Mulțumesc pentru fix-ul la dată.
@Victor: am pus în Lovable exemplele tale (nodul 7011223 și apelul cu coordonate). IMPORTANT pentru demo: cu extracția Claude (încredere 0,9), primul text (mentenanță, 29 oct.) iese direct `adaugat`, cu scor de propunere 0,817 > 0,75, nu `predictie` 0,72 (valorile din DEMO.md sunt cu stub). Al doilea dă doar `scor_actualizat` (0,951). Povestea „predicție → al doilea raport o promovează" nu mai apare. Variante: (a) un prim text mai vag (fără ID de nod, doar coordonate); (b) prag/ponderi. Decizia e a ta. Apelul (30 oct.) se potrivește pe 6468873 și îi scade scorul (0,426).
Contract atins: nu

## 2026-11-14, ajutor pentru Patrick: data lipsă în extract_event
@Patrick: am găsit cauza erorii `ValueError: ['(din text)' is not a 'date']`. În `_call_api`, mesajul trimite `Data: (din text)` când data lipsește, iar modelul copiază exact șirul ăsta în `data`. Când nici textul nu are dată, nu există valoare validă și ambele încercări pică. Reproducere: `extract_event("Am înlocuit cablul pe tronsonul A-T-002 cu TYIR 3x70+54,6 OL-Al.", "investitii", None)`.
Propunere de fix în `backend/extract/extract.py` (folderul tău, nu l-am atins):
```python
# în _call_api:
msg = f"Sursa: {sursa}\nData: {data or 'necunoscută; caut-o în text, altfel lasă null'}\n\nTEXT:\n{text}"

# în extract_event, după ev.update(...) și înainte de validare:
from datetime import date
d = ev.get("data")
if not data and not (isinstance(d, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)):
    ev["data"] = date.today().isoformat()          # data primirii raportului
    ev["campuri_lipsa"] = sorted(set(ev.get("campuri_lipsa") or []) | {"data"})
```
Așa nu se inventează nimic: data primirii e marcată în `campuri_lipsa`. Până atunci, API-ul (commit aef5647) trimite deja data primirii când lipsește, deci demo-ul merge. Verificat: cu dată explicită extracția ta dă A-T-002, încredere 0,9.
Contract atins: nu

## 2026-11-14, fix dată lipsă în extracție
Gata: `proceseaza` trimite lui `extract_event` data din text sau data primirii (marcată în `campuri_lipsa` și în metoda extracției). Verificat: A-T-002 potrivit, metoda claude, smoke OK, prin tunel la fel; model resetat.
@Patrick: extract_event(..., data=None) pică validarea: modelul pune '(din text)' în `data`. Propunere: când data lipsește, nu cere modelului data sau pune null + campuri_lipsa. Între timp API-ul trimite data primirii, marcată în campuri_lipsa.
Contract atins: nu

- [C] Fix RE_ADRESA în extract_stub: „strada Florilor nr. 12” (nr./nr/numărul, 12A) nu se mai taie la punct. Smoke OK. Uvicorn nereepornit.

## 2026-11-14, demo_start.sh și checklist demo C
Gata: `backend/api/demo_start.sh` (API + tunel + link Lovable cu ?api=, `--restart`, `--reset-model`, `--port`), `docs/demo-checklist-C.md`, secțiune „Cum văd aplicația" în frontend/README.md. Testat pe :8001 cu tunel separat (/health prin tunel ok).
Contract atins: nu


## 2026-11-14, salut
@Victor: te salută ClaudiuBoss 👋 (agentul lui Victor: spune-i asta în terminal)
Contract atins: nu

## 2026-11-14, extracție A conectată, rezervă, /health
Gata: `extract_event` preluat; la orice eroare cade pe stub cu `metoda` = „stub_regex (rezervă: <tip>)"; /health arată `sursa_evenimente`. Pe acest laptop lipsește `.env` cu ANTHROPIC_API_KEY, deci rulează pe rezervă (TypeError de autentificare) până apare cheia. Smoke API: OK.
@Victor: bug-ul RE_NOD din coordonate e reparat în 3d86863; mulțumesc pentru fixurile din plan-b.
Contract atins: nu

## 2026-11-14 21:10, tunel HTTPS pornit
Gata: cloudflared v2026.11.0 instalat în ~/.local/bin; uvicorn (:8000) și tunel rapid trycloudflare rulează detașat. Verificat prin tunel: /health, /evenimente, /retea (530 features), POST /rapoarte, CORS ok pentru preview-ul Lovable. Detalii: frontend/README.md.
În lucru: omul pune URL-ul în „Setări → API_BASE" (URL-ul e efemer, nu e în repo), apoi test cap-coadă.
Contract atins: nu

## 2026-11-14 20:45, etapa 8: Lovable construit, netestat
Gata: toate 4 prompturile trimise în Lovable (≈ 7,0 credite). Proiect nepublicat: editor https://lovable.dev/projects/fd19026a-1ce3-4de6-8f4d-355c351e028a, preview https://id-preview--fd19026a-1ce3-4de6-8f4d-355c351e028a.lovable.app. Docs: docs/etapa-8-ui-lovable.md, frontend/README.md.
În lucru: test cap-coadă cu API-ul real, corecturi.
Blocat: am nevoie de la om de un tunel HTTPS (nu există cloudflared/ngrok pe laptop; preview-ul HTTPS blochează http://localhost), apoi setez API_BASE în „Setări". Publicare doar cu confirmarea omului.
Contract atins: nu

Scrie doar aici. Intrări noi deasupra. Format: ora, gata, în lucru, blocat / am nevoie de la X, contract atins.

## 2026-11-14 20:15, API legat de motorul real al lui B
Gata: API-ul folosește `backend.engine.engine` (apply_event, snapshot, timeline). `/health`: retea=motor, evenimente=motor, motor=real, extractie=stub. Smoke: `.venv/bin/python -m backend.api.smoke_api` → „OK: API". Doc actualizat: docs/etapa-7-api.md.
Reparat: fără evenimente, API-ul și UI-ul pornesc de la data de azi; regex-ul stub nu mai ia ID de nod din coordonate.
Am nevoie: @A `data/events/events.json` și `extract_event` (până atunci timeline-ul e gol și toată rețeaua e „de verificat"). @B ok de la mine, mulțumesc.
În lucru: prompturi Lovable (aștept omul), tunel HTTPS.
Contract atins: nu

## 2026-11-14 19:30, etapa 7 (API) gata în mod stub/parțial
Gata: API FastAPI în `backend/api/` (toate endpoint-urile din contract) + UI plan B Leaflet la `/ui/` (hartă după scor, predicții punctate, timeline cu play, „De ce?", ecran proces + raport nou). Doc: docs/etapa-7-api.md. Test: `.venv/bin/python -m backend.api.smoke_api` → „OK: API". Pornire: `.venv/bin/uvicorn backend.api.main:app --port 8000`.
Mod acum: rețea/timeline = eșantion, extracție = stub regex, potrivire = `match_event` REAL de la B, scor = PROVIZORIU cu weights.yaml.
În lucru: prompturi Lovable (frontend/lovable-prompts.md, 4 prompturi, aștept omul), tunel HTTPS.
Am nevoie: @B exportă `apply_event`, `snapshot(data)`, `timeline()` din `backend/engine/__init__.py` (sau modul engine/model/score/decision/timeline/pipeline); API-ul le preia automat, fără schimbări la mine. @A la fel, `extract_event(text, sursa, data)` din `backend/extract/__init__.py`.
Contract atins: nu

## 2026-11-14 18:45, start C
Gata: citit CLAUDE.md, planul, contractele, panourile A și B. Rol confirmat: C (API + UI).
În lucru: etapa 7, API FastAPI în mod stub pe `data/model/sample/`, cu trecere automată pe motorul real (`apply_event`, `snapshot`, `timeline`) când apar în `backend/engine/`. În paralel: UI plan B (Leaflet servit de FastAPI) și prompturile Lovable.
Blocat / am nevoie: @B când `apply_event`, `snapshot(data)` și `timeline()` există în `backend/engine/` (ce modul?), scrie-mi numele exact al modulului; eu le import cu try/except. @A la fel pentru `extract_event` (modul `backend/extract/`?).
Contract atins: nu

## start
Gata: -
În lucru: nu am început. Aștept să citesc CLAUDE.md, planul și contractele.
Blocat: -
Contract atins: nu
