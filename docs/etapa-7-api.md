# Etapa 7: API FastAPI (C)

Date FICTIVE, rețea demonstrativă.

## Ce face
`backend/api/` expune modelul rețelei și pipeline-ul pentru UI (Lovable și UI-ul plan B). Pornește în mod „stub" (citește `data/model/sample/`) și trece **automat** pe datele reale când apar: motorul lui B (`snapshot`, `timeline`, `apply_event`), fișierele lui B (`data/model/snapshots/`, `data/model/timeline.json`) și extracția lui A (`extract_event`). `/health` arată ce mod e activ pentru fiecare parte.

## Cum se rulează și se verifică
```bash
python3 -m venv .venv && .venv/bin/pip install -r backend/api/requirements.txt -r backend/engine/requirements.txt
.venv/bin/python -m backend.api.smoke_api          # așteptat: ultima linie „OK: API"
.venv/bin/uvicorn backend.api.main:app --port 8000
curl localhost:8000/health
curl 'localhost:8000/retea?data=2026-09-15' | head -c 300
curl localhost:8000/evenimente
curl localhost:8000/element/A-T-002
curl -X POST localhost:8000/rapoarte -H 'Content-Type: application/json' \
  -d '{"text":"Am înlocuit cablul pe A-T-002 cu TYIR 3x70+54,6 OL-Al","sursa":"investitii","data":"2026-10-15"}'
```
UI plan B (Leaflet): `http://localhost:8000/ui/` (sau `/ui/?api=https://alt-host` pentru alt backend). Documentație interactivă: `/docs`.

## Intrări și ieșiri
| Endpoint | Ieșire |
|---|---|
| `GET /health` | `{status, mod: {retea, evenimente, extractie, motor}, nota}` |
| `POST /rapoarte` `{text, sursa, data?}` | StepTrace (`contracts/interfaces.md`) + `mod` |
| `GET /retea?data=YYYY-MM-DD` | GeoJSON, properties = ElementState (`contracts/state.schema.json`); instantaneul cu data ≤ cea cerută |
| `GET /evenimente` | `[{data, event_id, rezumat, elemente_atinse}]`, sortat; include rapoartele live (`live: true`) |
| `GET /element/{id}` | ElementState + `geometry` + `istoric [{data, nivel, scor, motive}]`; 404 dacă nu există |
| `GET /date` | datele instantaneelor disponibile (extra, nu în contract) |

## Decizii
- **Detectare automată a motorului**: funcțiile lui B/A sunt căutate în `backend.engine[.*]` / `backend.extract[.*]`; nu trebuie schimbat nimic la API când apar.
- **Până la etapa 5 (B)**: potrivirea e reală (`match_event`), scorul e **provizoriu**, calculat cu aceleași ponderi și praguri din `contracts/weights.yaml` (principiul „aceleași ponderi pentru tot sistemul"), marcat explicit „PROVIZORIU" în „de ce".
- **Până la etapa 3 (A)**: extracție stub cu regex, care nu inventează: ce nu găsește intră în `campuri_lipsa`, încredere ≤ 0,6.
- Rapoartele live se țin în memorie (se pierd la restart) și se suprapun pe hartă doar în mod stub; motorul real le aplică singur.
- CORS deschis, pentru Lovable prin tunel.

## Actualizare: legat de motorul real al lui B (etapa 5)
- `/health` arată acum `retea=motor, evenimente=motor, motor=real`; doar `extractie=stub` (aștept etapa 3 de la A).
- Scorul provizoriu din API nu se mai folosește: scorul, decizia și „de ce" vin din `apply_event` al lui B.
- **Fără `data/events/events.json`** (A nu l-a livrat încă) timeline-ul e gol: API-ul folosește data de azi ca dată curentă (`/date` → `[azi]`), iar UI-ul pornește de la azi. Toată rețeaua apare „de verificat" (scorul inițial 0,60 scade în timp). Asta e corect, nu e un bug: nimeni n-a verificat nimic încă.
- Pasul „extracție" din ecranul procesului arată Event-ul complet produs de extracție (B întoarce doar un rezumat).
- Reparat în extracția stub: ID-ul de nod (7 cifre) nu mai e prins din interiorul coordonatelor (ex. `44.2849717`).

## Limite
- Tunel HTTPS: pe laptopul C nu sunt instalate `cloudflared`/`ngrok` (de instalat de om; vezi `frontend/README.md`).
- UI-ul plan B ia Leaflet și harta de fond de pe internet (unpkg, tile OSM).
- Istoricul unui element se reconstruiește din instantanee (doar la datele lor).

## Ce trebuie să știe ceilalți
- @B: exportați `apply_event`, `snapshot`, `timeline` din `backend/engine/__init__.py` (sau unul din modulele `engine`, `model`, `score`, `decision`, `timeline`, `pipeline`) și API-ul le preia singur. `snapshot(None)` nu trebuie suportat; API-ul trimite mereu o dată.
- @A: exportați `extract_event(text, sursa, data)` din `backend/extract/__init__.py` (sau `extract.py`).
