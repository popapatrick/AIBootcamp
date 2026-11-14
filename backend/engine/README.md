# backend/engine (rol B, Victor)

Motorul modelului: rețeaua în graf, potrivire, scor, decizie, traseu pe străzi (OSM). Date FICTIVE (PTAB 7812).

| Fișier | Ce face | Doc |
|---|---|---|
| `network.py` | citește KMZ-ul, noduri + tronsoane, `clasa` (casa/important/origine/post, aerian/ramura/subteran) | `docs/etapa-1-retea-graf.md`, `etapa-9-aspect-harta.md` |
| `defects.py`, `sample.py` | defectele introduse în model, eșantion pentru C | `docs/etapa-1-retea-graf.md` |
| `match.py` | potrivire pe ID, coordonate, adresă | `docs/etapa-4-potrivire.md` |
| `scoring.py`, `config.py` | scor, praguri, ponderi din `contracts/weights.yaml` | `docs/etapa-5-scor-decizie.md` |
| `model.py` | `GridModel`: apply_event, snapshot, timeline, statistici, decizia omului | `docs/etapa-5-scor-decizie.md`, `etapa-14-verificare-om.md` |
| `sesiune2.py` | mutare fire, demontat, val de apeluri, trace, cerere de racordare | `docs/etapa-15-motor-sesiune2.md` |
| `osm.py` | traseu pe străzi, `strazi()` pentru modulele lui A (cache `data/model/osm/`) | `docs/etapa-6-traseu-osm.md` |
| `engine.py` | interfața publică pentru API: `apply_event`, `snapshot`, `timeline`, `statistici`, `aplica_decizie`, `model_scenariu`, `reset` | `contracts/interfaces.md` |
| `calibrare.py`, `fallback_events.py` | rulare pe evenimente reale, rezervă fără date de la A | `docs/calibrare.md` |

## Rulare și verificare
```bash
python3 -m venv .venv && .venv/bin/pip install -r backend/engine/requirements.txt   # o singură dată
.venv/bin/python -m backend.engine.smoke_network    # rețea, clase KMZ
.venv/bin/python -m backend.engine.smoke_match      # 13 cazuri
.venv/bin/python -m backend.engine.smoke_engine     # 36 verificări
.venv/bin/python -m backend.engine.smoke_sesiune2   # 23 verificări
.venv/bin/python -m backend.engine.smoke_osm        # 9 verificări
.venv/bin/python -m backend.engine.calibrare        # decizii pe evenimentele reale
```

## Reguli
Ponderile și pragurile vin doar din `contracts/weights.yaml`. Contractele se schimbă prin commit `contract:`. Ce lipsește se marchează, nu se inventează.

## Sesiunea 3
- `zona.py`: safeguard-ul zonei prototipului (`centru_retea`, `zona_ok`, `motiv_afara`); vezi `docs/etapa-20-safeguard-zona.md`.
