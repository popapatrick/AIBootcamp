# Etapa 17: locația operatorului pentru cererea de racordare (C, la cererea omului)

Date FICTIVE. Schimbare OpenSpec: `openspec/changes/locatie-operator-racordare/`. Tot lucrul l-a făcut C, la cererea explicită a omului, inclusiv fișiere din folderele lui A (`backend/racordare/`) și B (`backend/engine/`, `contracts/weights.yaml`), ca la commit 31b0847.

## Ce face
O cerere de racordare vine uneori fără locație exactă: textul are doar „casă pe Strada X", nu există clic pe hartă. Operatorul e la casă, cu tableta. Un buton explicit „Folosește locația operatorului (simulată)" cere o poziție GPS DUMMY, generată din textul scris de operator, în zona pe care o descrie. Lanțul de racordare pornește spre acea poziție. Poziția e marcată `simulata: true` peste tot, cu precizie, iar scorul e mai mic decât la clic sau coordonate; rezultatul rămâne predicție (neaplicat) până confirmă omul.

## Cum se verifică
```bash
.venv/bin/python -m backend.racordare.smoke_racordare   # OK: 20 verificări
.venv/bin/python -m backend.engine.smoke_sesiune2       # OK: 30 verificări (7 noi: operator)
EXTRACT_CLI=0 .venv/bin/python -m backend.api.smoke_api # OK: API (și cu API_EXTRACTIE=stub)
curl -G localhost:8000/locatie-operator-demo --data-urlencode "text=casă pe Strada Liviu Rebreanu"
```
Notă: fișierele din `data/cache/` care nu sunt în git pot schimba tipul unui text de buton (ex. „Raport tabletă ... lucrare finalizată" cache-uit ca `verificare`) și pica o aserțiune mai veche din `smoke_api` (`nod_lipsa`); nu ține de această etapă. `smoke_api` setează acum `EXTRACT_CLI=0` ca testele să nu cheme Claude real.

## Intrări și ieșiri
`GET /locatie-operator-demo?text=<descrierea operatorului>` (alias `adresa`; opțional `lat`, `lon` ca indiciu):
```json
{"lat": 44.2849415, "lon": 26.0590695, "precizie_m": 40, "simulata": true, "strada": "Strada Liviu Rebreanu",
 "motiv": "Poziție SIMULATĂ (nu GPS real), generată determinist din textul operatorului: ...",
 "indicii": [{"tip": "strada", "valoare": "Strada Liviu Rebreanu", "gasit": true}],
 "zona": "Strada Liviu Rebreanu"}
```
- `indicii[].tip`: `strada` | `intersectie` | `cartier` | `reper`; `gasit: false` pentru ce nu există în datele locale (se raportează, nu se ignoră). Reperele („lângă școală") sunt mereu `gasit: false`: OSM-ul local are doar străzi.
- Exemple: „strada X" = punct pe X; „strada X colț cu strada Y" = lângă intersecție; „cartierul 1 Decembrie" = doar în zona respectivă (`strada: null`); „Strada Viilor din cartierul 1 Decembrie" = ambele constrângeri.
- `precizie_m`: intersecție 10, stradă 15-40 (lungime/20), cartier 60.
- Eroare `422`, `detail: {mesaj, indicii}`: text lipsă, niciun indiciu găsit sau constrângeri contradictorii. Nu se inventează niciun punct; UI-ul cere clic pe hartă.

`POST /rapoarte` primește `locatie_operator: {lat, lon, precizie_m, simulata: true, zona?}` (cu `simulata: false` => 422). În StepTrace, pașii `potrivire` și `predictie` au `sursa_locatie: "text" | "clic" | "operator_simulat"`; jurnalul „de ce" (pasul `scor`, `motive[0]`) spune „poziția SIMULATĂ a operatorului, ±X m".

## Decizii
- Parsare cu reguli simple, fără AI (nu cere cheie și nu cheamă Claude): normalizare fără diacritice, prescurtări (str., bd., sos., cart.), nume de stradă din `osm.strazi()`.
- `osm.strazi()` întoarce acum și `zona` (eticheta OSM `is_in`, ex. „1 Decembrie"; 20 de străzi o au). Nu există poligon de cartier, deci zona = dreptunghiul străzilor ei plus 30 m.
- Determinist: seed = hash al textului normalizat; zgomot GPS <= jumătate din `precizie_m`. Pe stradă și intersecție se alege capătul cel mai depărtat de rețea (la >= 20 m și <= `raza_nod_m` - precizie de un nod, ca lanțul să pornească); pe cartier după seed.
- Scor: același calcul de propunere, înmulțit cu `racordare.factor_locatie_operator` = 0,8 (`contracts/weights.yaml`, alături de `operator_distanta_min_m` și `precizie_*`). Nivelul nu poate fi `in_model`: poziția simulată nu aplică singură lanțul, nici cu sursă bună (formular).
- Precedența locației: coordonate din text, apoi clic, apoi operator simulat.

## Rezultate (pe exemplul „casă pe Strada Liviu Rebreanu", `apel_client`)
Pe API cu extracție regex (încredere 0,45): cu clic 0,60, cu operator 0,48 (x0,8); ambele `predictie`, lanț de 4 stâlpi de la nodul 6948201. Pe motor cu încredere 0,9: clic 0,713, operator 0,57; sursă `formular` cu operator 0,67 (`predictie`, nu `adaugat`).

## Limite
- Poziția nu e GPS real; e un indiciu generat din text. Demo-ul trebuie să o spună.
- Nume de stradă potrivite exact (fără declinări); intersecția e aproximată prin cele mai apropiate puncte (<= 25 m); „cartier" înseamnă zona OSM `is_in`, aproximată cu dreptunghi; reperele nu se pot localiza.
- Drumul racordării merge pe o singură stradă (limita lui `prezice_lant`); la intersecție lanțul pornește de obicei foarte aproape de un nod (peste 7 m), deci poate fi scurt.

## Ce trebuie să știe ceilalți
- A (Patrick): `backend/racordare/operator_demo.py` e nou; `prezice_lant` nu s-a schimbat. README-ul folderului e completat.
- B (Victor): `sesiune2._cerere_racordare` citește `detalii.locatie_operator` și pune `sursa_locatie`; `osm.strazi()` are cheia `zona`; `weights.yaml` are 5 chei noi sub `racordare`. Comportamentul vechi (text, clic) e neschimbat; smoke-urile tale trec.
- UI (Lovable, făcut de Claudiu): buton „Folosește locația operatorului (simulată)" care apelează endpointul cu textul din câmp, afișează `indicii` (cu `gasit: false` vizibil), `zona` și `precizie_m` (ex. cerc de ±X m), marcaj „simulată", trimite `locatie_operator` în `POST /rapoarte`; la 422 arată `detail.mesaj` și cere clic pe hartă.
