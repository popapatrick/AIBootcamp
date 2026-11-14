# Sesiunea 3: blocăm logica, apoi UI-ul (plan explicit pe 3 roluri, OpenSpec)

Date FICTIVE. Scris de B (Victor) la cererea omului. Detaliile fiecărui feature sunt în `openspec/changes/<nume>/` (proposal, design, specs cu scenarii, tasks). Acest fișier spune CINE face CE, în ce ordine și de ce. Modul de lucru e cel din `docs/plan-sesiune-2-openspec.md` secțiunea 1 și din `CLAUDE.md`.

## 1. Scopul sesiunii
Înghețăm logica (geocodare, acuratețe, trace, safeguard, rețea de start, racordare) înainte să ne concentrăm pe UI. UI-ul se face după: în sesiunea asta Claudiu face doar API, banc de test al logicii și un singur prompt Lovable scris (netrimis până decide omul).

## 2. Cele 6 features noi
| # | Feature (`openspec/changes/...`) | Ce schimbă pentru utilizator |
|---|---|---|
| 1 | `geocodare-adresa-acuratete` | Din adresă/stradă/reper ies coordonate aproximative și o acuratețe care scade cu vagul textului. Doar cache OSM local + AI (Haiku din abonament). |
| 2 | `traseu-generat-din-raport` | La orice raport cu locație se generează un traseu simulat de o oră lângă punct; parametrii (zgomot, durată oprire, acoperire, decalaj) cresc sau scad acuratețea. |
| 3 | `safeguard-zona-prototip` | Nimic nu iese din 3 km față de centroidul rețelei; un punct din afară e „eronat în cadrul prototipului". |
| 4 | `retea-start-origine-model` | Rețeaua actuală + puncte generate o dată și hardcodate = rețeaua de start reală, acuratețe mare. Tot ce adaugă sistemul = „generat de model" (nu „AI"). |
| 5 | `racordare-fara-neaplicat` | Cererea de racordare prezice din datele disponibile; fără date lasă punctul casei pe hartă și încearcă; predicție slabă în loc de neaplicat. |
| 6 | `reglaje-logica-fara-cod` | Schimbări mici de logică fără cod (valori în `weights.yaml`, validate), cerere de logică pentru restul, banc de test fără UI, tag `logic-v1`. |

Decizii luate cu omul: geocodare doar din cache OSM local + AI (fără serviciu extern, fără cheie; acoperirea națională rămâne extindere dezactivată, nu se face acum); rețeaua KMZ/OSM = rețeaua reală; safeguard față de centroid, 3 km; schimbări mici prin YAML + cerere pe board.

## 3. Cine are acces la ce (ca să împărțim eficient)
- **A (Patrick):** `backend/extract` (prompt, `cli_ai.py`), `backend/trace`, `backend/racordare`, `data/reports`, `data/events`, cache AI. Folder nou: `backend/geo/` și `data/simulare/`, `data/golden/`. Algoritmi puri, testabili singuri, plus tot ce atinge AI-ul de standardizare.
- **B (Victor):** `backend/engine`, `data/model`, `data/network`, `contracts/`. Tot ce decide scorul, modelul, zona și calibrarea. Unelte noi: `scripts/`.
- **C (Claudiu):** `backend/api`, `frontend`, contul Lovable. În sesiunea asta: API, banc de test, verificare cap-coadă, prompt Lovable scris. Nu atinge motorul; schimbările lui mici merg prin `reglaj:` sau cerere.
- Toți: abonament Claude (fără cheie). `claude auth login` o dată pe laptopul demo.

## 4. Pasul 0, obligatoriu: contractul (B0, ~40 min)
Un singur commit `contract:`, aditiv, cu `interfaces.md` actualizat în același commit:
- `referinta.adresa_structurata {strada, numar, localitate, reper}`; `detalii.geocodare {lat, lon, precizie_m, metoda, acuratete, motiv}`; `detalii.trace_params`, `detalii.trace_sursa`.
- `origine` (`retea_start` | `generat_model`) pe elemente și `predictie.origine`; `predictie.slaba`; `racordare.treapta`; `eronat_prototip` și semnalul `in_afara_zonei_prototip`; `zona` (centru, rază) în `/stare`.
- `weights.yaml`: `geocodare`, `standardizare.plafon_dupa_localizator`, `trace_generat`, `zona.raza_max_m: 3000`, `scor.initial_retea_start: 0.90`, `racordare.raza_extinsa_m`, `prag_afisare`, factorii de treaptă.
- Semnături: `backend.geo.geocodeaza(referinta, strazi, cfg)`, `backend.trace.genereaza_traseu(punct, strazi, params, seed)`, `backend.engine.zona.zona_ok(lat, lon, net, cfg)`.
Până apare în `git log -- contracts/`, A și C pregătesc (date, texte, schelete), nu scriu cod care depinde de câmpurile noi.

