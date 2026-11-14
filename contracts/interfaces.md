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

## C: API
Vezi `contracts/api.openapi.yaml`. Cu mod stub (citește `data/model/sample/`) până apare motorul.

## Convenții comune
- Date: ISO `YYYY-MM-DD`. Coordonate: WGS84, `lat`, `lon` (în GeoJSON ordinea e `[lon, lat]`).
- ID-uri: nod = codul numeric din KMZ (ex. `6925190`); post = `DX10-2-099812`; tronson = prefix categorie + cod KMZ, pentru că `T-001` se repetă în cele 3 categorii: `A-T-001` (aerian), `R-T-001` (ramuri aeriene), `S-T-001` (subteran). Un raport care zice doar `T-054` e ambiguu și se potrivește cu scor mai mic.
- `data/model/defects.json` conține defectele introduse în model (nod lipsă, cablu înlocuit); rapoartele dummy ale lui A le referă cu aceste ID-uri.
- Tot ce e demo e marcat „date fictive".
