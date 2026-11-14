# Design

## Decisions

- `origine` ∈ {`retea_start`, `generat_model`}; `confirmat_de: om` rămâne separat (un element generat de model și confirmat de om are ambele).
- Generarea punctelor simulate (A): de-a lungul străzilor OSM din zonă, la distanța mediană dintre stâlpii existenți, fără suprapunere (≥ 2,5 m de nodurile existente, regula nodului nou), număr limitat (de ex. 40 de stâlpi + 15 case), seed fix, ieșire hardcodată în fișier JSON versionat. Rularea scriptului nu face parte din demo.
- Scorul inițial `initial_retea_start` e mare, nu 1,0: „nimeni nu l-a verificat recent" rămâne adevărat pentru scăderea în timp. `initial_element_kmz` rămâne pentru compatibilitate (valoarea veche, nefolosită pentru elementele de start).
- Schimbarea scorului inițial modifică calibrarea (praguri, scăderea în timp, conflicte): B recalibrează și documentează diferența în `docs/calibrare.md`.
- Scenariile de demo existente care adaugă elemente (nod lipsă, racord nou) rămân neschimbate; elementul adăugat primește `origine: generat_model`.
- Hărți: halou și simbol după `clasa` rămân; originea se arată separat (ex. contur punctat pentru `generat_model`).

## Risks / Trade-offs

- Punctele simulate pot intra în conflict cu predicțiile deja în cache (ID-uri). Regula nodului nou (2,5 m) le separă; recalibrarea verifică.