## 5. Sarcinile lui B (Victor), în ordine
| ID | Sarcină | Feature | De ce e a lui B |
|---|---|---|---|
| B0 | Commit-ul de contract (secțiunea 4) | toate | doar B schimbă contractele |
| B1 | `backend/engine/zona.py`, safeguard în potrivire, mutare_fire, racordare, trace; `eronat_prototip` | 3 | e regula de intrare |
| B2 | Pasul „doar adresă" apelează `backend.geo`; plafon `incredere_extractie` după localizator | 1 | potrivirea și scorul sunt ale motorului |
| B3 | `network.py` încarcă `puncte-simulare.json`; `origine` pe tot; scor inițial nou | 4 | motorul deține modelul |
| B4 | Traseu generat la raport; `factor_trace` în acuratețe; contradicție oprire/adresă | 2 | e un factor în același scor |
| B5 | `_cerere_racordare` cu scară de rezerve și „predicție slabă" | 5 | decizia de nivel e a motorului |
| B6 | `verifica_reglaje.py`, `weights.limits.yaml`, `scripts/verifica_tot.sh`, `docs/cerere-logica.md`, regula `reglaj:` în CLAUDE.md | 6 | uneltele de înghețare |
| B7 | Recalibrare pe datele noi (scor inițial, geo-test), referință de aur, tag `logic-v1` | toate | calibrarea e a motorului |
| B8 | Documentație finală: `etapa-18..22`, `calibrare.md`, `DEMO.md`, `data/model/README.md` | toate | regula de documentație |

## 6. Sarcinile lui A (Patrick), în ordine
| ID | Sarcină | Feature | Explicație |
|---|---|---|---|
| A1 | `backend/geo/`: `geocodeaza` pe `osm.strazi()` (normalizare, intersecție, interpolare, precizie), pas AI prin `cli_ai` care alege DOAR dintre străzile din cache, cache, `smoke_geo.py`, README | 1,3 | algoritm pur + AI de standardizare |
| A2 | Prompt de extracție: `adresa_structurata`, încredere după gradul de standardizare, exemple cu grade diferite; `data/reports/geo-test.json` (adrese cu coordonate așteptate, de la foarte standardizat la vag); re-umplere cache | 1 | extracția e a lui |
| A3 | `backend/trace/genereaza.py`: traseu determinist, parametri (puncte, zgomot, durată, acoperire, decalaj); `localizeaza` îl redescoperă în teste | 2,3 | algoritm pur |
| A4 | `data/simulare/genereaza_puncte.py` (stâlpi și case pe străzi OSM, seed fix, ≥ 2,5 m de existente, în zonă) și `puncte-simulare.json` hardcodat | 4 | date, fără atins motorul |
| A5 | `backend/racordare`: scara de rezerve pentru lanț (treptele 1-4), `treapta` în rezultat | 5 | algoritm pur |
| A6 | `data/golden/`: texte de aur (geocodare, trace, racordare, în afara zonei) cu rezultat așteptat | 6 | datele de aur |
| A7 | Documentație: README `backend/geo`, `backend/trace`, `backend/racordare`, `data/simulare`, `etapa-3` (prompt nou) | toate | regula de documentație |

## 7. Sarcinile lui C (Claudiu), în ordine
| ID | Sarcină | Feature | Explicație |
|---|---|---|---|
| C1 | API: `detalii.geocodare`, `trace_params` în `POST /rapoarte`, `trace_sursa`, `origine`, `slaba`, `treapta`, `eronat_prototip`, `zona` în `/stare`, `GET /geocodeaza?adresa=`; pas „geocodare" în `trace` (Show pipeline); teste în `smoke_api.py` | 1-5 | stratul care leagă totul |
| C2 | `backend/api/banc_logica.py` (texte din `data/golden/` prin pipeline, tabel + sumar) și `GET /reguli` read-only | 6 | logica se verifică fără UI |
| C3 | Verificare cap-coadă pe API cu bancul: scrie în `board/` ce nu iese, cu exemple (cereri de logică sau reglaje) | toate | testerul logicii |
| C4 | Un singur prompt Lovable scris în `frontend/lovable-prompt-sesiune3.md`, NETRIMIS: „Rețea de start" / „Generat de model", „predicție slabă", mesaj „eronat în prototip", parametri trace, fără „Predicție AI". Se trimite doar când decide omul | 3,4,5 | economisește credite |
| C5 | `docs/etapa-23-reglaje.md` (ghid), `demo-checklist-C.md`, `frontend/README.md` actualizate | toate | regula de documentație |
Reglajele mici (`reglaj:`) sunt ale lui C ca mod de lucru normal, vezi secțiunea 9.

