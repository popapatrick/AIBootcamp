# backend/racordare (rol A)

`prezice_lant(locatie, net, strazi, cfg)` prezice lanțul de stâlpi de la cel mai apropiat nod până la o casă nouă (cerere de racordare). Funcție pură, fără rețea. Date fictive.

- Nod de start: cel mai apropiat în `cfg.racordare.raza_nod_m`, altfel `status: fara_nod`.
- Pas între stâlpi: mediana lungimii tronsoanelor existente (fără subterane), din `net` (GeoJSON sau dict motor).
- Drum: dacă o stradă OSM (`osm.strazi()`) e la <= 40 m și de nod, și de casă, se merge pe ea (`lant`, `urmeaza_strada` 1.0); altfel linie dreaptă (`linie_dreapta`, `urmeaza_strada` None; motorul aplică `factor_fara_strada`).
- Peste `max_stalpi_prezisi` se taie lanțul și `ambiguu: true` cu `motiv`.
- Ieșire: `{status, nod_start, distanta_m, stalpi[{ordine,lat,lon}], cabluri[{de_la,la,puncte}], urmeaza_strada, ambiguu, motiv}`; capetele cablurilor: id nod, `stalp-N`, `casa`.

Limite: drum doar pe o singură stradă (fără graf între străzi); punctele se prind de vertexul cel mai apropiat; pragul de 40 m e constantă în cod, nu în `weights.yaml`.

Verificare: `.venv/bin/python -m backend.racordare.smoke_racordare`
