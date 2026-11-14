# Sesiunea 2: plan explicit, muncă împărțită egal (OpenSpec)

Date FICTIVE. Scris de B (Victor). Detaliile fiecărui feature sunt în `openspec/changes/<nume>/` (proposal, design, specs cu scenarii, tasks). Acest fișier spune CINE face CE, în ce ordine și de ce.

## 1. Cum lucrăm cu OpenSpec (toți)
1. Instalare o singură dată: `brew install node`, `npm install -g @fission-ai/openspec@latest`, apoi `git pull --rebase origin main`.
2. Ordinea de citit: acest fișier, apoi `openspec/changes/<feature>/proposal.md` și `specs/*/spec.md` (ce trebuie să facă sistemul, cu scenarii), apoi `tasks.md` (sarcinile).
3. Implementare: în Claude spui „/openspec-apply-change <feature>, doar sarcinile mele (A/B/C)". Bifezi `- [x]` în `tasks.md` doar când e gata și verificat (smoke test). Înainte de push: `git pull --rebase origin main`.
4. Specificația pare greșită? Nu o rescrie singur: scrie în `board/<laptop>.md` cu `@Victor`.
5. La final, feature-ul se arhivează (`/openspec-archive-change`) doar când toate sarcinile sunt bifate.
6. Comenzi utile: `openspec list`, `openspec validate --all`.

## 2. Cele 7 features
| # | Feature | Ce vede omul în demo |
|---|---|---|
| 1 | `harta-aspect-kmz` | Harta ca în KMZ (case verzi, noduri importante, cabluri pe categorie) + halou de stare |
| 2 | `interfata-rapoarte-pipeline` | 4 butoane de sursă, text messy, Generează exemplu, Show pipeline, data ultimei actualizări |
| 3 | `mutare-fire-sens-giratoriu` | Mesaj „firele au fost mutate": zonă „de verificat" + traseu propus pe străzi |
| 4 | `cerere-racordare-predictie` | Buton Cerere racordare casă: actualizare directă sau lanț prezis de stâlpi pe străzi |
| 5 | `verificare-om-predictii` | Acceptă (verificat în teren) / Respinge pe o predicție; marcaj „confirmat de om" |
| 6 | `timeline-cazuri-extreme` | Încarcă rețeaua cu evenimente: ramură pe etape, sens giratoriu, segment demontat, val de apeluri |
| 7 | `locatie-din-trace-tableta` | Trace GPS din ultima oră + adresă vagă: oprirea cea mai lungă dă stâlpul exact |

## 3. Principiul împărțirii
Fiecare lucrează pe un lanț complet, ca să nu așteptăm unul după altul:
- **B (Victor): motorul și contractul.** Tot ce decide scorul, modelul și jurnalul.
- **A (Patrick): modulele de calcul noi (trace și racordare) plus tot ce e date și extracție.** Primește două foldere noi doar ale lui, `backend/trace/` și `backend/racordare/`, ca să lucreze la algoritmi fără să atingă motorul. B le integrează.
- **C (Claudiu): API și toată interfața Lovable.** Plus verificarea cap-coadă și pregătirea demo-ului.

Estimare (ore de lucru Claude cu omul, aproximativ): B ~9 h, A ~9,5 h, C ~10 h.

## 4. Pasul 0, obligatoriu: contractul (B, ~30 min)
Un singur commit `contract:` cu tot ce depinde de ceilalți: `clasa` pe noduri/tronsoane; `schimbari[]` și `ultima_actualizare`; tipurile de eveniment `mutare_fire`, `activ_demontat`, `cerere_racordare`; sursa `om_teren` (0,95) și `detalii.decizie`; `detalii.trace`; endpointul `POST /predictii/{id}/decizie`; pragurile noi în `weights.yaml`; și semnăturile modulelor lui A:
- `backend/trace`: `gaseste_opriri(puncte, cfg)` și `localizeaza(trace, adresa, net, strazi, cfg)`.
- `backend/racordare`: `prezice_lant(locatie, net, strazi, cfg)`.
Până apare în `git log -- contracts/`, A și C doar pregătesc (texte, scenarii, prompturi), nu scriu cod care depinde de câmpurile noi.

