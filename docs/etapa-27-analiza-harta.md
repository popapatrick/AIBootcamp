# Etapa 27: analiza hărții (V3, D4; rol B, Sesiunea 4)

Date FICTIVE pentru rețea; străzile sunt reale (OSM local, ODbL). Fără imagini, fără serviciu extern, fără AI.

## Ce face
Legăturile prezise spre puncte îndepărtate nu mai merg în linie dreaptă prin case: modelul „analizează harta" și alege cel mai plauzibil drum pe **graful de străzi OSM local**.

`backend/engine/analiza_harta.py::traseu_pe_strazi(tinta, net, cfg, evita=None, preferate=None, exclus=None, *, sursa=None, de_la=None, strazi=None)` (pură, deterministă):
1. **Ținta pe stradă:** se proiectează pe cel mai apropiat segment (`bransament_m`). Peste `analiza_harta.max_bransament_m` (40 m) factorul scade: `max_bransament_m / bransament_m`, nu sub 0,5.
2. **Plecări:** primii `candidati` (5) stâlpi existenți (`net["noduri"]`, fără `*-casa`, fără `exclus`) din `raza_cautare_m` (800 m, în linie dreaptă), proiectați pe stradă (la cel mult 40 m de ea; altfel alternativă cu motivul „stâlpul e la X m de cea mai apropiată stradă").
3. **Drum:** Dijkstra pe graf pentru fiecare plecare; se alege cel mai scurt (drum + branșament de la ambele capete); restul sunt `alternative` cu `motiv` („mai lung cu 28 m", „nu există legătură pe străzi", „stâlpul e la 55 m de …") și `traseu` (pentru fără legătură: linia dreaptă, de desenat punctat).
4. **Stâlpi:** stâlpii existenți la < `reutilizare_stalp_m` (10 m) de drum sunt refolosiți (devin ancore); între ancore se pun stâlpi noi la cel mult `pas_stalp_m` (40 m, distribuiți uniform). Noii stâlpi în afara zonei de 3 km se taie (`ales.taiat`, lanțul se oprește la ultimul stâlp din zonă).
5. **Acuratețe:** `acuratete = plafon_locatie[sursa] × factor`, `factor = max(factor_min, exp(-L/lungime_referinta_m)) × factor_branșament`; `acuratete_stalpi = min(acuratete, plafon_locatie.analiza_harta)` (0,40). `sursa` implicit `analiza_harta`.
6. **Fără drum pe străzi:** linie dreaptă spre cel mai apropiat stâlp din candidați, `fara_drum: true`, `acuratete = min(plafon, analiza_harta.fara_drum)` (0,25), explicația „Nu există drum pe străzi; linie dreaptă, de verificat.". Dacă nu există niciun stâlp în `raza_cautare_m`: `ales: null`.
7. **V4 (mutare fire):** `evita={"centru": (lat, lon), "raza_m": r}` – muchiile care intră în cerc nu se folosesc; `preferate=["Strada Crinului"]` – muchiile acelor străzi costă `mutare_fire_document.cost_strada_noua`× (alege, nu schimbă lungimea raportată). `de_la="<id stâlp>"`: doar acel stâlp ca plecare (legătura unui nod lipsă spre un vecin declarat).

### Unde se folosește
- **Racordare** (`sesiune2.py::_cerere_racordare` + `backend/racordare`): ordinea nouă = treapta 1 (nod în `raza_nod_m`) → 2 (rază extinsă) → **3 analiza hărții** (casa la > `raza_extinsa_m`) → 4 (niciun stâlp în `raza_cautare_m`: doar casa). `treapta` rămâne în rezultat (`predictie.treapta`, pas `predictie`): noua semnificație a lui 3 = „analiza hărții", a lui 4 = „fără drum și fără stâlp în zonă". Scorul treptei 3 = scorul propunerii × `factor` (în loc de `factor_linie_dreapta_lunga`); apoi plafonul sursei casei ca până acum. Stâlpii noi: `sursa_locatie: analiza_harta` (plafon 0,40). Treptele 1-2 neschimbate.
- **Nod lipsă departe** (`model.py::_propune_element_nou`): nod nou la > 80 m de orice tronson (`NOD_DEPARTE_M`) și legătură spre un vecin > 80 m (`LEGATURA_LUNGA_M`) care altfel ar fi linie dreaptă (adică `osm.traseu` nu dă rezultat) → legătura pe străzi, cu stâlpi intermediari `NOU-<id>-<vecin>-S<k>` (sursa `analiza_harta`, plafonați) și tronsoane `NOU-<id>-<vecin>`, `…-L2`, …; pas `analiza_harta` cu `vecin`. Legăturile scurte sau cu traseu OSM credibil rămân ca înainte. Dacă analiza taie stâlpi din zonă sau nu are drum, legătura rămâne linie dreaptă. Constantele de 80 m sunt în cod (nu în `weights.yaml`).
- Nu s-au schimbat: raportele cu ID, căutarea pe stradă pentru elemente existente, regula „nod lipsă / racord nou = mereu element nou".

## Cum se verifică
```bash
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune4   # așteptat: 100/100 OK (blocul „analiza: …”, „racordare: …”, „nod lipsă departe: …”)
.venv/bin/python -m backend.racordare.smoke_racordare             # așteptat: OK: 30 verificări
bash scripts/verifica_tot.sh --strict-distributie                 # așteptat: TOT VERDE; distribuția în țintă, calibrare: 0 evenimente schimbate
```

## Intrări / ieșiri (pasul `analiza_harta` din `pasi`)
```json
{"nume": "analiza_harta", "incredere": 0.255, "rezultat": {
  "tinta": {"lat": 44.28466, "lon": 26.05401}, "bransament_m": 0.1,
  "ales": {"de_la": "6396507", "lungime_m": 536.4, "strazi": ["Strada Liviu Rebreanu"],
           "stalpi_noi": [[lat, lon], "... 13"], "stalpi_reutilizati": [],
           "traseu": [[44.2846129, 26.0601052], "..."], "cabluri": [{"de_la": "6396507", "la": "stalp-1", "puncte": [[lat, lon], "..."]}, "..."], "taiat": false},
  "alternative": [{"de_la": "6862954", "lungime_m": 484.5, "motiv": "stâlpul e la 55 m de cea mai apropiată stradă (peste 40 m): nu se leagă pe stradă", "traseu": [[lat, lon], [lat, lon]]}],
  "acuratete": 0.255, "acuratete_stalpi": 0.255, "factor": 0.6375, "fara_drum": false,
  "explicatie": ["Am găsit 103 stâlpi în 800 m și am verificat cei mai apropiați 5.", "Drumul pe Strada Liviu Rebreanu e cel mai scurt (536.4 m).", "Am pus 13 stâlpi noi la cel mult 40 m; nu am refolosit niciun stâlp existent."]}}
```
Pasul apare între `potrivire` și `predictie` (la racordare) sau între `potrivire` și `scor` (la nod lipsă; cu `vecin`). Nu apare la treptele 1-2, nici pentru legături scurte.

## Pentru Claudiu (UI)
- Pasul `analiza_harta`: desenează `ales.traseu` (linie plină), `alternative[].traseu` (subțire/punctat, cu `motiv` la hover), `ales.stalpi_noi` (poziții noi) și `ales.stalpi_reutilizati` (ID-uri existente, evidențiate); `explicatie` = cele 3 rânduri din fișa „Analiza hărții". `fara_drum: true` → linia dreaptă punctată + banda roșie. `ales: null` → doar mesajul din `explicatie`.
- Elementele prezise au `predictie.metoda: "traseu_pe_strazi"` (sau `"linie_dreapta"` la `fara_drum`), `predictie.traseu` (drumul întreg, lista [lat, lon]), `predictie.alternative` (aceleași ca în pas), `sursa_locatie: "analiza_harta"` pe stâlpii intermediari, `predictie.treapta` (3 = analiza hărții, 4 = doar casa). Câmpurile aceluiași drum sunt repetate pe fiecare element al lanțului (traseul e același).
- Lanțul e tăiat la `racordare.max_stalpi_prezisi` (8) stâlpi cu `ambiguu`; traseul și explicația arată drumul întreg, ultimul cablu merge pe stradă până la casă.
- Scorul propunerii scade cu lungimea drumului (casă la 300 m ≈ 0,17 acuratețe analiză, la 100 m ≈ 0,25 cu plafonul implicit 0,40).

## Decizii
- Graful se construiește din `osm.strazi()` (nume păstrate), nu din `osm._graf` (fără nume); `osm.traseu` rămâne neschimbat (folosit la nodul lipsă cu stradă credibilă și la căutarea pe stradă).
- Stâlpii existenți de pe drum sunt ancore, nu doar „potriviri la fiecare 40 m", ca să nu pierdem un stâlp aflat între două puncte de eșantionare. Cel mai bun punct de plecare poate fi chiar un stâlp aflat pe drum (cel mai apropiat de țintă).
- `acuratete_stalpi` și `factor` sunt ieșiri suplimentare față de planul V3 (necesare scorului racordării).
- `weights.yaml` neschimbat; constantele de 80 m (nod departe / legătură lungă) și 40 m (stâlp de plecare față de stradă) sunt în cod.

## Limite
- Doar străzile din cache-ul OSM local (24 de străzi; fără `footway`, `path`, `trunk` etc.); o stradă nelegată în OSM dă `fara_drum`.
- Candidații sunt cei mai apropiați 5 în linie dreaptă; dacă toți sunt departe de o stradă, drumul poate rata un stâlp mai îndepărtat bine legat.
- Treptele 1-2 din racordare folosesc în continuare regula veche (o singură stradă la ≤ 40 m; altfel linie dreaptă): casele între ~150 și 400 m fără stradă comună nu primesc încă analiza hărții.
- Casă la 800 m sau mai departe de orice stâlp: treapta 4 (doar casa), nu mai linie dreaptă lungă.
- Branșamentul (stâlp/țintă -> stradă) e o linie dreaptă; poate trece prin case.
- Calibrare: nicio decizie sau scor din referința de aur nu s-a schimbat; doar cererile de racordare la > 400 m și nodurile lipsă izolate dau rezultate noi.

## Notă V4 (mutare fire din document și racordare pe străzi la treptele 1-2; `docs/etapa-28-mutare-fire-document.md`)
- `evita` / `preferate` / `exclus` / `de_la` sunt folosite acum de `sesiune2.py::_legaturi_mutare` (fire mutate): câte un apel pe pereche de capete din afara zonei, cu `evita={centru, raza_m}`, `preferate=[strada_noua]`, `exclus` = tot ce e în rază, `de_la` = capătul de plecare, `sursa` = sursa centrului (`intersectie`, `strada`, `coordonate`, `id`). Un pas `analiza_harta` pe legătură, cu `legatura`, `de_la`, `la`, `evita`, `strada_preferata`.
- Racordare: analiza hărții se folosește și la **treptele 1-2** când ar ieși linie dreaptă mai lungă de 40 m (vezi `docs/etapa-22-racordare-cu-rezerve.md`). Limita „treptele 1-2 folosesc regula veche” de mai sus nu mai e valabilă; rămâne doar branșamentul scurt (≤ 40 m) drept.

## Linie planificată (`backend/engine/linie_planificata.py`, mixin `LiniePlanificata` în `GridModel`)
**Ce face.** Un raport `linie_planificata` (status `planificat`) nu schimbă rețeaua, dar apare mereu pe hartă ca **predicție punctată** `PLAN-<event_id>` (tronson): `nivel: predictie`, `predictie.metoda: traseu_pe_strazi` (sau `linie_dreapta` dacă nu există stradă credibilă), `predictie.propunere.proprietate: linie_planificata`, `predictie.traseu` (puncte), `predictie.lungime_m`, `sursa_locatie` după cum a fost localizat, scor plafonat (`plafon_locatie[sursa]`). Niciodată `in_model`. Înlocuiește vechea regulă (2 noduri în `detalii.noduri`, altfel `neaplicat`, iar un raport potrivit cu un stâlp dădea `fara_efect`).

**Scara** (prima care se aplică):
1. 2 noduri cunoscute (`detalii.noduri`, `referinta.element_id`, ID-uri de 7 cifre din text) -> `traseu_pe_strazi(de_la=nod1)` până la nod2; sursa `id`; `capete` = cele 2 noduri; pas `analiza_harta`.
2. 2 puncte GPS (`detalii.puncte = [{lat, lon}, {lat, lon}]` sau `referinta.coordonate` + `detalii.coordonate_2`) -> `osm.traseu` între ele; sursa `coordonate`; fără stradă credibilă, linie dreaptă cu calitate `analiza_harta.fara_drum`.
3. o ancoră (nod/ID, punct GPS sau stâlp existent cu care s-a potrivit raportul) + stradă -> segment de stradă de la ancoră, în sensul ferestrei, lung cât `detalii.lungime_m` (altfel 100 m); sursa `id` pentru nod, `coordonate` pentru GPS. Un punct fără stradă -> traseu pe străzi de la cel mai apropiat stâlp existent la punct (`analiza_harta`).
4. adresă/stradă cu sau fără indiciu -> segmentul din fereastra `backend.geo.fereastra_strada` (pas `cautare_strada`, `tip_cautat: "linie"`, cu `segment` și `lungime_m`; sursa `adresa_numar` | `intersectie` | `strada` | `reper`). `intre nr. X și Y` = exact intervalul; „de la colțul cu Y până la capăt” = de la intersecție la capătul străzii; altfel fereastra tăiată/prelungită la `lungime_m`, fără lungime cel mult 300 m. Dacă un capăt e la > 40 m de cel mai apropiat stâlp existent, segmentul se leagă de acel stâlp pe străzi (pas `analiza_harta`, `predictie.legat_de`, calitatea × factorul analizei).
5. niciun indiciu de loc, sau doar un nod fără direcție -> `neaplicat`. Capăt în afara zonei de 3 km -> `neaplicat`, „eronat în cadrul prototipului”.

**Verificare.** `EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune4` -> `smoke_sesiune4: 136/136 OK` (15 verificări noi `teste_linie_planificata`: 2 noduri, ID-uri din text, 2 GPS, „între nr.”, doar strada, colț până la capăt, nod + stradă, fără loc, un nod singur, niciodată `in_model`, determinism, în afara zonei). Pe scenariu (`data/events/events.json`): EV4-010 `Strada Speranței între nr. 10 și 20` -> predicție 0,503 (adresa_numar, 60 m + legătură de stâlpul SIM-032); EV4-028 `Strada Tineretului, colț cu Șoseaua Principală` + coordonate -> predicție 0,8 (coordonate, 100 m de la stâlpul potrivit); EV4-046 `Strada Orizont, vizavi de nr. 8` -> predicție 0,475 (adresa_numar, 120 m + legătură de stâlp).

**Decizii.** Mereu predicție (nu `de_verificat` sub prag, ca să apară pe hartă); `linie_planificata` nu mai trece prin ramura „potrivit -> doar notă”: un stâlp potrivit devine ancoră. `weights.yaml` neschimbat; constantele `LINIE_IMPLICITA_M` (100), `LINIE_MAX_M` (300), `LEGAT_MAX_M` (40) sunt în cod. **Stâlpi intermediari: nu se generează** (doar tronsonul `PLAN-*`; o linie planificată nu are încă stâlpi stabiliți).

**Limite.** `lungime_m` din raport nu prelungește „între nr. X și Y” (intervalul e explicit; EV4-010 declară 150 m, ies 60 m). Direcția segmentului dintr-o ancoră e spre fereastră, altfel spre capătul opus startului (nu știm sensul real). Legătura de stâlp poate fi lungă (EV4-046: ~290 m) și scade calitatea. Un nod singur fără stradă, sau fără GPS/stradă, nu are direcție -> `neaplicat`. Extracția nu produce încă `detalii.puncte`/`coordonate_2` (de adăugat în promptul lui Patrick dacă vrem 2 GPS din text).

**Pentru Claudiu (UI).** `PLAN-*` e în snapshot ca tronson cu `nivel: predictie` și geometrie `LineString` (punctat); `sursa_locatie` și `predictie.propunere.proprietate: "linie_planificata"` îl disting de alte predicții. În `pasi` poate apărea `cautare_strada` (cu `tip_cautat: "linie"`, `segment`, `linie` = fereastra) și/sau `analiza_harta`, apoi `predictie` și `scor`; `neaplicat` nu are element pe hartă. Contractul (`contracts/`) nu s-a schimbat.
