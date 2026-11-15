# Interfețe între module

Schimbare aici = commit `contract:` + anunț în `board/` + acord de la cei afectați.

## A → B și C: extracția
```python
# backend/extract/  (proprietar A)
def extract_event(text: str, sursa: str, data: str | None = None) -> dict:
    """Transformă un raport/apel în Event conform contracts/event.schema.json.
    sursa: una din echipa_sursa (mentenanta, investitii, racordari, apel_client).
    Nu inventează: ce lipsește intră în campuri_lipsa. Folosește cache din data/cache/."""
```
Fișier: `data/events/events.json` = listă de Event, sortată după `data`. Până există, `data/events/events.stub.json`.

## B → C: motorul
```python
# backend/engine/  (proprietar B). Modulul de import pentru C: `backend.engine.engine`
#   from backend.engine.engine import apply_event, snapshot, timeline, statistici, reset, jurnal
# La prima folosire reia evenimentele din data/events/events.json (altfel events.stub.json), în ordinea datelor.
def apply_event(event: dict) -> dict:
    """Aplică un Event pe model, întoarce StepTrace pentru ecranul procesului."""

# StepTrace
{
  "event_id": "EV-001",
  "pasi": [
    {"nume": "extractie",  "rezultat": {...}, "incredere": 0.8},
    {"nume": "potrivire",  "rezultat": {"element_id": "6-031", "metoda": "id"}, "incredere": 1.0},
    {"nume": "predictie",  "rezultat": {"metoda": "traseu_strada_osm", "urmeaza_strada": 0.82}, "incredere": 0.7},
    {"nume": "scor",       "rezultat": {"scor_nou": 0.78, "nivel": "in_model"}, "motive": ["..."]}
  ],
  "modificari": [ /* ElementState (contracts/state.schema.json) atinse */ ]
}

def match_event(event: dict, net: dict, weights: dict | None = None) -> dict:
    """Etapa 4. Potrivește evenimentul pe un element. Rezultatul e pasul „potrivire" din StepTrace:
    {status: potrivit|ambiguu|absent_din_model|nepotrivit, element_id, metoda: id|coordonate|adresa|None,
     calitate 0-1, candidati [{element_id, distanta_m}], coordonate_folosite, semnale [...], motiv}.
    `absent_din_model` nu e eroare: așa apar elementele lipsă (nod lipsă, racord nou)."""

def snapshot(data: str) -> dict:
    """GeoJSON FeatureCollection cu starea rețelei la acea dată; properties = ElementState."""

def statistici(data: str) -> dict:
    """{data, elemente, procent: {in_model, predictie, de_verificat}, scor_mediu, verificat_recent_pct}."""

def timeline() -> list[dict]:
    """[{data, event_id, decizie, tip, eticheta, rezumat, elemente_atinse}]; eticheta = mutare_fire | demontat | val_apeluri | racordare | decizie_om | tipul evenimentului; pentru timeline-ul din UI. decizie: adaugat | aplicat | predictie | conflict | de_verificat | scor_actualizat | fara_efect | neaplicat | respins (decizia omului a retras o predicție)."""
```
Fișiere: `data/model/snapshots/<YYYY-MM-DD>.geojson`, `data/model/timeline.json`. Eșantion fals dar valid: `data/model/sample/` (înlocuit de cel real când e gata).

## Sesiunea 2: extinderi de contract (commit `contract:`, B)

### StepTrace: `schimbari`
```json
"schimbari": [ {"element_id": "NOU-…", "ce": "adaugat|actualizat|predictie|neaplicat|conflict|retras|scos_din_uz|de_verificat",
                "scor_inainte": 0.6, "scor_dupa": 0.85, "de_ce": "text"} ]
```
`statistici(data)` primește și `ultima_actualizare` (data ultimului eveniment aplicat sau actualizat).

### Tipuri noi de eveniment (event.schema.json)
- `mutare_fire`: `detalii.centru {lat,lon}`, `detalii.raza_m`, `detalii.motiv_mutare`. Elementele din rază trec „de verificat" (cel mult `mutare_fire.max_elemente`), cu traseu propus pe străzi, neaplicat.
- `activ_demontat`: element scos din uz doar dacă scorul propunerii trece pragul de aplicare; altfel semnal negativ.
- `cerere_racordare`: locația în `referinta.coordonate`. Actualizare directă dacă există date, altfel lanț prezis de stâlpi (`backend.racordare`).
- decizia omului = `tip: verificare`, `echipa_sursa: om_teren`, `tip_sursa_pondere: om_teren`, `detalii.decizie {tinta_id, decizie, motiv}`. O singură decizie pe predicție. Acceptare: predicția devine element real cu `confirmat_de: om`. Respingere: retrasă, penalizare pe metoda propunătoare.