## 5. Sarcinile lui B (Victor), în ordine
| ID | Sarcină | Feature | De ce e a lui B |
|---|---|---|---|
| B1 | Commit-ul de contract (secțiunea 4) | toate | doar B schimbă contractele |
| B2 | `clasa` din `serie`/`categorie`, în snapshot și `network.geojson` | 1 | motorul deține modelul |
| B3 | `schimbari[]` structurate la `apply_event` și `ultima_actualizare` în statistici | 2 | jurnalul și scorul sunt ale motorului |
| B4 | Decizia omului: acceptă/respinge, o singură decizie, marcaj `confirmat_de: om` | 5 | e un input în același calcul de scor |
| B5 | `mutare_fire`: zona „de verificat" și propunere de traseu pe străzi (`osm.py`) | 3 | refolosește OSM și scorul |
| B6 | `activ_demontat`, val de apeluri (agregare), încărcarea scenariului `extrem` | 6 | reguli de scor |
| B7 | Integrare trace: apelează `backend/trace`, folosește rezultatul în potrivire, jurnal | 7 | potrivirea e a motorului |
| B8 | Integrare racordare: apelează `backend/racordare`, predicții individuale pe stâlp | 4 | modelul aplică predicțiile |
| B9 | Recalibrare, `docs/DEMO.md`, `docs/etapa-9` și `etapa-14`, notă în `board` | toate | calibrarea e a motorului |

## 6. Sarcinile lui A (Patrick), în ordine
| ID | Sarcină | Feature | Explicație |
|---|---|---|---|
| A1 | `data/reports/exemple-dummy.json`: câte 4 texte messy pe sursă (racordări, investiții, mentenanță, apel call center), cu stâlp existent și inexistent | 2 | alimentează butonul Generează exemplu |
| A2 | Prompt și teste `extract_event` pentru: apel call center, `mutare_fire`, `cerere_racordare`, decizie `verificare` | 2,3,4,5 | extracția e a lui |
| A3 | `backend/trace/`: opriri (rază 12 m, minim 3 min), potrivire adresă cu numele străzii OSM, alegerea opririi celei mai lungi, ambiguitate, `smoke_trace.py` | 7 | algoritm pur, testabil singur |
| A4 | `backend/racordare/`: lanț de stâlpi de la cel mai apropiat nod spre casă, pe străzi OSM, la distanța mediană dintre stâlpii existenți, `smoke_racordare.py` | 4 | algoritm pur, testabil singur |
| A5 | `data/reports/trasee-dummy.json`: min. 3 trasee, între care „verificat stâlpi existenți și oprit unde nu era stâlp"; rapoarte de tabletă cu adresă vagă | 7 | cazul de demo cerut |
| A6 | `data/events/events.extreme.json` + rapoartele lui: ramură pe etape, segment demontat (2 rapoarte), val de apeluri (3+) | 6 | datele scenariului |
| A7 | Texte dummy: sens giratoriu, cerere racordare (cu și fără date în GIS), decizie om | 3,4,5 | exemple pentru UI și teste |
| A8 | Documentație: `docs/etapa-10` (exemple), `etapa-12` (scenariu extrem), `etapa-13` (mutare fire), `etapa-16` (trasee), README în folderele noi | toate | regula de documentație |

