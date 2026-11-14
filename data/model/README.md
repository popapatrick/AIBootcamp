# data/model (rol B, Victor)

Date FICTIVE derivate din `data/network/Retea_JT_PTAB_7812.kmz`.

- `network.geojson`: rețeaua reală din KMZ (noduri cu `serie`, `clasa`; tronsoane cu `categorie`, `clasa`, `capete`). Regenerat cu `python -m backend.engine.network`.
- `network_model.geojson`: modelul cu defectele introduse (nod lipsă, secțiune diferită).
- `defects.json`: defectele și ID-urile lor (referite de rapoartele din `data/reports/`).
- `sample/`: eșantion valid pentru C, folosit când motorul nu e disponibil.
- `events.fallback.json`: evenimente sintetice de rezervă dacă lipsesc cele ale lui A.
- `osm/streets_raw.json`: cache cu străzile OSM (© OpenStreetMap contributors, ODbL). Se reface cu `python -m backend.engine.osm --fetch`.
- `snapshots/`, `timeline.json`, `jurnal.json`: ieșiri exportate de `GridModel.export()`, dacă au fost generate.

## Sesiunea 3
- Rețeaua de start include acum și cele 55 de puncte simulate din `data/simulare/puncte-simulare.json` (A), încărcate de `backend/engine/network.py::incarca_puncte_simulare` când `GridModel()` pornește fără rețea dată; `origine: retea_start`, scor inițial 0,90. Elementele adăugate de sistem au `origine: generat_model`. Zona prototipului (3 km față de centroid) e în `backend/engine/zona.py`. Vezi `docs/etapa-20-safeguard-zona.md` și `docs/etapa-21-retea-start-origine.md`.
- `network.geojson` din acest folder e exportul rețelei KMZ originale, fără punctele simulate (snapshot-urile și `/retea` le conțin).
