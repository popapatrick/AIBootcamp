# backend/geo (A)

`geocodeaza(referinta, strazi, cfg)`: locație aproximativă din adresă, doar din cache-ul OSM local (`engine.osm.strazi()`). Fără servicii externe, fără chei. Date FICTIVE.

Intrare: `referinta.adresa_structurata {strada, numar, localitate, reper}` sau `referinta.adresa` (text liber; număr detectat cu „nr. N" sau cifre la final). Ieșire: `{status: gasit|necunoscut, lat, lon, precizie_m, metoda: osm_cache|ai_estimare, acuratete, motiv}`.

Ordine: (1) nume normalizat (`backend.trace._norm`: fără diacritice/prefixe) cu toate cuvintele numelui în text; (2) „X colț cu Y" / „X & Y" = vârfurile cele mai apropiate (dacă la > 2*precizie_intersectie+30 m, cade pe strada X); (3) dacă (1) eșuează, `cli_ai.call_cli` alege DOAR din lista de nume din cache; răspuns în afara listei sau CLI oprit = `necunoscut`. Cache AI doar în proces.

Acuratețe = `cfg.geocodare.acuratete[intersectie|strada_numar|strada|reper]`, x `factor_ai_fuzzy` dacă a ales AI. Precizie: stradă = lungime/2 în [min, max]; număr, intersecție, reper = valori fixe din cfg.

Ipoteze: OSM nu are numere de casă, deci N se pune la fracția `clamp(N/100, 0.1, 0.9)` din cea mai lungă cale a străzii, fără par/impar. Reper fără nume de stradă = `necunoscut`.
`in_afara_zonei` nu se decide aici (punctul e mereu pe o stradă din cache): îl aplică motorul cu `engine.zona.zona_ok`.

Verificare: `.venv/bin/python -m backend.geo.smoke_geo`
