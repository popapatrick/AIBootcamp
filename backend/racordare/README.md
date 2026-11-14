# backend/racordare (rol A)

`prezice_lant(locatie, net, strazi, cfg)` prezice lanțul de stâlpi de la cel mai apropiat nod până la o casă nouă (cerere de racordare). Funcție pură, fără rețea. Date fictive.

- Nod de start: cel mai apropiat nod. Scara de rezerve (`treapta` în rezultat; scorul îl calculează motorul din ea, cu `factor_*` din `weights.yaml`): **1** nod în `raza_nod_m` (stradă dacă există, altfel linie dreaptă); **2** nod în `raza_extinsa_m` (la fel, cu `motiv`); **3** cel mai apropiat nod oricât de departe, doar linie dreaptă (`motiv`; peste `max_stalpi_prezisi` devine `ambiguu`); **4** rețea fără niciun nod: `status: fara_nod`, fără stâlpi/cabluri, doar casa (rămâne pe hartă). Zona prototipului și `neaplicat` (fără locație/în afara zonei) sunt decise de motor, nu aici.
- Pas între stâlpi: mediana lungimii tronsoanelor existente (fără subterane), din `net` (GeoJSON sau dict motor).
- Drum: dacă o stradă OSM (`osm.strazi()`) e la <= 40 m și de nod, și de casă, se merge pe ea (`lant`, `urmeaza_strada` 1.0); altfel linie dreaptă (`linie_dreapta`, `urmeaza_strada` None; motorul aplică `factor_fara_strada`).
- Peste `max_stalpi_prezisi` se taie lanțul și `ambiguu: true` cu `motiv`.
- Ieșire: `{status, treapta (1-4), nod_start, distanta_m, stalpi[{ordine,lat,lon}], cabluri[{de_la,la,puncte}], urmeaza_strada, ambiguu, motiv}`; capetele cablurilor: id nod, `stalp-N`, `casa`.

Limite: drum doar pe o singură stradă (fără graf între străzi); punctele se prind de vertexul cel mai apropiat; pragul de 40 m e constantă în cod, nu în `weights.yaml`.

## `locatie_operator_demo(text, net, strazi, cfg, lat=None, lon=None)` (adăugat de C la cererea omului)
Poziție GPS DUMMY a operatorului, din textul lui, în zona descrisă. Funcție pură, determinist (seed = hash al textului normalizat), fără AI. Date FICTIVE.

- Indicii: `strada` („strada X", tolerant la diacritice, majuscule, str./bd./sos./cart.), `intersectie` („colț cu", „intersecția", sau două străzi; străzile se taie la <= 25 m), `cartier` (zonele OSM `is_in`, zona = dreptunghiul străzilor ei + 30 m, nu avem poligon), `reper` („lângă ...", mereu `gasit: false`).
- Constrângerile se combină prin intersecție. Punct la >= `racordare.operator_distanta_min_m` de rețea și, dacă se poate, la <= `raza_nod_m` (altfel lanțul nu pornește); pe stradă/intersecție alege capătul cel mai depărtat de rețea, pe cartier după seed; `lat`/`lon` opționale aleg cel mai apropiat punct posibil. Zgomot GPS <= jumătate din `precizie_m`.
- `precizie_m`: intersecție 10, stradă 15-40 (lungime/20), cartier 60 (din `weights.yaml`, `racordare.precizie_*`).
- Ieșire: `{lat, lon, precizie_m, simulata: True, strada, motiv, indicii: [{tip, valoare, gasit}], zona}`. Niciun indiciu găsit sau constrângeri contradictorii: `LocalizareEroare` (cu `.indicii`), nu inventează un punct.

Limite: reguli simple (nume exacte de stradă, fără genitiv „străzii"); intersecția e aproximată prin cele mai apropiate puncte; reperele nu există în datele locale.

Verificare: `.venv/bin/python -m backend.racordare.smoke_racordare`
