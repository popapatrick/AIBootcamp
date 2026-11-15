# Panou laptop B

Scrie doar aici. Intrări noi deasupra. Format: ora, gata, în lucru, blocat / am nevoie de la X, contract atins.

## 2026-11-15, plan sesiunea 4: accent pe căutarea pe stradă (Victor, B)
Victor a cerut accent pe cazul „stradă + indiciu parțial” (ex. „lângă nr. 15”): modelul caută pe stradă, nu așteaptă coordonate exacte. Planul are acum D11 și V6 rescris: indiciul extras de AI (`numar`, `langa`, `vizavi`, `intre`, `dupa`, `capat`, `colt`, `element`), fereastră de căutare pe stradă (ancore din rapoarte anterioare sau convenția de numerotare, par/impar), apoi căutarea elementelor din fereastră (1 candidat = potrivit, 2–4 = predicție cu alternative, 0 = element nou sau „de verificat”). Pasul nou `cautare_strada` în `pasi`; vizualizare în P3; primul card de pe intro e acest caz; 8 cazuri golden.
@Claudiu: în textele tale (C4), cel puțin o treime doar stradă + indiciu, fără coordonate.
Contract atins: nu

## 2026-11-15, plan sesiunea 4 (prototip gata de prezentat), PROPUNERE (Victor, B)
Gata: `docs/plan-sesiune-4-prezentare.md`, după cererea lui Victor + nota „Modificări” a lui Claudiu. Măsurat pe main: 620/630 elemente de start la 0,72 (scăderea în timp), elementele noi la 0,96 fără coordonate, 8/29 evenimente `neaplicat`. Decizii luate cu Victor (D1–D10): doar Lovable pentru UI, pagină de intro separată, `in_model` ascuns în UI, analiză hartă pe graful de străzi OSM local, 4 benzi de culoare (verde ≥0,80 / galben / portocaliu / roșu <0,40), GIS t0 0,95 cu scădere lentă, plafon de acuratețe după sursa locației, traseul generat oprit, doar 3 butoane de echipă, „verificat de om” = 1,0 din panoul oricărui element. Patrick nu participă: backend-ul lui trece la B, `data/reports/` la C.
În lucru: nimic până la aprobare. Primul pas după aprobare: contract `sesiunea 4` (Faza 0) + 5 schimbări OpenSpec + CLAUDE.md.
@Claudiu: citește planul (secțiunile 6, 7, 8 sunt ale tale); nu începe cod până nu apare contractul în `git log -- contracts/`. Spune-mi pe board dacă ceva din P1–P3 (Lovable) nu se poate face în Lovable sau dacă estimarea de 15–20 credite e greșită.
Contract atins: nu

## Ajutor pentru Claudiu: timeline derulabil, ciornă de prompt Lovable (Victor, B)
@Claudiu: am verificat planul timeline-ului față de ce ai făcut (C8, sesiunea 3). Are sens și nu strică nimic din C8 dacă păstrăm comutatorul de scenariu, badge-urile de decizie, marcajele pe `eticheta`, halo-ul verde/galben și „De ce?" pe element; se schimbă doar interacțiunea: panou vertical derulabil în loc de Play + slider. Ți-am scris o ciornă de prompt în `docs/draft-prompt-lovable-timeline-derulabil.md` (7 puncte, ~4-6 credite, un singur mesaj), cu ce rămâne neschimbat, verificarea și compatibilitatea. Ce ai de făcut: (1) sarcina 2.1: `GET /evenimente` (și `?scenariu=extrem`) să treacă `schimbari`, `pasi`, `eronat_prototip` neatinse, plus test în smoke_api; (2) citește ciorna, ajusteaz-o la Lovable-ul tău (mută-o în `frontend/` ca `lovable-prompt-timeline-derulabil.md`); (3) NU o trimite până nu decide omul (cost de credite). Plan-B (Leaflet) rămâne cu Play ca rezervă, nu e nevoie să-l schimbi dacă nu apuci.
Întrebări către tine: ai deja în preview intrările de timeline cu `eticheta`/`decizie` funcționale? Dacă ai ceva care contrazice ciorna (de ex. axa de marcaje pe slider pe care o scoatem), spune.
Contract atins: nu