Un refuz al deciziei omului (a doua decizie, predicție necunoscută, decizie invalidă) întoarce StepTrace cu `decizie: neaplicat` și `eroare: {cod: deja_decis | necunoscut | decizie_invalida, mesaj}`; API-ul le traduce în 409 / 404 / 400.

### Completări B5-B8 (aditive)
- `nivel: scos_din_uz` (ElementState) pentru `activ_demontat` cu cel puțin `demontat.rapoarte_min` echipe și scor peste prag.
- `verificat_recent` (bool) în snapshot, din `scor.verificat_recent_zile` (haloul verde în UI).
- StepTrace: pas nou `trace` (rezultatul `backend.trace.localizeaza`) înaintea `potrivire`, când raportul are `detalii.trace` și nu are ID/coordonate; `potrivire` cu `status: zona` pentru `mutare_fire` (centru, raza_m, elemente).
- Motorul: `engine.aplica_decizie(event)` (ridică KeyError/ValueError) și `engine.model_scenariu("extrem")`.
- ID-uri generate: `MUT-<event>-<n>` (traseu propus după mutare), `NOU-<event>-S<n>`, `NOU-<event>-casa`, `NOU-<event>-L<n>` (lanț de racordare).

### Locația operatorului pentru cerere_racordare (aditiv; făcut de C la cererea omului)
Caz: cerere de racordare fără coordonate în text și fără clic; operatorul e la casă. Butonul „Folosește locația operatorului (simulată)" apelează `GET /locatie-operator-demo?text=<descrierea operatorului>` (alias `adresa`; opțional `lat`, `lon` ca indiciu). Răspuns: `{lat, lon, precizie_m, simulata: true, strada, motiv, indicii: [{tip: strada|intersectie|cartier|reper, valoare, gasit}], zona}`. Generare deterministă din text (fără AI): „strada X" dă un punct pe X, „X colț cu Y" lângă intersecție, „cartierul Z" (zonele OSM `is_in`) restrânge la zona Z, combinațiile se intersectează. `precizie_m` reflectă cât de vagă e zona (intersecție 10 m, stradă 15-40 m după lungime, cartier 60 m). Indiciile negăsite apar cu `gasit: false` (reperele mereu, nu avem repere în datele locale). Niciun indiciu găsit: `422` cu `detail: {mesaj, indicii}`, fără punct inventat.
`POST /rapoarte` acceptă `locatie_operator: {lat, lon, precizie_m, simulata: true, zona?}` (`simulata: false` e refuzat cu 422). Motorul îl pune în `detalii.locatie_operator` și îl folosește pentru `cerere_racordare` doar dacă lipsesc `referinta.coordonate` și `detalii.locatie` (prioritate: text, clic, operator). Pașii `potrivire` și `predictie` din StepTrace poartă `sursa_locatie: "text" | "clic" | "operator_simulat"`. Scorul propunerii se înmulțește cu `racordare.factor_locatie_operator` (weights.yaml) și rezultatul nu trece de `predictie` fără decizia omului; jurnalul „de ce" spune că poziția e simulată, cu precizia. `osm.strazi()` întoarce acum și `zona` (eticheta OSM `is_in`, sau null) pe fiecare stradă; `backend.racordare.locatie_operator_demo(text, net, strazi, cfg, lat=None, lon=None)` e funcția pură.

### Metoda de extracție, anunțată în UI (aditiv)
Pasul `extractie` din StepTrace și `/health` poartă `metoda_cod`: `ai_cli` (Claude Haiku prin Claude Code headless, din abonament, fără cheie: `claude auth login` o dată; textul nou se standardizează cu AI și intră în cache), `ai_api` (apel Claude cu cheia demo, doar în ziua demo-ului, `EXTRACT_ALLOW_API=1`), `ai_cache` (rezultat AI generat anterior de un agent Haiku sau de API și păstrat în `data/cache/`) sau `regex` (stub, text nou fără cache). UI-ul afișează câte un semn: „AI (live)" pentru `ai_cli` și `ai_api`, „AI (cache)", „Regex (simplificat)" (ultima rezervă, nu calea normală). Pe hartă, elementele cu `nivel: predictie` sunt marcate „Predicție AI" cu metoda din `predictie.metoda` (traseu_strada_osm, lant_racordare, zona_mutata, pozitie_din_trace, propunere_proprietate); tooltip: scorul și factorii. Atenție la onestitate: extracția folosește AI; predicțiile vin din scor plus străzi OSM, nu dintr-un model de limbaj; UI-ul le numește „Predicție AI" ca să se deosebească de elementele aplicate din rapoarte.