## 8. Ordinea în timp și dependențe
| Pas | B | A | C |
|---|---|---|---|
| 0 | B0 contract | A6 (date de aur, fără cod nou), A4 (generează puncte) | schelet `banc_logica.py` pe date existente |
| 1 | B1 safeguard | A1 geo, A2 prompt | C1 (după B0) |
| 2 | B2 geocodare în potrivire (după A1), B3 (după A4) | A3 trace, A5 racordare | C2, C3 pe ce există |
| 3 | B4 trace (după A3), B5 racordare (după A5) | A7 documentație | C3 repetat, C4 |
| 4 | B6 unelte reglaj | verifică datele de aur pe motor | C5, primele reglaje reale |
| 5 | B7 recalibrare, tag `logic-v1`, B8 | — | rulează bancul pe tag, confirmă |
Dependențe: B2 așteaptă A1; B3 așteaptă A4; B4 așteaptă A3; B5 așteaptă A5; C2 așteaptă A6. Dacă ești blocat, treci la următoarea sarcină care nu depinde de nimeni și scrii în `board/` cu `@X`.

## 9. Schimbări mici de logică fără implementare mare (metoda)
1. **Reglaj** (un număr): oricine, inclusiv Claudiu, schimbă o valoare în `contracts/weights.yaml`, rulează `python -m backend.engine.verifica_reglaje`, lipește linia tipărită în `board/<laptop>.md`, face commit `reglaj: <cheia> a -> b, motiv` și push. Nu atinge alte fișiere în același commit.
2. **Cerere de logică** (altceva decât un număr): scrie în `board/<laptop>.md` cu `@Victor` după `docs/cerere-logica.md` (ce vrei, intrare exemplu, ieșire așteptată, de ce). Victor o face în ≤ 30 min (agent Sonnet) sau spune de ce nu.
3. **Prompt AI**: doar A; schimbarea invalidează cache-ul, se re-umple.
4. **Bancul de test** (`banc_logica.py`) arată imediat efectul înainte de push; reglajul care rupe limite sau smoke-uri nu se împinge.
5. După tag `logic-v1`, orice altă schimbare de cod în motor trece prin cerere aprobată.

## 10. Foldere noi și reguli
- `backend/geo/`, `data/simulare/`, `data/golden/`: scrie doar A. `scripts/`, `backend/engine/zona.py`, `backend/engine/verifica_reglaje.py`, `contracts/weights.limits.yaml`: doar B.
- Excepție unică la „scrii doar în folderele tale": commit-ul `reglaj:` pe `contracts/weights.yaml` (doar valori).
- Neschimbat: ponderile se aplică întregului sistem; regula de intrare; nu inventăm date lipsă; documentație pe etapă; commit-uri mici cu prefix `[A]`/`[B]`/`[C]`/`contract:`/`reglaj:`; fără `--force`; fără cheie API; bug care persistă după 2 încercări -> spuneți că trebuie ridicat efortul sau modelul.
- Model pe dificultate: Haiku pentru standardizare și texte dummy, Sonnet pentru cod, model mare doar la bug persistent sau algoritm greu (de ex. interpolarea pe stradă, generarea traseului), cu acordul omului.

## 11. Estimare și limite
- Ore de lucru Claude cu omul, aproximativ: B ~8 h, A ~9 h, C ~6 h (C are mai puțin cod, mai mult verificare).
- Acuratețea geocodării e necalibrată pe date reale: se calibrează pe `geo-test.json` (fictiv). Acoperirea e doar zona modelului. Traseul GPS e simulat. Valorile din `weights.yaml` sunt puncte de plecare.
- Dacă timpul se termină: se taie, în ordine, B8 (părți de doc), A7, C4; nu se taie contractul, safeguard-ul, racordarea fără neaplicat și tag-ul `logic-v1`.