## Timeline derulabil: partea de motor gata, UI pentru C (Victor, B)
Gata (la cererea omului): `timeline()` / `GET /evenimente` (și `?scenariu=extrem`) întoarce acum pe fiecare intrare `schimbari[]` (scor înainte -> după), `pasi[]` („De ce?") și `eronat_prototip`. Contract aditiv în `interfaces.md`; test în smoke_sesiune2 (65); doc `docs/etapa-25-timeline-derulabil.md`; OpenSpec `timeline-derulabil` (proposal, design, spec, tasks).
@Claudiu: decizii luate cu omul: panou vertical lateral în loc de Play și bara de dată; scroll mută harta automat (debounce, cache pe dată); fiecare intrare = dată, etichetă, decizie, scor înainte -> după, elemente atinse evidențiate pe hartă, „De ce?" la clic (din `pasi`, fără alt apel); scenariul extrem implicit. Sarcinile tale sunt în `openspec/changes/timeline-derulabil/tasks.md` (2.1, 3.1-3.3, 4.1): un singur prompt Lovable grupat, netrimis până decide omul; plan-B ca rezervă.
Contract atins: DA (aditiv, `interfaces.md`)

## Verificare după update-urile A și C (Victor, B)
Gata: trase `main`; `scripts/verifica_tot.sh` TOT VERDE; banca pe golden 19/20 (pe cache AI, fără CLI). Singura diferență `g-06-ortografie`: ortografia cere `ai_cli` la geocodare (cache-ul AI al geocodării e doar în proces), deci fără login iese `neaplicat`, cu `ai_cli` iese predicție 0,477. E comportamentul corect; @Patrick: golden-ul g-06 să accepte `neaplicat` fără AI sau marchează-l „doar cu ai_cli". Referința de aur reîmprospătată: EV-023 0,886 -> 0,891 (generatorul de trasee nou al lui A), nicio decizie schimbată.
Nu am nevoie de nimic de la voi acum; tag-ul `logic-v1` rămâne.
Contract atins: nu

## Banca cu AI real (ai_cli) pe golden: 15/20 (Victor, B)
Login `claude` făcut; `cli_ai.stare()` = autentificat, toate cele 20 de cazuri au ieșit `ai_cli` (nu regex). Logica motorului e ok; diferențele rămase sunt de extracție și de golden.
@Patrick (prompt, A2): textele de tipul „stalp nou montat la <coordonate>" (g-02, z-02, z-03, z-04, z-07) ies `activ_inlocuit`, nu `nod_lipsa` (în regex ieșeau `nod_lipsa`): promptul trebuie să spună că un stâlp NOU montat/necartat = `nod_lipsa`, `activ_inlocuit` doar când textul zice că a înlocuit/demontat unul vechi. Asta face ca z-04/z-07 (2,9 km și centru) să iasă `neaplicat` în loc de predicție. g-06 (ortografie) iese acum predicție 0,477 (AI alege strada), golden zice `de_verificat`: aliniază golden-ul la `predictie`. g-07/g-08/r-02: golden de aliniat (vezi mesajul anterior).
Cache-ul nou generat de rularea mea nu e comis (data/cache/ neurmărit pe laptopul B); îl umple Patrick din `fill_cache` după fixul de prompt.
Contract atins: nu

## Răspunsuri B7 și tag logic-v1 (Victor, B)
@Claudiu: (1) `g-05` era în motor (stradă fără număr = precizie ±150 m, peste raza de 15 m, nu se mai lipește pe `SIM-L30`: acum `predictie` ~0,58 ca element nou); trage `main`. (2) `g-07/g-08` (reper, stradă necunoscută): corect e `neaplicat` fără nivel, nu `de_verificat` (nu inventăm locație); golden-ul trebuie aliniat (cerere către Patrick). (3) `r-02`: treapta 1 e corectă cu nodurile SIM-* în rețea; golden se regenerează pe `GridModel().net`. (4) `detalii.geocodare` și `trace_sursa` rămân în pașii `geocodare`/`trace`, nu în Event-ul extracției (extracția rămâne a lui A, motorul nu rescrie evenimentul). (5) `api.openapi.yaml` descrie acum `trace_params`, `/geocodeaza`, `/reguli`.
@Patrick: (1) golden: `g-07`/`g-08` asteptat `decizie: neaplicat` (fără `nivel`); `r-02` treapta 1 (sau alege coordonate care dau treapta 2 pe rețeaua cu SIM-*). (2) `genereaza_traseu` cu `acoperire 1.0`, zgomot 5, oprire 12 min: din 60 de seed-uri, 7 ies `ambiguu` (a doua „oprire” de ~5 min) și 1 `fara_opriri` (ex. seed `EV-LIVE-009`, punctul 44.2849717, 26.0601908): generatorul trebuie să garanteze oprirea de `durata_oprire_min` în fereastra de 60 min și mersul să nu producă o a doua oprire; teste pe 100 de seed-uri.
Tag: `logic-v1` pe commit-ul acestui mesaj (`scripts/verifica_tot.sh` verde; banca: 15/20, restul = golden de aliniat și texte care cer AI). După tag, schimbări de cod în motor doar prin cerere aprobată (`docs/cerere-logica.md`); valorile se schimbă cu `reglaj:`.
Contract atins: nu

## B7 aproape: golden rulat, regulă nouă, cereri către A și C (Victor, B)
Gata: banc pe `data/golden/` (fără AI, doar regex): 8/20 ok. Reparat în motor: o locație din adresă mai imprecisă decât raza de potrivire (15 m) nu se mai lipește pe un element existent (stradă fără număr -> element nou/`nepotrivit`); smoke_sesiune2 62. `data/golden/calibrare-referinta.json` scris (referința pentru `verifica_reglaje`). DEMO.md are secțiunea Sesiunea 3.
@Claudiu: (1) banca compară `eronat_prototip: false` cu valoarea lipsă și dă „diferit" la 10 cazuri; tratează lipsa ca false (la fel `slaba`). (2) pe laptopul meu nu e login `claude`, deci banca a mers pe regex: rulează banca tu cu `ai_cli` și scrie ce rămâne diferit.
@Patrick: (1) `r-02-treapta2` iese treapta 1 pentru că rețeaua are acum și cele 55 de noduri SIM-*; regenerează golden-ul racordare pe `GridModel().net` (nu pe rețeaua fără SIM). (2) `g-06-ortografie` și `r-07` cer extracția AI; verifică-le tu cu `ai_cli`.
Tag `logic-v1`: îl pun când banca pe AI iese fără diferențe de logică (rămân doar cele de extracție, documentate).
Contract atins: nu

## B7 parțial: calibrare geocodare pe geo-test.json (Victor, B)
Gata: măsurat pe `data/reports/geo-test.json`; reglaj în `weights.yaml`: `geocodare.acuratete.strada_numar` 0,55 -> 0,45, `precizie_numar_m` 25 -> 200 (eroarea reală 143-245 m). 0 decizii schimbate pe cele 29 de evenimente. Tabel în `docs/calibrare.md`.
@Patrick (A1): (1) intersecțiile gt-06/gt-07 ies la 506 și 104 m de așteptat (tol. 30 m) și cad pe stradă (acuratețe 0,40); verifică parsarea „colț cu"/„X și Y". (2) gt-12 (ortografie) dă un fals pozitiv la 1,9 km fără AI, la fel „Calea Victoriei 10 București" -> „Strada București" (semnalat de Claudiu): cere ca toate cuvintele numelui, nu doar unul, să se potrivească. (3) A6 `data/golden/` e blocul meu pentru B7/tag.
Contract atins: nu (valori în weights, limite lărgite)

## B3 complet: puncte simulate încărcate în rețeaua de start (Victor, B)
Gata: `network.incarca_puncte_simulare` încarcă `data/simulare/puncte-simulare.json` (A4, format respectat) în `GridModel()`; 55 de noduri SIM-* cu `origine: retea_start`, în zonă. smoke_sesiune2 60, `scripts/verifica_tot.sh` TOT VERDE, calibrarea neschimbată. Contract: openapi actualizat (trace_params, /geocodeaza, /reguli).
@Patrick: mulțumesc pentru A4. @Claudiu: `GET /retea` conține acum 320 de noduri; harta arată casele/stâlpii SIM-*.
Rămân la mine: B7 (după A6 `data/golden/`: calibrare pe `geo-test.json`, referință de aur, tag `logic-v1`) și B8 (DEMO.md, docs finale).
Contract atins: DA (openapi, commit `contract:` separat)

## B6 gata: unelte de reglaj + răspunsuri către Claudiu (Victor, B)
Gata: `python -m backend.engine.verifica_reglaje` (limite din `contracts/weights.limits.yaml`, diferență de calibrare, smoke-uri, linie pentru board), `scripts/verifica_tot.sh` (TOT VERDE acum), `docs/cerere-logica.md`. Ghidul tău `etapa-23-reglaje.md` e deblocat (am șters nota „depinde de B6").
@Claudiu răspunsuri: (1) `cer-02` „casa lângă nodul 7101969": rămâne predicție cu lanț de 1 stâlp; corectează `asteptat` (nu există „actualizare directă" în regulile de acum). (2) geocodarea e acum în motor (B2): pasul `geocodare` apare la rapoartele cu adresă și fără ID/coordonate/clic/operator. (3) contractul: `zona` e în `GET /retea` (nu `/stare`), actualizez `api.openapi.yaml` cu `trace_params`, `/geocodeaza`, `/reguli`. (4) Trace-ul real al regex-ului (0,774 -> in_model): acceptat, e semnal real de pe tabletă; cu plafonul de standardizare (coordonate 0,9) nu crește peste. (5) DEMO.md: aliniez la 0,738 în B8. Banca poate citi `modificari[i].origine`, `predictie.slaba/treapta`, `eronat_prototip` din trace (sus), cum faci deja.
@Patrick: A6 (`data/golden/`) e singurul lucru pe care îl aștept pentru B7; format propus de Claudiu în board (`{id, sursa, text, data?, asteptat?}`).
Contract atins: nu (openapi urmează într-un commit `contract:`)

## B5 gata: racordare cu rezerve (Victor, B)
Gata: cererea de racordare nu mai e `neaplicat` din lipsă de date: locația (coordonate > clic > adresă > operator), lanț pe trepte 1-4 (A5), scor cu `factor_*` pe treaptă, predicție slabă (`predictie.slaba`, `treapta`), casa rămâne pe hartă. `neaplicat` doar fără locație sau în afara zonei. smoke_sesiune2 58. Doc: `docs/etapa-22-racordare-cu-rezerve.md`.
@Claudiu: `predictie.slaba` și `predictie.treapta` sunt în snapshot și în modificări; pasul „predicție" are `treapta`.
Contract atins: nu

## B2 + B4 gata: geocodare în potrivire și traseu generat în motor (Victor, B)
Gata: motorul apelează `backend.geo` pentru adresă (pas „geocodare", `metoda: adresa`), plafonează `incredere_extractie` după localizator, generează traseu simulat la raport (`factor_trace`, pas „trace", `trace_sursa: simulat`, `detalii.trace_params`). smoke_sesiune2 52, smoke_engine 36, calibrare neschimbată. Docs: `etapa-18-geocodare-adresa.md`, `etapa-19-traseu-generat.md`.
@Claudiu (C1): expune pasul „geocodare" și „trace" din StepTrace (nu mai sunt la indexul 1; caută după `nume`), `detalii.geocodare`, `detalii.trace_sursa`, `trace_params` din `POST /rapoarte`, `origine`, `eronat_prototip`, `zona` în `GET /retea`.
@Patrick: mulțumesc pentru A1, A3, A5. A4 (puncte simulate, format în intrarea B3) și A2/A6 rămân.
Contract atins: nu

## B3 (parțial): origine + scor inițial 0,90 (Victor, B)
Gata: `origine` (`retea_start` | `generat_model`) în snapshot și StepTrace, `predictie.origine`, scor inițial 0,90. Calibrare: deciziile neschimbate. Rămâne încărcarea `puncte-simulare.json` după A4. Doc: `docs/etapa-21-retea-start-origine.md`, `docs/calibrare.md`.
@Patrick: A4 poate începe; format cerut pentru `data/simulare/puncte-simulare.json`: `{"noduri": [{"id": "SIM-001", "lat": .., "lon": .., "serie": "serie 5"|"serie 7"}], "tronsoane": [{"id": "SIM-L1", "capete": ["id1","id2"], "puncte": [[lat,lon],...], "categorie": "aerian"}]}`; eu le încarc cu `origine: retea_start`.
@Claudiu: `origine` e în snapshot (`GET /retea`); expune-l fără transformări.
Contract atins: nu

## B1 gata: safeguard 3 km (Victor, B)
Gata: `backend/engine/zona.py` (`zona_ok(lat, lon, net, cfg)`), aplicat în potrivire, mutare_fire și cerere_racordare; punct în afară = `eronat_prototip`, neaplicat, cu motiv. smoke_sesiune2 36, calibrare neschimbată. Documentat în `docs/etapa-20-safeguard-zona.md`.
@Patrick: în `backend/geo` și `backend/trace` folosește `from backend.engine.zona import zona_ok` și întoarce `in_afara_zonei`. Contractul (B0) e pe main, poți implementa.
@Claudiu: `eronat_prototip` e în StepTrace și `zona` trebuie pus în `GET /retea` (C1).
În lucru: B2 (geocodare în potrivire, după A1) și B3.
Contract atins: nu

## Sesiunea 3 pornită: planul e pe main (Victor, B)
Gata: `docs/plan-sesiune-3-logica.md` (sarcini explicite A1–A7, B0–B8, C1–C5, ordine, dependențe, metoda pentru schimbări mici) și 6 features OpenSpec noi: geocodare-adresa-acuratete, traseu-generat-din-raport, safeguard-zona-prototip, retea-start-origine-model, racordare-fara-neaplicat, reglaje-logica-fara-cod. CLAUDE.md și fișierele agenților actualizate.
@Patrick @Claudiu: faceți `git pull --rebase origin main`, citiți planul și `openspec/changes/<feature>/specs`. Până apare commit-ul `contract:` (pasul 0, în curând), pregătiți doar date și scheme: A6/A4 (Patrick), schelet banc_logica (Claudiu). Geocodare doar din cache OSM local + AI, fără cheie. Schimbări mici: `reglaj:` sau cerere cu `@Victor`.
Contract atins: DA, commit `contract:` B0 (aditiv): adresa_structurata, detalii.geocodare/trace_params/trace_sursa, origine, predictie.slaba/treapta, eronat_prototip, zona în GET /retea, weights (zona, geocodare, standardizare, trace_generat, initial_retea_start, racordare.*). Acum A și C pot implementa.

## Schimbarea e acum și în fișierele agenților (Victor/B)
@Patrick @Claudiu: am adăugat în `.claude/agents/patrick.md`, `victor.md` și `claudiu.md` secțiunea „Standardizare cu AI, fără cheie API" (ordinea cache -> `ai_cli` -> `ai_api` -> regex ca rezervă, `claude auth login` pe laptopul demo, model pe dificultate), plus câte o regulă specifică rolului. Faceți `git pull --rebase origin main` înainte de următorul bloc de lucru și citiți-o; regula e și în `CLAUDE.md`.
Contract atins: nu

## STANDARDIZARE CU AI ACUM, fără regex și fără cheie: `ai_cli` (Victor/B, la cererea lui Victor)
@Patrick @Claudiu: Victor nu vrea regex ca cale de standardizare. Am implementat acum **standardizarea cu AI prin Claude Code headless (`claude -p`, model Haiku), din abonament, fără cheie API**. Ordinea pentru un text: cache (`ai_cache`) -> Claude headless (`ai_cli`) -> API cu cheia demo (`ai_api`, doar `EXTRACT_ALLOW_API=1`) -> regex (ultima rezervă). Rezultatul `ai_cli` se scrie în cache.
Am atins folderele voastre, la cererea omului, cu schimbări mici (commit `[B]` separat de ale voastre):
- @Patrick: fișier NOU `backend/extract/cli_ai.py` + test `test_cli_ai.py` + ~8 rânduri în `extract_event_cu_metoda` (după cache miss, înaintea gate-ului API) + secțiune în `docs/etapa-3-extractie.md` și README. Nu am schimbat cheia de cache, promptul sau `fill_cache`. Verifică că ți se potrivește și ajustează cum vrei.
- @Claudiu: în `pipeline.py` folosesc `extract_event_cu_metoda` (ia `metoda_cod` direct din extracție; rămâne calea veche la ImportError), iar `sources.extractie_cod()` întoarce `ai_cli` când Claude headless e autentificat. Etichete în UI: `ai_cli` și `ai_api` = „AI (live)", `ai_cache` = „AI (cache)", `regex` = „Regex (simplificat)" (rezervă). Butoanele C5-C7: textele lor trec acum prin AI (`ai_cli`), deci regex-ul tău pentru ele rămâne doar rezervă; reia testul trace-1 (pe AI era 0,71, predicție; întrebarea ta cu regex 0,774 își pierde rostul).
- **Pe laptopul demo, o singură dată:** `claude auth login` (se deschide browserul, abonament). Verificare: `claude auth status` -> `loggedIn: true` și `/health` -> `extractie_cod: ai_cli`. Eu am testat cu un binar fals (autentificare, ai_cli, cache, dezactivare, plus API cap-coadă); apelul real nu l-am putut rula pentru că binarul de aici nu e autentificat. Victor trebuie să facă login ca să-l vedem real.
Contract atins: da, aditiv (`metoda_cod` primește `ai_cli`).

## ANUNȚ: cheie DEMO doar în ziua demo-ului + semne în UI pentru regex vs AI (Victor/B, la cererea lui Victor)
@Patrick @Claudiu: Victor alocă **o cheie demo doar când implementăm extracția live** (ziua demo-ului). Până atunci nimeni nu are cheie și nimeni nu apelează API-ul; mesajul anterior rămâne valabil, cu o ajustare: **nu scoateți `_call_api`**, ținut în spatele `EXTRACT_ALLOW_API=1` (oprit implicit), ca să se poată porni rapid cu cheia demo. Victor va anunța în `board/` când și cum se pune cheia (local, în `.env`, nu în git).
Cerere nouă: UI-ul să anunțe clar când extracția e regex și când e AI, și când un element e „predicție AI". Contract (aditiv, în `contracts/interfaces.md`): `metoda_cod` în pasul `extractie` și în `/health`: `ai_api` | `ai_cache` | `regex`.
- @Patrick: `extract_event` întoarce/marchează `metoda_cod`: `ai_cache` la cache hit, `ai_api` la apel API (când e permis), iar cache miss fără API ridică `CacheMiss` (C cade pe `regex`). Pune-l în ieșire sub `detalii.metoda_extractie` sau ca al doilea rezultat, cum e mai curat pentru tine; spune în board formatul ales.
- @Claudiu: (1) API: `pasi[extractie].metoda_cod` și `/health.extractie_cod` cu cele trei valori (`ai_api` dacă apelul s-a făcut, `ai_cache` dacă vine din cache, `regex` dacă e stub); păstrează și textul uman de acum. (2) Lovable, un prompt mic (poate intra împreună cu C5-C7): în „Proces raport", la pasul Extracție, un semn colorat: „AI (cache)" / „AI (API)" / „Regex (simplificat)", cu tooltip „Regex = extracție simplă, fără AI, pentru text nou fără cache"; în colțul de stare un semn global cu modul curent. Pe hartă și în panoul „De ce?", elementele cu `nivel == "predictie"` primesc eticheta „Predicție AI" plus metoda din `predictie.metoda` (traseu_strada_osm, lant_racordare, zona_mutata, pozitie_din_trace, propunere_proprietate) și scorul; cele aplicate din rapoarte rămân „Din raport", iar cele cu `confirmat_de == "om"` au „Confirmat de om". Fiți onești în tooltip: extracția folosește AI, predicția vine din scor plus străzi OSM.
Contract atins: da, aditiv (`metoda_cod`, în `contracts/interfaces.md`).

## ATENȚIE TUTUROR: fără cheie API, extracția prin subagenți Haiku (decis de Victor)
@Patrick @Claudiu: cheia API nu se mai folosește (dă probleme). Regula e în `CLAUDE.md`, secțiunea „Fără cheie API; model pe dificultate". Pe scurt: (1) nu apelați API-ul și nu puneți chei în `.env`; (2) textele devin evenimente prin **subagenți Claude Code cu modelul Haiku** (din abonament); (3) la rulare extracția e **cache + stub regex**; (4) model pe dificultate: Haiku pentru extragere/texte dummy, Sonnet pentru cod, model mare doar pentru bug care persistă după 2 încercări sau schimbări de contract, cu acordul omului.
- @Patrick (A, cere schimbări în `backend/extract/`, folderul tău): (a) `extract_event` să NU mai apeleze API-ul: la cache hit întoarce evenimentul, la cache miss ridică o excepție clară (`CacheMiss`); API-ul lui C o prinde deja și cade pe stub. Păstrează `_call_api` doar în spatele variabilei `EXTRACT_ALLOW_API=1` (oprit implicit) sau scoate-l. (b) Cheia de cache să nu mai depindă de `MODEL` (acum diferă între OpenRouter și Anthropic): folosește o etichetă fixă (ex. `agent-haiku`) în hash. Asta invalidează cache-ul o dată, deci regenerezi totul. (c) Unealtă nouă `python -m backend.extract.fill_cache`: `--lipsa` listează textele (exemple-dummy.json, rapoartele din `data/reports/`, textele de demo din `docs/DEMO.md`, apelurile/trace-urile) fără intrare în cache, cu sursa și data; `--import fisier.json` ia rezultatele agenților (listă de {text, sursa, data, event}), le validează pe schemă (cu `_normalizeaza`, `_data_valida`, `_sectiune`) și scrie intrările în cache. (d) Lansează tu subagenți Haiku (Agent cu `model: haiku`) care primesc `SYSTEM` din extract.py + schema + textul și returnează JSON-ul; împarte textele în loturi; importă. (e) Regenerează tot cache-ul (rapoartele pentru `events.json` rămân cele din fișier, nu se schimbă) și comite-l. (f) Documentează în `docs/etapa-3-extractie.md` și `backend/extract/README.md`, inclusiv că regulile de prompt (stâlp necartat = nod_lipsa) trebuie verificate acum cu un agent Haiku real, nu cu mock.
- @Claudiu (C, în `backend/api/`): (a) `extract_func()` și `health`: `extractie` să arate `cache + stub` (nu „claude"/„cheie API lipsă"); scoate dependența de `ANTHROPIC_API_KEY` din `_are_cheie()`; (b) la cache miss fallback-ul pe stub rămâne, dar marchează în răspuns `metoda_extractie: "stub_regex (text nou, fără cache)"` ca UI-ul să poată arăta „extracție simplificată"; (c) după ce Patrick regenerează cache-ul, refă testul cap-coadă pe textele de demo (trebuie să iasă din cache, nu stub) și actualizează `docs/demo-checklist-C.md` (scoate „cheie în .env"); (d) în Lovable nu e nimic de schimbat (UI-ul vorbește doar cu API-ul tău).
- Eu (B): motorul nu apelează API-ul; nu schimb nimic acolo. Am actualizat `CLAUDE.md`, `PLAN-prototip.md` și `docs/DEMO.md` (risc: text nou live iese cu stub; folosiți textele pregătite).
Contract atins: nu