### `clasa` (ElementState)
Noduri: serie 7 = `casa`; serie 5 și 6 = `important`; origine plecare JT = `origine`; post = `post`. Tronsoane: `aerian`, `ramura`, `subteran` după categorie. Elementele fără serie/categorie KMZ (adăugate sau prezise din rapoarte): nod = `casa`, tronson = `aerian` (simplificare pentru prototip).

### Module noi ale lui A (folderele `backend/trace/` și `backend/racordare/`, doar A scrie)
`strazi` = lista întoarsă de `backend.engine.osm.strazi()`: `[{"nume": str|None, "puncte": [[lat, lon], ...]}]` (B o publică). `cfg` = `contracts/weights.yaml` încărcat.
```python
# backend/trace/
def gaseste_opriri(puncte: list[dict], cfg: dict) -> list[dict]:
    """puncte = [{t: ISO datetime, lat, lon}]. Întoarce opriri în ordine cronologică:
    [{lat, lon, durata_min, inceput, sfarsit, n_puncte}]. Rază cfg.trace.raza_oprire_m, minim cfg.trace.durata_min_min."""

def localizeaza(trace: list[dict], adresa: str | None, net: dict, strazi: list[dict], cfg: dict) -> dict:
    """Întoarce {status: gasit|ambiguu|fara_opriri, opriri, strada: {nume, distanta_m}|None,
    alegere: {lat, lon, durata_min, element_id|None, distanta_element_m}|None,
    vizitate: [{element_id, durata_min}], ambiguitate: bool, calitate: 0-1, motiv}.
    Adresa dă strada (potrivire pe nume), traseul dă locul: oprirea cea mai lungă la cel mult cfg.trace.distanta_strada_m de stradă.
    Funcție pură, fără rețea externă."""

# backend/racordare/
def prezice_lant(locatie: dict, net: dict, strazi: list[dict], cfg: dict) -> dict:
    """locatie = {lat, lon} a casei. Întoarce {status: lant|linie_dreapta|fara_nod, nod_start: element_id, distanta_m,
    stalpi: [{ordine, lat, lon}], cabluri: [{de_la, la, puncte}], urmeaza_strada: 0-1|None, ambiguu: bool, motiv}.
    Stâlpii se așază la distanța mediană dintre stâlpii existenți (calculată din net). Funcție pură."""
```
Până la `osm.strazi()`, A poate lucra cu `data/model/osm/streets_raw.json`.

## Sesiunea 3: extinderi de contract (commit `contract:`, B, aditiv)
- `referinta.adresa_structurata {strada, numar, localitate, reper}` (extracție, A). `detalii.geocodare {lat, lon, precizie_m, metoda, acuratete, motiv}`; `metoda` = osm_cache | ai_estimare | trace | necunoscut | in_afara_zonei. `detalii.trace_params`, `detalii.trace_sursa` (simulat | real).
- Elemente: `origine` = `retea_start` | `generat_model` (separat de `confirmat_de`); `predictie.origine` = `generat_model`; `predictie.slaba`; `predictie.treapta` (1-4, racordare). UI: „Predicție AI" dispare; AI = doar standardizarea (`metoda_cod`).
- StepTrace: `eronat_prototip: true` + semnal `in_afara_zonei_prototip` când un punct e la peste `zona.raza_max_m` de centroidul rețelei de start (decizie `neaplicat`, fără excepții pe sursă). `GET /retea` întoarce `zona {centru:{lat,lon}, raza_m}`.
- Racordare: `neaplicat` doar fără locație deductibilă sau în afara zonei; altfel predicție, eventual slabă (`racordare.prag_afisare`).
- `weights.yaml`: `zona`, `geocodare`, `standardizare`, `trace_generat`, `scor.initial_retea_start`, `racordare.{raza_extinsa_m, prag_afisare, factor_*}`. Valorile se pot schimba prin commit `reglaj:` (vezi CLAUDE.md).
```python
# backend/geo/ (A)
def geocodeaza(referinta: dict, strazi: list[dict], cfg: dict) -> dict:
    """Din referinta.adresa_structurata/adresa: {status: gasit|necunoscut|in_afara_zonei, lat, lon, precizie_m,
    metoda: osm_cache|ai_estimare, acuratete 0-1 (din cfg.geocodare), motiv}. Doar cache OSM local; AI (cli_ai) alege doar dintre străzile din cache."""
# backend/trace/ (A)
def genereaza_traseu(punct: dict, strazi: list[dict], params: dict, seed: str) -> list[dict]:
    """Traseu simulat de 60 min lângă punct: [{t, lat, lon}], determinist pe seed; params = cfg.trace_generat suprascris."""
# backend/engine/zona.py (B)
def zona_ok(lat: float, lon: float, net: dict, cfg: dict) -> dict:
    """{ok: bool, distanta_m, raza_m, centru}; centru = centroidul nodurilor rețelei de start."""
```
`prezice_lant` întoarce și `treapta` (1-4); `cfg.racordare.raza_extinsa_m` activează treapta 2.

