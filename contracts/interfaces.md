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
# backend/engine/  (proprietar B)
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

def snapshot(data: str) -> dict:
    """GeoJSON FeatureCollection cu starea rețelei la acea dată; properties = ElementState."""

def timeline() -> list[dict]:
    """[{data, event_id, rezumat, elemente_atinse}] pentru timeline-ul din UI."""
```
Fișiere: `data/model/snapshots/<YYYY-MM-DD>.geojson`, `data/model/timeline.json`. Eșantion fals dar valid: `data/model/sample/` (înlocuit de cel real când e gata).

## C: API
Vezi `contracts/api.openapi.yaml`. Cu mod stub (citește `data/model/sample/`) până apare motorul.

## Convenții comune
- Date: ISO `YYYY-MM-DD`. Coordonate: WGS84, `lat`, `lon` (în GeoJSON ordinea e `[lon, lat]`).
- Cod nod/tronson exact ca în KMZ (ex. `T-001`).
- Tot ce e demo e marcat „date fictive".