## Documentația înainte de commit-ul final: regulă nouă și ce lipsește (Victor/B)
@Patrick @Claudiu: am adăugat în `CLAUDE.md` („Documentație", „Regula de final") ce trebuie să existe înainte de orice commit care încheie un task: doc de etapă în `docs/`, README de folder la zi, docstring la funcțiile publice, actualizat `DEMO.md` / `frontend/README.md` / `contracts/interfaces.md` unde s-a schimbat comportamentul. Abia apoi bifezi sarcina în OpenSpec. Un task bifat fără documentație se consideră nebifat. Dacă un document lipsește, îl creezi tu înainte de push-ul final.
- @Patrick: verifică (A8) că `docs/etapa-10`, `etapa-12` (completat cu EV-X11/X12), `etapa-13`, `etapa-16` sunt la zi cu ce ai schimbat azi (promptul `nod_lipsa` pentru stâlp necartat, `mut-01`), că `backend/extract/README.md` menționează regulile noi și că `docs/etapa-3-extractie.md` are secțiunea cu tipurile noi (mutare_fire, cerere_racordare, decizia omului). Notează în doc că regula nouă din prompt e verificată doar cu mock și că cache-ul Claude trebuie regenerat.
- @Claudiu: lipsește `docs/etapa-11-interfata-rapoarte.md` (interfața Lovable: cele 4 butoane, Show pipeline, Acceptă/Respinge, cerere racordare, fire mutate, trace, încărcare scenariu: ce face fiecare, prompturile trimise, credite folosite, cum se verifică pe preview). Completează `frontend/README.md` cu ecranele noi și `docs/demo-checklist-C.md` după repetiție. Menționează în doc că cache-ul Claude din `data/cache/` trebuie regenerat după schimbarea promptului lui Patrick.
- Eu (B): documentația mea e completă (`etapa-5` secțiunea Sesiunea 2, `etapa-9`, `etapa-14`, `etapa-15`, `calibrare`, `DEMO`, README în `backend/engine` și `data/model`).
Contract atins: nu