## Timeline derulabil (commit `contract:`, B, aditiv)
Fiecare element din `timeline()` (și din `GET /evenimente`) are acum și `schimbari[]` (aceleași ca în StepTrace: `{element_id, ce, scor_inainte, scor_dupa, de_ce}`), `pasi[]` (pașii StepTrace: extracție, geocodare, trace, potrivire, predicție, scor, cu `rezultat` și `motive`) și `eronat_prototip`. UI-ul își construiește lista derulabilă din ele: data, `eticheta`, `decizie`, scor înainte -> după, elemente atinse (`elemente_atinse`) și „De ce?" (`pasi`) la clic; harta la data evenimentului vine din `GET /retea?data=` (sesiunea 4: fără `&scenariu=extrem`).

## Sesiunea 4: prototip gata de prezentat (commit `contract:`, B; planul: `docs/plan-sesiune-4-prezentare.md`)
Patrick nu participă: `backend/extract`, `backend/geo`, `backend/trace`, `backend/racordare`, `data/simulare`, `data/golden`, `data/cache` trec la B; `data/reports` trece la C.

**Acuratețe (D5, D6, P1, P2; `weights.yaml`: `acuratete`, `retea_start`, `plafon_locatie`, `culori`).**
- Rețeaua GIS (KMZ) pornește la `acuratete.initial_gis` 0,95 și scade cu `scadere_gis_per_30_zile`, nu sub `minim_gis` (contradicțiile pot coborî mai jos).
- Punctele simulate SIM-* sunt „din rapoarte mai vechi”: `origine: generat_model`, `t0: true`, scor ales determinist pe ID din `retea_start.scor_galben|portocaliu|rosu`, în proporțiile `fractie_*`.
- Orice element creat sau mutat dintr-un raport are scorul ≤ `plafon_locatie[sursa_locatie]`; un raport ulterior cu sursă mai bună ridică plafonul.
- Raport de teren executat (mentenanță/investiții, `status: executat`): aplicat de la `acuratete.aplicat_raport_executat` 0,50 (linie plină, culoare după scor). Restul: `praguri.aplicat` 0,75.
- `banda` (ElementState și jurnal): verde ≥ `culori.verde`, galben ≥ `culori.galben`, portocaliu ≥ `culori.portocaliu`, altfel roșu. Calculată de motor; UI-ul doar o afișează.

**Verificat de om (D10).** Eveniment nou `verificare_om` (`echipa_sursa: om_teren`, `detalii.tinta_id`, `motiv`), din `POST /element/{id}/verificare`: scor `verificat_om.scor` 1,0, `verificat_om: true`, `verificat_om_data`, `confirmat_de: om`; pe o predicție o și aplică. Scade cu `verificat_om.scadere_per_30_zile`, nu sub `minim`. Un raport ulterior care contrazice: `verificat_om` → false, scor recalculat + contradicție, jurnalul notează. „Acceptă” pe o predicție se comportă la fel.

