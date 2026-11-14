# Plan prototip: A grid model that keeps itself up to date

Stare: gata pentru implementare. Timp disponibil: o noapte, deci planul are o linie de tăiere clară (vezi secțiunea 6). Lucrul se împarte pe 3 laptopuri cu Claude, coordonate prin git (vezi secțiunea 10).

## 1. Scop
Un prototip care transformă rapoartele echipelor (mentenanță, investiții, racordări) și apelurile clienților în modificări ale modelului GIS al rețelei JT, fiecare cu scor de încredere vizibil. Un om din teren vede ce e sigur și ce nu înainte să plece.

## 2. Decizii luate
- **Rețea de bază:** `Retea_JT_PTAB_7812.kmz` (date fictive: 264 tronsoane aeriene/ramuri/subterane, 265 noduri, 1 post de transformare, lângă Giurgiu/Ilfov). Din ea scoatem sau mutăm câteva elemente ca să avem ce descoperi.
- **Inputuri dummy în română:** fișe cu câmpuri (coordonate, adresă, nr. cadastral) și text liber ca din Word, pentru mentenanță, investiții, racordări, plus apeluri de clienți (ID client + locație).
- **Extracție text → structură:** API Claude (Victor are cheie; merge doar în `.env`, ignorat de git).
- **Potrivire pe rețea:** cod nod/tronson dacă e dat; altfel coordonate (element apropiat); altfel adresă geocodată, cu scor mic.
- **Traseu cablu lipsă:** străzi din OpenStreetMap, traseu probabil pe stradă între nodurile vecine, comparat cu linia dreaptă. Fără analiză de imagini.
- **Ponderile se aplică sistemului întreg, nu doar apelurilor.** Fiecare input (raport de mentenanță, investiții, racordări, apel de client) are o fiabilitate, iar fiecare predicție (traseu, tip de activ, element lipsă) are o încredere. Toate intră în același calcul de scor. Apelul clientului e doar un alt tip de input, fără mecanism special. „Nu am curent/net" poate însemna că a căzut rețeaua, nu că lipsește, deci apelul are pondere mică și adaugă ipoteze, nu certitudini.
- **Scor de încredere:** reguli simple, explicabile, cu „de ce" la fiecare scor.
- **Regula de intrare a unei propuneri:**
  - nu există nimic în model în acel loc → se adaugă direct;
  - există ceva și propunerea e sigură (peste prag) → se aplică;
  - există ceva și propunerea e nesigură → apare ca predicție vizibil diferită (ex. linie punctată), neaplicată, cu scor;
  - orice modificare are jurnal (ce, de ce, din ce raport).
- **Interfață:** backend Python real + UI în Lovable, care apelează API-ul. Două ecrane:
  1. ecranul procesului, cu etapele pentru un raport: text → structură → potrivire → propunere → scor;
  2. harta GIS cu timeline și buton play, ~3 luni simulate, ~25–30 evenimente.
- **Demo:** partea cu timeline e de maximum 1 minut. Trebuie să meargă atât cu datele dummy deja încărcate, cât și cu un raport nou lipit live, procesat de adevăratul pipeline (nu doar redare).

## 3. Arhitectură
```
rapoarte dummy / raport nou lipit live
        │
  [1] Extracție (Claude)  →  eveniment standard
        │
  [2] Potrivire pe graf (ID / coordonate / adresă)
        │
  [3] Predicție traseu (OSM) pentru elemente lipsă
        │
  [4] Scor de încredere + decizie (adaugă / aplică / predicție)
        │
  [5] Model GIS versionat în timp  →  API  →  UI Lovable (proces + hartă + timeline)
```

Schema comună de eveniment: `event_id`, `echipa_sursa` (mentenanta/investitii/racordari/apel_client), `tip` (racord_nou, activ_inlocuit, linie_planificata, nod_lipsa, avarie_semnalata), `referinta` (id element și/sau coordonate/adresă), `status` (executat/planificat/semnalat), `data`, `fiabilitate_sursa`, `text_original`, `incredere_extractie`.

Model în timp: fiecare element al rețelei are o listă de stări datate (`valid_de_la`, scor, motiv, eveniment sursă), iar timeline-ul doar alege o dată și afișează starea la acea dată.

