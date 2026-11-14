# data/model (rol B, Victor)

Date FICTIVE derivate din `data/network/Retea_JT_PTAB_7812.kmz`.

- `network.geojson`: rețeaua reală din KMZ (noduri cu `serie`, `clasa`; tronsoane cu `categorie`, `clasa`, `capete`). Regenerat cu `python -m backend.engine.network`.
- `network_model.geojson`: modelul cu defectele introduse (nod lipsă, secțiune diferită).
- `defects.json`: defectele și ID-urile lor (referite de rapoartele din `data/reports/`).
- `sample/`: eșantion valid pentru C, folosit când motorul nu e disponibil.
- `events.fallback.json`: evenimente sintetice de rezervă dacă lipsesc cele ale lui A.
- `osm/streets_raw.json`: cache cu străzile OSM (© OpenStreetMap contributors, ODbL). Se reface cu `python -m backend.engine.osm --fetch`.
- `snapshots/`, `timeline.json`, `jurnal.json`: ieșiri exportate de `GridModel.export()`, dacă au fost generate.