## Răspuns pentru C: racordare 0,738 (Victor/B)
@Claudiu: ai dreptate, cu extracție 0,7 iese `predictie` 0,738 (pragul e 0,75); cu formular și încredere 0,9 iese `adaugat` ~0,84. Am aliniat `docs/DEMO.md` (nu mut pragul, ca să rămână aceleași ponderi pentru tot sistemul). Pentru demo: cererea de la apel (0,64) și cea de la racordări (~0,74) sunt ambele predicții, iar „Acceptă" din UI le aplică. Rest verificat: smoke engine 36, sesiune2 23, API OK pe main (b28383d).
Contract atins: nu

## B5-B8 gata + analiză a ce au făcut ceilalți (Victor/B)
Pe main: `mutare_fire` (zonă „de verificat" + traseu propus pe străzi), `activ_demontat` (scos_din_uz doar cu 2 echipe și scor peste prag), val de apeluri (agregare + plafon), locația din trace (apelează `backend.trace`), `cerere_racordare` (apelează `backend.racordare`, stâlp cu stâlp acceptabil), `engine.aplica_decizie`, `engine.model_scenariu("extrem")`. Detalii: `docs/etapa-15-motor-sesiune2.md`; demo: `docs/DEMO.md` (secțiunea Sesiunea 2). Teste: `smoke_sesiune2` 23, `smoke_engine` 36, restul OK.
@Claudiu: (1) `model_scenariu("extrem")` există; poți înlocui `sources.model_extrem()` (ridică FileNotFoundError dacă lipsește fișierul). (2) Timeline are acum `tip` și `eticheta` (mutare_fire | demontat | val_apeluri | racordare | decizie_om | tipul evenimentului): folosește-le în loc de EV-X01..X10. (3) `api.openapi.yaml` corectat: `scenariu` ca parametru de query pe `/retea` și `/evenimente`; decizia are 409/404/422/501. (4) Snapshot are `verificat_recent` (bool, din `scor.verificat_recent_zile` = 30 în weights.yaml); folosește-l pentru haloul verde, nu 45 de zile; `confirmat_de == "om"` = plin cu marcaj. (5) Nivel nou `scos_din_uz` (gri, tăiat). (6) StepTrace: pas `trace` înaintea `potrivire` (trace tabletă), `potrivire` cu `status: zona` la mutare_fire. (7) `smoke_api` pe laptopul meu pică la decizia omului, pentru că cu extracția stub apelul „lipsește un stâlp” (apel_client) iese avarie pe un element existent, nu predicție. Cu Claude iese nod_lipsa. Fă testul independent de extracție (de ex. un Event nod_lipsa trimis direct la `apply_event` pentru pregătire) sau sare peste dacă `extractie` e stub.
@Patrick: ți-am rulat scenariul extrem: X01-X03 (ramura), X04/X05 (demontat: scos_din_uz la X05), X07-X10 (val de apeluri) merg. Lipsește cazul **sens giratoriu**: te rog adaugă în `events.extreme.json` (A6b) un eveniment `mutare_fire`, `echipa_sursa` mentenanta, `status: semnalat`, `detalii: {"centru": {"lat": 44.2830448, "lon": 26.0636533}, "motiv_mutare": "sens_giratoriu"}`, `referinta.coordonate` = același centru, `data` ex. 2026-11-06 (înainte de X07), `text_original` cu textul raportului (și raportul .txt + index.json); apoi un `verificare` executat (tableta, 2026-11-08) pe unul dintre nodurile marcate (ex. 6513200, 7824201, 7313134) ca să se vadă revenirea la verde. Nu adăuga decizii `om_teren` în fișier: omul le dă din UI. Praguri hardcodate din A3/A4: le las așa, nu contează la demo.
Contract atins: da, aditiv (timeline `tip`/`eticheta`, openapi, `verificat_recent`, `scos_din_uz`), în `contracts/`.

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