Scorul (pornire de la reguli, parametri în fișier de configurare):
- element din KMZ original: scor inițial 0.6, nu 1.0, pentru că nimeni nu l-a verificat recent;
- scade lent în timp de la ultima verificare;
- crește la confirmare din teren (raport de mentenanță executat);
- scade la un semnal contradictoriu (orice input care îl contrazice, inclusiv un apel);
- toate efectele de mai sus sunt multiplicate cu fiabilitatea sursei inputului (tabletă cu coordonate > formular > text liber > apel), într-un singur tabel de ponderi în configurare, la fel pentru toate tipurile de input;
- pentru elemente prezise: scor combinat din încrederea extracției, calitatea potrivirii și cât de bine urmează traseul strada, trecut prin același mecanism de decizie (adaugă / aplică / predicție) ca orice altă modificare.

API (FastAPI):
- `POST /rapoarte` primește text, rulează pipeline-ul, întoarce pașii intermediari;
- `GET /retea?data=...` întoarce GeoJSON cu starea și scorurile la acea dată;
- `GET /evenimente` lista pentru timeline;
- `GET /element/{id}` istoricul și „de ce".

## 4. Seturi de date dummy (scenarii pentru ~28 evenimente)
1. **Nod lipsă pe stradă curbată:** un nod scos din model; un raport de mentenanță îl pomenește; sistemul propune traseul pe stradă, nu linia dreaptă.
2. **Înlocuire de cablu nerecordată:** raport de investiții cu cablu nou; sistemul modifică secțiunea și arată scor ridicat.
3. **Racord nou cu coordonată scrisă greșit** (lat/lon inversate sau zecimale lipsă); sistemul o corectează sau o marchează „de verificat".
4. **Apeluri de clienți într-o zonă:** mai multe apeluri „nu am curent" scad încrederea secțiunii, fără să o șteargă.
5. **Raport contradictoriu:** două echipe descriu aceeași zonă diferit → predicție, nu aplicare.
6. **Secțiune neverificată luni de zile:** scorul scade vizibil pe timeline; hartă cu zone roșii.
7. **Raport fără ID, doar adresă și nr. cadastral:** potrivire cu scor mic.

## 5. Etape de implementare (în ordine, fiecare cu rezultat verificabil)
**Etapa 0, pregătire (~20 min).** Structură repo, `.env` (în `.gitignore`), dependențe, `.gitignore` pentru `.env` și date mari. Verificare: serverul pornește și răspunde la `/health`.

**Etapa 1, rețeaua în graf (~45 min).** Parsăm `doc.kml` în noduri și tronsoane, construim graful, exportăm GeoJSON. Introducem defectele din secțiunea 4. Verificare: număr de noduri/tronsoane identic cu KMZ-ul (265/264), GeoJSON afișat pe o hartă simplă.

**Etapa 2, datele dummy (~60 min).** Scriem ~28 rapoarte în română (câmpuri și text liber) și o listă de apeluri, cu date pe ~3 luni, aliniate la scenarii. Verificare: fiecare scenariu are măcar un raport; datele sunt într-un singur folder, versionate.

**Etapa 3, extracție cu Claude (~60 min).** Prompt cu schema de eveniment, ieșire JSON validată, încredere a extracției, salvare în cache pentru demo fără internet. Verificare: pe cele 28 de rapoarte, câmpurile obligatorii sunt completate sau marcate lipsă, fără invenții; cel puțin 3 rapoarte verificate manual.

**Etapa 4, potrivirea pe graf (~45 min).** ID, apoi coordonate (cel mai apropiat element, cu prag de distanță), apoi adresă. Verificare: fiecare eveniment ajunge la un element sau la „nepotrivit" cu motiv.

**Etapa 5, scor și motor de decizie (~75 min).** Regulile din secțiunea 3, modelul versionat în timp, jurnal. Verificare: pe scenariile 2, 4 și 5, scorurile se mișcă așa cum ne așteptăm și fiecare are „de ce".

**Etapa 6, predicția traseului din OSM (~60 min).** Descărcăm străzile zonei (o singură dată, cache local), calculăm traseul pe stradă între nodurile vecine, comparăm cu linia dreaptă. Verificare: scenariul 1 produce un traseu care urmează strada și are scor mai mare decât linia dreaptă.

**Etapa 7, API (~30 min).** Endpoint-urile din secțiunea 3. Verificare: `curl` pe fiecare; `POST /rapoarte` cu un text nou întoarce pașii intermediari.

**Etapa 8, UI în Lovable (~90 min).** Ecranul procesului pentru un raport, harta cu culori după scor, predicții punctate, timeline cu play, panou „de ce", formular „adaugă raport nou". Backend-ul se expune printr-un tunel la demo. Verificare: se rulează tot pe date dummy, apoi se lipește un raport nou și apare pe hartă.