## 7. Sarcinile lui C (Claudiu), în ordine
| ID | Sarcină | Feature | Explicație |
|---|---|---|---|
| C1 | API: `schimbari` în răspuns, `GET /exemple?sursa=`, `POST /predictii/{id}/decizie`, `GET /trasee-demo`, scenariu `?scenariu=extrem`, `locatie`/`centru` din clic în `POST /rapoarte`, `trace` în raport; teste în `smoke_api.py` | 2,3,4,5,6,7 | stratul care leagă UI-ul de motor |
| C2 | Lovable: simboluri KMZ după `clasa`, halou de stare, legendă | 1 | aspectul hărții |
| C3 | Lovable: 4 butoane de sursă, Generează exemplu, Show pipeline cu pași și schimbări, data ultimei actualizări, traseu punctat pe străzi | 2 | ecranul principal |
| C4 | Lovable: Acceptă/Respinge pe predicție, marcaj „om" | 5 | decizia omului |
| C5 | Lovable: Cerere racordare casă, clic pe hartă, lanț punctat | 4 | cererea de racordare |
| C6 | Lovable: buton Fire mutate, clic pe hartă, zonă și traseu punctat | 3 | mesajul cu sens giratoriu |
| C7 | Lovable: Generează traseu ultima oră, editare cu clic pe hartă, afișare opriri | 7 | trace simulat |
| C8 | Lovable: Încarcă rețeaua cu evenimente, Play sub 45 s, halou verde/galben | 6 | timeline-ul extrem |
| C9 | Verificare cap-coadă pe preview, `docs/etapa-11` (interfață) și `demo-checklist-C.md`, repetiție 60 s | toate | demo gata |

Notă Lovable: au fost folosite ≈16,9 credite. Grupați prompturile (C2+C3 într-unul, C4+C5+C6 într-unul) ca să economisiți credite. Nu se publică până nu decide omul.

## 8. Ordinea în timp și dependențe
| Pas | B | A | C |
|---|---|---|---|
| 0 | B1 contract | A1, A5 (date, fără cod nou) | scrie prompturile C2 și C3 (nu le trimite) |
| 1 | B2, B3 | A3 (trace) | C1 (API), C2, C3 |
| 2 | B4, B5 | A4 (racordare), A2 | C4, C6 |
| 3 | B7 (după A3), B8 (după A4) | A6, A7 | C5, C7 |
| 4 | B6 | A8 | C8 |
| 5 | B9 recalibrare | verifică datele pe motor | C9 repetiție |

Dependențe: B7 așteaptă A3; B8 așteaptă A4; C8 așteaptă B6 și A6; C5 și C6 așteaptă B8 și B5. Dacă ești blocat, treci la următoarea sarcină care nu depinde de nimeni și scrii în `board/` cu `@X`.

## 9. Foldere noi și reguli
- `backend/trace/` și `backend/racordare/`: scrie doar A. Funcții publice cu docstring și README. B le apelează, nu le modifică; dacă B găsește un bug, scrie în board cu `@Patrick`.
- Restul folderelor rămân cum erau: A (`backend/extract`, `data/reports`, `data/events`), B (`backend/engine`, `data/model`, `contracts`), C (`backend/api`, `frontend`).
- Neschimbat: ponderile se aplică întregului sistem, regula de intrare (nou -> adaugă; sigur -> aplică; nesigur -> predicție neaplicată cu scor), nu inventăm date lipsă, documentație pe etapă, commit-uri mici cu prefix `[A]`/`[B]`/`[C]`/`contract:`, fără `--force`, bug care persistă după 2 încercări -> spuneți că trebuie ridicat efortul.

## 9b. Documentația, înainte de commit-ul final
Regula e acum în `CLAUDE.md` (secțiunea Documentație, „Regula de final"). Pe scurt: doc de etapă + README de folder + docstring + actualizarea `DEMO.md` / `frontend/README.md` / `interfaces.md` acolo unde s-a schimbat comportamentul, toate înainte să bifezi un task în OpenSpec. Lista documentelor așteptate la final: `etapa-9` (B, gata), `etapa-10`, `etapa-12`, `etapa-13`, `etapa-16` (A), `etapa-14`, `etapa-15` (B, gata), `etapa-7b` (C, gata), `etapa-11` (C, interfața Lovable, lipsește), README în `backend/trace`, `backend/racordare`, `backend/engine`, `data/model`, `frontend`.

## 10. Limite și presupuneri
- „Casă" = serie 7 (verde) e o presupunere din simbolurile KMZ.
- Traseul GPS e simulat; adresa dă doar strada (numărul nu se geocodează); pragurile trace-ului nu sunt calibrate pe date reale.
- Hărțile de bază cer internet.
- Plan-B (Leaflet) rămâne rezervă; nu îl dezvoltăm în plus.
