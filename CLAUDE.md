# CLAUDE.md: reguli pentru toți agenții

Proiect: prototip „A grid model that keeps itself up to date" (hackathon PPC, Challenge 2). Planul complet e în `PLAN-prototip.md`. Răspunde în română. Datele sunt FICTIVE (rețea demonstrativă); nu se pun date reale PPC în repo.

## Rolul tău
Roluri: A = Patrick, B = Victor, C = Claudiu (agenți `.claude/agents/patrick.md`, `victor.md`, `claudiu.md`; panouri `board/Patrick.md`, `board/Victor.md`, `board/Claudiu.md`). Citește fișierul local `.laptop` (conține A, B sau C). Dacă lipsește, întreabă omul și creează-l. Apoi urmează agentul tău: `.claude/agents/patrick.md`, `victor.md` sau `claudiu.md`.

## La începutul fiecărui bloc de lucru
1. `git pull --rebase origin main`
2. Citește `board/*.md` (în special întrebările către tine, marcate `@A`/`@B`/`@C` sau `@Patrick`/`@Victor`/`@Claudiu`) și `git log --oneline -20 -- contracts/`.
3. Alege următoarea etapă din `PLAN-prototip.md` care e a ta.

## Reguli git
- Scrii DOAR în folderele rolului tău (tabel în `PLAN-prototip.md`, 10.1). Dacă ai nevoie de ceva în alt folder, scrie în `board/<laptop-tău>.md` cu `@X`.
- Commit-uri mici, minimum la ~20–30 min, cu prefix: `[A]`, `[B]`, `[C]` sau `contract:`.
- Push direct pe `main`. Înainte: rulează smoke test-ul sau pornește serverul. Nu împinge cod care strică `main`.
- Dacă push e respins: `git pull --rebase origin main`, rezolvă, push. Niciodată `--force`.
- Excepție: commit `reglaj:` poate schimba DOAR valori numerice în `contracts/weights.yaml`, după `python -m backend.engine.verifica_reglaje` (vezi „Sesiunea 3"). Nu atinge alte fișiere în același commit.
- Schimbare de contract = doar commit `contract:`, anunțat în `board/`, cu `contracts/interfaces.md` actualizat în același commit.
- Secrete: nu scrie chei în fișiere, commit-uri sau chat. **Cheia API NU se mai folosește** (vezi „Fără cheie API" mai jos).

## Documentație (obligatorie)
O etapă nu e terminată fără `docs/etapa-N-<nume>.md` (ce face, cum se rulează/verifică, intrări/ieșiri, decizii, limite, ce trebuie să știe ceilalți), plus README în folderele tale și docstring la funcțiile publice. Vezi secțiunea 12 din plan.

**Regula de final (înainte de ORICE commit care încheie un task sau o etapă):**
1. Există documentul etapei în `docs/` (sau secțiunea nouă într-unul existent): ce face, cum se verifică (comanda exactă și rezultatul așteptat), intrări/ieșiri, decizii, limite, ce trebuie să știe ceilalți.
2. Folderul tău are `README.md` actualizat cu fișierele/funcțiile noi; funcțiile publice noi au docstring.
3. Dacă ai schimbat un comportament descris în `docs/DEMO.md`, `frontend/README.md` sau `contracts/interfaces.md`, ai actualizat și acelea.
4. Abia apoi bifezi `- [x]` în `openspec/changes/<feature>/tasks.md` și scrii intrarea din `board/`. Task bifat fără documentație = nebifat.
5. Dacă un document lipsește, îl creezi tu în același commit sau într-unul imediat următor, înainte de push-ul de final al sesiunii. Nu lăsa documentația „pe mai târziu".

## Panou
Scrie în `board/<laptop-tău>.md`, noi intrări deasupra: ora, gata, în lucru, blocat / am nevoie de la X, contract atins. Citește panourile celorlalți.

## Efort și model
Dacă un bug nu se rezolvă după 2 încercări sau o eroare se repetă, spune explicit omului și în `board/` că „poate trebuie ridicat efortul sau modelul", cu motivul. Nu insista la nesfârșit.

## Fără cheie API; model pe dificultate (decis de Victor, 14 nov.)
- **Nu mai folosi cheia API** (nici OpenRouter, nici Anthropic). Cheia dă probleme; folosim abonamentul. Nu pune chei în `.env`, nu rula cod care apelează API-ul. **Excepție anunțată: Victor aloc o cheie DEMO doar în ziua demo-ului, când implementăm extracția live;** până atunci nimeni nu are cheie. Apelul API rămâne în cod în spatele `EXTRACT_ALLOW_API=1` (oprit implicit) și se pornește doar la cererea lui Victor. Extracția fără cheie = **cache din `data/cache/` + stub regex** (rezerva din `backend/api/pipeline.py`).
- Textele se transformă în evenimente de **subagenți Claude Code cu modelul Haiku** (din abonament), nu prin API: dai agentului promptul `SYSTEM` din `backend/extract/extract.py`, schema `contracts/event.schema.json` și textul; întoarce JSON-ul evenimentului; îl importi în cache (Patrick face uneltele, vezi `board/`).
- **Model pe dificultate:** Haiku = extragere text -> eveniment, formatare, texte dummy, verificări simple. Sonnet = cod obișnuit (API, UI, teste, documentație). Model/efort mare (Opus) doar pentru bug care persistă după 2 încercări, schimbări de contract sau algoritmi dificili; spune-i omului înainte.
- **Standardizarea e cu AI, nu cu regex.** Text nou live = Haiku prin Claude Code headless din abonament (`ai_cli`, `backend/extract/cli_ai.py`; o singură dată `claude auth login` pe laptopul demo), apoi cache. Regex rămâne doar ultima rezervă, marcată „Regex (simplificat)". Pregătiți totuși în cache textele de demo (`docs/DEMO.md`) pentru viteză.

## Principii de produs (nu le încălca)
- Ponderile se aplică întregului sistem: toate inputurile și toate predicțiile trec prin același calcul de scor și același `contracts/weights.yaml`. Apelul clientului e doar un alt input.
- Regula de intrare: nimic existent → se adaugă; există ceva și e sigur → se aplică; există ceva și e nesigur → predicție vizibil diferită, neaplicată, cu scor. Fiecare modificare are jurnal și „de ce".
- Nu inventa date lipsă: marchează „lipsă" sau „de verificat".

## OpenSpec (features noi)
Features noi se planifică cu OpenSpec: `openspec/changes/<feature>/` (propunere, spec, sarcini pe roluri), creat cu `/openspec-propose "idee"`; implementare cu `/openspec-apply-change`; la final `/openspec-archive-change`. Citește `openspec/changes/` și `openspec/specs/` la începutul blocului de lucru. Instalare: `brew install node`, `npm install -g @fission-ai/openspec@latest`, apoi `git pull`. Cine deține feature-ul scrie în `openspec/changes/<feature>/`; `openspec/specs/` se schimbă doar prin arhivare.
Sesiunea 2: împărțirea sarcinilor pe roluri e în `docs/plan-sesiune-2-openspec.md`. Folderele noi `backend/trace/` și `backend/racordare/` sunt ale lui A (Patrick); B le integrează în motor.

## Sesiunea 3: blocăm logica, apoi UI (planul: `docs/plan-sesiune-3-logica.md`)
Citește `docs/plan-sesiune-3-logica.md` și `openspec/changes/` (geocodare-adresa-acuratete, traseu-generat-din-raport, safeguard-zona-prototip, retea-start-origine-model, racordare-fara-neaplicat, reglaje-logica-fara-cod) la începutul blocului. Sarcinile: B0–B8 (Victor), A1–A7 (Patrick), C1–C5 (Claudiu). Pasul 0 e contractul lui B; până apare în `git log -- contracts/`, ceilalți pregătesc fără cod dependent.
- **Geocodare:** adresa/strada dă coordonate aproximative DOAR din cache-ul OSM local + AI (Haiku din abonament, fără cheie, fără serviciu extern). AI alege dintre străzile din cache, nu inventează coordonate. Acuratețea scade cu vagul textului; tabelul e în `weights.yaml`.
- **Trace:** se generează automat la raport, lângă punct, ca semnal complementar; parametrii (zgomot, durată, acoperire, decalaj) cresc sau scad acuratețea. Etichetat „simulat".
- **Safeguard:** niciun punct nu iese din 3 km față de centroidul rețelei de start (`zona.raza_max_m`); în afară = „eronat în cadrul prototipului", neaplicat, în jurnal. Fără excepții pe sursă.
- **Origine:** rețeaua de start (KMZ/OSM + puncte simulate hardcodate) = `origine: retea_start`, acuratețe mare. Tot ce adaugă sistemul = `generat_model`. Nu mai scrie „Predicție AI": AI face doar standardizarea (extracție, geocodare); predicțiile sunt ale modelului nostru.
- **Racordare:** nu mai e `neaplicat` din lipsă de date: scară de rezerve (locație: coordonate > clic > geocodare > trace > operator; lanț: raza normală > extinsă > linie dreaptă > doar casa) și „predicție slabă". `neaplicat` doar fără locație sau în afara zonei.
- **Schimbări mici de logică:** (1) `reglaj:` = o valoare în `contracts/weights.yaml`, validată cu `python -m backend.engine.verifica_reglaje`, linia tipărită se lipește în `board/`; (2) orice altceva = „cerere de logică" în `board/` cu `@Victor` după `docs/cerere-logica.md`. Prompturile AI sunt ale lui A. Banc de test fără UI: `backend/api/banc_logica.py`.
- **Înghețare:** după `scripts/verifica_tot.sh` verde și `data/golden/`, Victor pune tag-ul `logic-v1`; după el, schimbări de cod în motor doar prin cerere aprobată. UI-ul (Lovable) se face după; un singur prompt grupat, netrimis până decide omul.

## Sesiunea 4: prototip gata de prezentat (planul: `docs/plan-sesiune-4-prezentare.md`)
Rulează doar pe laptopurile lui Victor (B) și Claudiu (C); **Patrick (A) nu participă**. Folderele lui trec temporar: `backend/extract`, `backend/geo`, `backend/trace`, `backend/racordare`, `data/simulare`, `data/golden`, `data/cache` la **B**; `data/reports` la **C**. Citește planul, `openspec/changes/` (acuratete-realista, predictie-pe-strazi, simplificare-demo, scenariu-timeline-realist, ui-prezentare-gis) și `contracts/interfaces.md` („Sesiunea 4”). Planul aprobat ține loc de cerere de logică pentru `logic-v1`; la final Victor pune `logic-v2`.
- **Acuratețe:** rețeaua GIS (KMZ) e verde și stabilă (0,95, nu sub 0,85 din timp); ce vine din rapoarte e plafonat după cum a fost localizat (coordonate 0,85 … analiză hartă 0,40); raport executat aplică de la 0,50; 4 benzi de culoare (`banda`, calculată de motor); „verificat de om” = 1,0 pe orice element.
- **Accent: căutare pe stradă.** Stradă + indiciu parțial („lângă nr. 15”, „între 10 și 20”, „capătul străzii”) → fereastră pe stradă → elementele din ea. Nu se așteaptă coordonate exacte. Fără niciun indiciu de loc nu se inventează nimic.
- **Analiza hărții:** legăturile prezise merg pe graful de străzi OSM local, nu în linie dreaptă prin case.
- **Scoase:** scenariul extrem, traseul de ultima oră (UI, API; generarea din motor oprită), plasarea prin clic, bannerul „DATE FICTIVE” de sus, codurile brute în UI. Doar 3 butoane de echipă (Mentenanță, Investiții, Racordări).
- **UI:** doar Lovable, 3 prompturi grupate (P1–P3), fiecare netrimis până decide Victor; textele în română vin din API, Lovable doar afișează.
- Textele de demo folosesc doar cele 24 de străzi din cache-ul OSM local (`osm.strazi()`).

## Sesiunea 4b: tracking echipe (planul: `docs/plan-tracking-echipe.md`)
Funcție independentă de rapoarte: o tură simulată a tabletei unei echipe (GPS pe străzi, determinist pe seed). Oprire lângă un stâlp existent = stâlp confirmat (acuratețea crește, sursa `tracking_gps`, fiabilitate 0,60); oprire lungă fără stâlp = stâlp presupus (predicție punctată, plafonată). Fiecare tură e eveniment `tracking_tura` în timeline. UI: tab separat „Tracking echipe”, cu animația tabletei și rezultatele arătate la fiecare oprire. B: contract, `backend/tracking/`, mixin în motor, 2 ture în scenariu. C: 3 endpointuri `/tracking/*`, prompt Lovable P4 (netrimis până decide Victor). OpenSpec: `openspec/changes/tracking-echipe/`. Nu e „traseul de ultima oră” (acela rămâne scos).
