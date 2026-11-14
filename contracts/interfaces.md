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
    """[{data, event_id, decizie, rezumat, elemente_atinse}] pentru timeline-ul din UI. decizie: adaugat | aplicat | predictie | conflict | de_verificat | scor_actualizat | fara_efect | neaplicat."""
```
Fișiere: `data/model/snapshots/<YYYY-MM-DD>.geojson`, `data/model/timeline.json`. Eșantion fals dar valid: `data/model/sample/` (înlocuit de cel real când e gata).

## C: API
Vezi `contracts/api.openapi.yaml`. Cu mod stub (citește `data/model/sample/`) până apare motorul.

## Convenții comune
- Date: ISO `YYYY-MM-DD`. Coordonate: WGS84, `lat`, `lon` (în GeoJSON ordinea e `[lon, lat]`).
- ID-uri: nod = codul numeric din KMZ (ex. `6925190`); post = `DX10-2-099812`; tronson = prefix categorie + cod KMZ, pentru că `T-001` se repetă în cele 3 categorii: `A-T-001` (aerian), `R-T-001` (ramuri aeriene), `S-T-001` (subteran). Un raport care zice doar `T-054` e ambiguu și se potrivește cu scor mai mic.
- `data/model/defects.json` conține defectele introduse în model (nod lipsă, cablu înlocuit); rapoartele dummy ale lui A le referă cu aceste ID-uri.
- Tot ce e demo e marcat „date fictive".
