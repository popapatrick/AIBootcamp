# data/golden (rol A)

Date de aur pentru logica sesiunii 3 (A6). Date FICTIVE; străzile sunt din cache-ul OSM, ID-urile din `data/model/network.geojson`.
Coordonatele așteptate se CALCULEAZĂ în `genereaza_golden.py` din `osm.strazi()`, rețea și `weights.yaml` (nu sunt scrise de mână).

## Ce citește bancul (`backend/api/banc_logica.py`)
`data/golden/*.json` = LISTĂ de `{id, sursa, text, data, asteptat, asteptat_detaliu}`; `sursa` = mentenanta | investitii | racordari | apel_client | om_teren.
Bancul compară doar cheile din `asteptat`: `tip, decizie, nivel, origine, slaba, treapta, eronat_prototip, element_id` (generatorul verifică prin assert că nu apar altele). `asteptat_detaliu` e ignorat de banc.

| Fișier | Cazuri | Ce verifică |
|---|---|---|
| `geocodare.json` | 8 | ID existent, coordonate în text, stradă+număr, intersecție, doar stradă, ortografie greșită, doar reper, stradă necunoscută |
| `racordare.json` | 6 | treptele 1, 2, 3 (două, una la ~2,9 km), în afara zonei (3,1 km), fără locație |
| `zona.json` | 6 | 40 km, 5 km, 3,1 km, 4 km (apel), 2,9 km și centrul (în zonă) |

Valorile `nivel`/`slaba` vin din specificații (praguri, treptă), NU din rularea motorului: bancul arată diferențele, iar reglajele sau calibrarea le explică. Cazurile `om_teren` n-au text cu coordonate; rămân doar în `detaliu/zona.json`.

## `detaliu/` (nu e citit de banc)
Nivelul fin, pentru teste directe pe module: `{id, intrare, asteptat, toleranta, nota}` în `{_nota, centru_zona, raza_zona_m, cazuri}`.
- `geocodare.json` (13): `asteptat {status, metoda, lat, lon, nivel, acuratete (din weights.yaml), precizie_m_max}`; `toleranta`: `{metrica: "pe_strada", strada, dist_max_m}` (punctul trebuie să fie pe stradă; OSM nu are numere de casă) sau `{metrica: "distanta", dist_max_m}`. Intersecțiile se calculează pe cea mai lungă cale a fiecărei străzi, ca `backend.geo`.
- `trace.json` (7): `intrare {punct, adresa, params (suprascrie trace_generat), seed}`; `asteptat {oprire_gasita, durata_min_cel_putin, oprire_la_punct_m_max, contradictie, sens_acuratete}`; `None` = nu se verifică (zgomot mare/acoperire mică pot rata oprirea). Cazul 07 cere același traseu ca 01.
- `racordare.json` (7): `asteptat {status_in, treapta, slaba, nod_start, distanta_directa_nod_m, in_zona}`; treapta 4 se verifică cu `net: "gol"` (rețea fără noduri).
- `zona.json` (7): `asteptat {eronat_prototip, semnal, decizie, distanta_m, raza_m}`, inclusiv `om_teren` la 40 km.

## Regenerare
`.venv/bin/python data/golden/genereaza_golden.py` (determinist; `data/` nu e pachet, rulăm ca script). Se rulează doar când se schimbă rețeaua, străzile sau `weights.yaml`; fișierele se comit.

Verificat manual cu `backend.geo`, `backend.trace`, `backend.racordare` (11 cazuri geo, 7 trace, 6 racordare): potrivesc, cu excepțiile din `nota` (intersecții, durata opririi cu zgomot 5 m).