**Etapa 9, repetiție demo (~30 min).** Scenariu de 60 de secunde, rulat de 3 ori cap-coadă, plus plan B: rezultate din cache și o înregistrare video.

## 6. Linie de tăiere pentru o noapte
Obligatoriu (etapele 0–5 și 7–8): rețea, rapoarte, extracție, potrivire, scor, API, UI cu timeline.
Dacă rămâne timp: etapa 6 (traseu pe stradă). Dacă nu rămâne, scenariul 1 se prezintă cu linia dreaptă marcată „predicție", iar traseul pe stradă rămâne în prezentare ca pas următor, spus clar ca nefăcut.
Se taie primele: scenariul 7 (adresă fără ID), orice analiză de imagini, auto-detectarea inversării lat/lon (rămâne marcare „de verificat").

## 7. Riscuri
- **Lovable apelează un backend local:** are nevoie de tunel cu HTTPS public (ngrok/cloudflared). Încercăm în Etapa 7, nu la final. Plan B: UI mic în HTML/Leaflet servit de FastAPI.
- **Extracția Claude greșește:** cerem JSON strict, marcăm „lipsă" în loc să inventeze, verificăm manual 3 exemple.
- **Date fictive prezentate ca reale:** în UI și în prezentare scrie clar „date fictive, rețea demonstrativă". Nu se afirmă nimic despre PPC care nu e confirmat.
- **Repo privat al altui cont:** nu punem date reale PPC și nu punem cheia API în repo.
- **Cheia API:** doar în `.env`, în `.gitignore`.

## 8. Ce NU face prototipul (de spus la demo)
- Nu lucrează pe date reale PPC și nu e integrat cu platforma GIS a companiei.
- Nu analizează imagini satelitare; traseul se bazează pe străzi OSM.
- Reglementările: doar jurnal de modificări și marcarea predicțiilor, fără cerințe formale verificate cu mentorii.

## 9. Întrebări rămase pentru mentori (nu blochează prototipul)
- Ce platformă GIS se folosește azi și în ce format se exportă modelul?
- Cine are voie să valideze o modificare?
- Ce toleranță de poziție e acceptabilă?
- Cât durează azi de la schimbarea din teren până în GIS?

## 10. Lucru în paralel: 3 laptopuri, fiecare cu Claude, git ca loc de comunicare
Repo: `popapatrick/AIBootcamp`, toți trei cu acces de scriere. Regula de bază: **doi agenți nu ating niciodată aceleași fișiere**, iar tot ce trece de la unul la altul trece printr-un contract scris în git.

### 10.1 Cine face ce
| Laptop | Rol | Etape | Folderele lui (doar el scrie aici) |
|---|---|---|---|
| **A** | Date + extracție | 2, 3 | `data/reports/`, `data/events/`, `data/cache/`, `backend/extract/` |
| **B** | Motor (graf, potrivire, scor, OSM) | 0, 1, 4, 5, 6 | `data/network/`, `data/model/`, `backend/engine/`, `contracts/weights.yaml` |
| **C** | API + UI Lovable | 7, 8 | `backend/api/`, `frontend/` |
| toți | Etapa 9, repetiția demo | 9 | — |

Etapa 0 (schelet de repo și contracte) o face B în primele ~30 min, iar A și C încep în paralel cu ce nu depinde de ea (vezi 10.4).

### 10.2 Structura repo-ului
```
contracts/            # singura zonă partajată
  event.schema.json   # schema comună de eveniment (A produce, B consumă)
  state.schema.json   # starea unui element la o dată, cu scor și „de ce" (B produce, C consumă)
  api.openapi.yaml    # endpoint-urile (C implementează, B și A le respectă)
  interfaces.md       # semnăturile funcțiilor Python între module
  weights.yaml        # tabelul unic de ponderi (inputuri și predicții), proprietar B
data/  backend/  frontend/  board/  docs/
CLAUDE.md             # regulile de mai jos, citite automat de fiecare Claude
```

### 10.3 Contractele dintre module
- **A → B:** `data/events/events.json`, listă de evenimente conform `event.schema.json`. Funcția `extract_event(text, sursa) -> Event` e apelată și de API pentru `POST /rapoarte`.
- **B → C:** funcția `apply_event(event) -> StepTrace` (pașii intermediari pentru ecranul procesului) și instantanee `data/model/snapshots/<data>.geojson` plus `data/model/timeline.json`.
- **C → toți:** `api.openapi.yaml`, plus mod „stub" al API-ului care citește fișiere gata făcute, ca UI-ul să nu aștepte motorul.
- O schimbare de contract se face doar într-un commit cu prefixul `contract:`, anunțată în `board/` și acceptată de cei afectați înainte să se bazeze cineva pe ea.

### 10.4 Cum nu stă nimeni degeaba la început
- **A:** scrie în primele 30–40 min `data/events/events.stub.json` cu 4–5 evenimente scrise de mână conform schemei, apoi trece la cele ~28 de rapoarte și la extracție. Citește rețeaua direct din KMZ pentru ID-uri reale.
- **B:** publică schema de eveniment și scheletul în primele 30 min, apoi `data/model/sample/` cu un instantaneu fals dar valid, ca C să poată construi UI.
- **C:** pornește UI-ul în Lovable pe date din `data/model/sample/` și pe API în mod stub, până apare motorul.
- Prima integrare reală: A → B când există `events.json` cu extracție reală, B → C când motorul produce instantanee reale.

### 10.5 Reguli git (și pentru agenți, în `CLAUDE.md`)
1. La începutul fiecărui bloc de lucru: `git pull --rebase origin main`, apoi citește `board/*.md` și diff-ul din `contracts/`.
2. Fiecare agent lucrează doar în folderele lui din 10.1. Dacă are nevoie de o schimbare în alt folder, o cere în `board/`, nu o face el.
3. Commit-uri mici și dese, minimum la fiecare ~20–30 min, cu prefix: `[A] ...`, `[B] ...`, `[C] ...` sau `contract: ...`.
4. Push direct pe `main`, pentru că folderele sunt disjuncte. Înainte de push: pornește serverul sau rulează smoke test-ul. Nu se împinge cod care strică `main`.
5. Dacă `git push` e respins: `git pull --rebase`, rezolvă, push. Nu se face niciodată `--force`.
6. Cheia API stă doar în `.env`, pe fiecare laptop separat, trimisă pe alt canal. `.env` și `.laptop` sunt în `.gitignore`. Fiecare laptop își marchează rolul într-un fișier local `.laptop` (A, B sau C), citit de Claude.
7. Datele pun ce e fictiv în clar: „date fictive". Fără date reale PPC în repo.

### 10.6 Panoul de coordonare `board/`
Un fișier per laptop: `board/Patrick.md`, `board/Victor.md`, `board/Claudiu.md`. Fiecare scrie doar în al lui, așa că nu apar conflicte. Format de intrare, nou deasupra:
```
## 02:15
Gata: ...
În lucru: ...
Blocat / am nevoie de la B: ...
Contract atins: nu / da (care)
```
Întrebările către alt laptop se scriu în `board/` cu `@B`/`@Victor`, `@C`/`@Claudiu` sau `@A`/`@Patrick`, iar răspunsul vine în panoul celui întrebat. Omul din fața laptopului poate transmite verbal ce e urgent, dar tot ce afectează codul trebuie scris în git.

### 10.7 Puncte de sincronizare (ore de la start)
- **H+0:30** contracte și schelet pe `main`; A și C confirmă în panou că le-au citit.
- **H+1:30** stub-uri gata la toți, UI-ul afișează date false pe hartă.
- **H+3:30** prima integrare A → B (evenimente reale prin motor, chiar și cu scor simplu).
- **H+5:30** scor complet (etapa 5), API real, Lovable apelează API-ul prin tunel.
- **H+7:00** traseu OSM (etapa 6) dacă a rămas timp, altfel se aplică linia de tăiere din secțiunea 6.
- **H+8:00** înghețăm funcționalitățile, repetiția demo de 1 minut, plan B cu cache și video.
La fiecare punct, cei trei verifică împreună că `main` pornește curat de pe un laptop proaspăt clonat.

### 10.8 Primul pas concret
0. **Înainte de primul commit, laptopul C configurează Lovable** prin pluginul oficial Lovable (MCP, autentificare OAuth făcută de om, o singură dată). Claude creează proiectul Lovable din prompturile din `frontend/lovable-prompts.md`, citite din plan: ecranul procesului, harta cu timeline, panoul „de ce", formularul de raport nou. Lovable consumă credite, deci Claude spune câte prompturi trimite înainte. Rezultatul (link-ul proiectului Lovable, ce s-a creat, ce rămâne de făcut) se scrie în `board/Claudiu.md` și în `frontend/README.md`, ca ceilalți să nu refacă nimic. Publicarea proiectului Lovable o confirmă omul.
1. Unul dintre voi comite structura și `CLAUDE.md` din 10.2 și 10.5 (poate B, ca parte din Etapa 0).
2. Ceilalți fac `git clone` / `git pull`, creează `.laptop` și `.env` local. După `git pull` trebuie să găsească gata: structura, contractele, `CLAUDE.md`, panoul și starea Lovable.
3. Fiecare Claude citește `PLAN-prototip.md` și `CLAUDE.md` și își scrie prima intrare în `board/`.

### 10.9 Pregătirea celorlalte laptopuri (fiecare, o singură dată)
1. `git clone https://github.com/popapatrick/AIBootcamp.git` și deschide folderul în Claude.
2. Activează pluginul **Lovable** din contul claude.ai și autentifică-te (OAuth). Îl folosește în principal C, dar îl activăm pe toate trei ca oricare Claude să poată citi starea proiectului Lovable și să continue munca altuia.
3. Creează local `.laptop` (A, B sau C) și `.env` cu cheia API (nu intră în git).
4. Claude citește, în ordine: `CLAUDE.md`, `PLAN-prototip.md`, `contracts/`, `board/*.md`, `docs/`. Regulile de rol sunt în agenți dedicați din repo, ca să se încarce singure: `.claude/agents/patrick.md`, `victor.md`, `claudiu.md`. Fiecare conține rolul, folderele proprii, contractele pe care le produce și le consumă, regulile din 10.5 și regula de efort din secțiunea 11.
5. Prima acțiune a fiecărui Claude: o intrare în `board/<laptop>.md` cu „citit planul, rol confirmat, întrebări".

## 11. Model și efort pe laptop
Claude alege singur modelul și efortul potrivit pentru fiecare subtask (subagenți și sesiuni), pe baza tabelului de mai jos. Omul alege doar modelul de bază al sesiunii din selectorul de model al aplicației, iar Claude îl schimbă din sesiune doar cu acordul lui.

| Laptop | Muncă | Recomandare |
|---|---|---|
| A | scris rapoarte dummy, schemă, prompt de extracție | model mediu, efort mediu |
| B | scor, potrivire, OSM, decizii cu multe cazuri-limită | model puternic, efort ridicat |
| C | API, prompturi Lovable, legături UI | model mediu, efort mediu |

Regulă în `CLAUDE.md`: dacă un bug nu se rezolvă după 2 încercări, sau o eroare se repetă, Claude spune explicit în chat și în `board/` că „poate trebuie ridicat efortul sau modelul", cu motivul, și omul decide. Claude nu continuă la nesfârșit în aceeași direcție.

## 12. Documentația la fiecare pas
Regulă: **o etapă nu e terminată până nu are documentație în același commit sau în următorul, înainte de a trece mai departe.** Documentația e scrisă de agentul care a făcut etapa, în română, scurt, ca un coleg care vine după el să poată continua fără să întrebe.

Ce se scrie, per etapă, în `docs/etapa-N-<nume>.md`:
- **Ce face** modulul, în 3–5 rânduri.
- **Cum se rulează** și cum se verifică (comanda exactă și rezultatul așteptat).
- **Intrări și ieșiri**, cu trimitere la contractul din `contracts/`.
- **Decizii luate și de ce**, inclusiv ce am respins.
- **Limite cunoscute și ce nu merge încă.**
- **Ce trebuie să știe ceilalți laptopuri** (dependențe, ce s-a schimbat).

În plus:
- fiecare folder mare are `README.md` cu 5–10 rânduri (ce e aici, cine îl deține);
- funcțiile publice au docstring cu intrare, ieșire și un exemplu;
- deciziile importante merg într-un singur fișier cu intrări datate, `docs/decizii.md`;
- orice schimbare de contract actualizează `contracts/interfaces.md` în același commit `contract:`;
- starea Lovable (link proiect, ce prompturi s-au trimis, ce rămâne) e în `frontend/README.md`;
- la sfârșit, `docs/DEMO.md` (scenariul de 60 de secunde, pașii, planul B) și `docs/LIMITE.md` (ce NU face prototipul, din secțiunea 8).

Verificare la fiecare punct de sincronizare din 10.7: fiecare laptop confirmă în panou „documentația etapei lui e pe `main`". Un punct de sincronizare nu se consideră trecut fără ea.