**Căutare pe stradă (D11, V6; `cautare_strada`).** Extracția pune în `referinta.adresa_structurata.indiciu` `{tip: numar|langa|vizavi|intre|dupa|inainte|capat|inceput|colt|element|parte, numar, numar_2, strada_2, element_id, distanta_stalpi, paritate}`. `backend.geo` întoarce o fereastră pe stradă (ancore din rapoarte anterioare, altfel convenția de numerotare). Motorul caută elementele de tipul cerut în fereastră: 1 candidat = potrivit (calitate `calitate_cautare_unic`), 2–`max_candidati_predictie` = predicție pe cel mai apropiat cu `predictie.alternative`, 0 = element nou (dacă tipul îl cere) sau „de verificat” la punctul estimat. Pas nou în StepTrace: `cautare_strada` `{strada, de_la_m, pana_la_m, punct, precizie_m, metoda: ancore|conventie|indiciu, indiciu, ancore[], candidati[], ales}`. `neaplicat` rămâne doar fără niciun indiciu de loc sau în afara zonei.

**Analiza hărții (D4, V3; `analiza_harta`).** Predicțiile de legătură (racordare, nod lipsă departe, mutare fire) merg pe graful de străzi OSM local, nu în linie dreaptă: `predictie.metoda: traseu_pe_strazi`, `predictie.traseu`, `predictie.alternative`. Pas nou în StepTrace: `analiza_harta` `{tinta, bransament_m, ales{de_la, lungime_m, strazi[], stalpi_noi, stalpi_reutilizati, traseu}, alternative[], acuratete, explicatie[]}`. Fără drum pe străzi: linie dreaptă, scor `fara_drum`.

**Fire mutate din document (V4; `mutare_fire_document`).** `mutare_fire` fără `detalii.centru`: centrul vine din `detalii.intersectie {strada_1, strada_2}` geocodată (rază `raza_intersectie_m`); traseul nou ocolește centrul pe străzi, preferând `detalii.strada_noua`. Dacă traseul nou e aplicat (raport executat, P1), tronsoanele aeriene vechi din zonă trec pe `nivel: scos_din_uz` cu scor mic („demontat probabil”, gri punctat în UI), fără să fie șterse; traseul nou = tronsoane `MUT-<event>-<n>` cu pași `analiza_harta`.

**Scoase (D7, D9).** Scenariul extrem (`?scenariu=extrem`, `events.extreme.json` → `data/events/arhiva/`), `GET /trasee-demo`, `trace_params` și `trace` din `POST /rapoarte`; `demo.trace_generat_activ: 0` oprește traseul generat în motor (codul rămâne). `locatie` (clic) rămâne în API pentru teste, neutilizat în UI. `GET /exemple` doar pentru `mentenanta`, `investitii`, `racordari`.

**API nou (C).** `POST /element/{id}/verificare`, `GET /demo/exemple`, `POST /demo/reset`, `GET /legenda`; `standardizare` și `focus` în `POST /rapoarte`; `banda`, `verificat_om`, `sursa_locatie`, `t0`, `eticheta_origine` în `GET /retea`; `text_original`, `echipa`, `standardizare`, `banda_inainte`, `banda_dupa`, `focus` în `GET /evenimente`. Detalii: `api.openapi.yaml`.

**UI (Lovable).** Nu afișează coduri (`in_model`, `predictie`, `generat_model`): culoare din `banda`, linie plină (în rețea) / punctată (predicție) / gri punctat (demontat probabil), insigne „GIS”, „Din raport”, „Verificat de om”. Fără bannerul „DATE FICTIVE” pe hartă.

## C: API
Vezi `contracts/api.openapi.yaml`. Cu mod stub (citește `data/model/sample/`) până apare motorul.

## Convenții comune
- Date: ISO `YYYY-MM-DD`. Coordonate: WGS84, `lat`, `lon` (în GeoJSON ordinea e `[lon, lat]`).
- ID-uri: nod = codul numeric din KMZ (ex. `6925190`); post = `DX10-2-099812`; tronson = prefix categorie + cod KMZ, pentru că `T-001` se repetă în cele 3 categorii: `A-T-001` (aerian), `R-T-001` (ramuri aeriene), `S-T-001` (subteran). Un raport care zice doar `T-054` e ambiguu și se potrivește cu scor mai mic.
- `data/model/defects.json` conține defectele introduse în model (nod lipsă, cablu înlocuit); rapoartele dummy ale lui A le referă cu aceste ID-uri.
- Tot ce e demo e marcat „date fictive".
