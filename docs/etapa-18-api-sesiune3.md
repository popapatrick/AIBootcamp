# Etapa 18: API sesiunea 3 (C1), bancul de logică și `/reguli` (C2), prompt Lovable netrimis (C4)

Rol C. Cod în `backend/api/` (`main.py`, `pipeline.py`, `sources.py`, `smoke_api.py`, `banc_logica.py`), prompt în `frontend/lovable-prompt-sesiune3.md`. Contract: commit `3517dfa`. Datele sunt FICTIVE.

## Ce face
**C1, pass-through pentru câmpurile sesiunii 3**
- `POST /rapoarte` acceptă `trace_params` (`puncte`, `zgomot_m`, `durata_oprire_min`, `acoperire`, `decalaj_m`, toate numerice, opționale); ajunge în `detalii.trace_params` al Event-ului. Valorile lipsă nu se trimit (motorul folosește `weights.trace_generat`).
- Câmpurile produse de motor trec neatinse: `detalii.geocodare`, `detalii.trace_sursa`, `modificari[].origine`, `predictie.slaba` / `predictie.treapta`, `eronat_prototip`, `adresa_structurata`.
- Pas nou `geocodare` în `pasi`, imediat după `extractie`, doar dacă Event-ul (sau rezultatul extracției) are `detalii.geocodare`. Nu se inventează pasul altfel.
- `GET /retea` adaugă `zona = {centru: {lat, lon}, raza_m}`: din `engine.zona.zona_ok` dacă există (B1), altfel centroidul nodurilor rețelei de start + `zona.raza_max_m` din `weights.yaml` (la start: 3000 m).
- `GET /geocodeaza?adresa=...`: depanare, apelează `geocodeaza(referinta, strazi, cfg)` din `backend.geo` / motor. Întoarce ce dă funcția (`status`, `lat`, `lon`, `precizie_m`, `metoda`, `acuratete`, `motiv`). **501** „geocodarea nu e încă în motor (B2/A1)" până există funcția.

**C2**
- `GET /reguli`: `contracts/weights.yaml` ca JSON, read-only (ponderi, praguri, zonă, geocodare, trace_generat etc.).
- `python -m backend.api.banc_logica`: rulează texte prin `pipeline.proceseaza` (fără server HTTP, pe modelul din memorie, nu scrie în `data/`), tipărește tabel + sumar.

**C4**: `frontend/lovable-prompt-sesiune3.md`, prompt grupat (origine, contur punctat, predicție slabă/treaptă, banner „eronat în prototip", cerc de zonă, parametri trace, pas „Geocodare"). **NETRIMIS**: se trimite doar după decizia omului și după ce backend-ul întoarce efectiv câmpurile. Cost estimat 3-5 credite.

## Comenzi și rezultat așteptat
```bash
.venv/bin/python -m backend.api.smoke_api                       # ... sesiunea 3: zona 3000 m, /reguli ok, /geocodeaza 501 ... OK: API
API_EXTRACTIE=stub .venv/bin/python -m backend.api.smoke_api    # la fel, OK: API
python3 -m backend.engine.smoke_engine                          # OK: 36 (motorul neatins)
python3 -m backend.api.banc_logica                              # tabel + „Sumar: 29 cazuri, 29 cu asteptat: 22 ok, 7 diferite, 0 erori"
curl -s localhost:8000/reguli | head -c 300
curl -s "localhost:8000/geocodeaza?adresa=Strada%20Liviu%20Rebreanu%2012"   # acum 501
```
Opțiuni banc: `--fisier F`, `--json`, `--doar-diferente`, `--cu-ai` (implicit `EXTRACT_CLI=0`: doar cache din `data/cache/` + regex, fără apel AI). Cod de ieșire 1 dacă există diferențe sau erori.

## Intrări / ieșiri banc
- Intrare: `data/golden/*.json` (fără `calibrare-referinta.json`); dacă folderul lipsește, fallback pe `data/reports/exemple-dummy.json` cu notă „ATENȚIE: data/golden/ nu există".
- Format propus pentru `data/golden` (de confirmat de @Patrick, A6): listă JSON `{id, sursa, text, data?, asteptat?}`. `asteptat` poate avea: `tip`, `decizie`, `nivel`, `origine`, `slaba`, `treapta`, `eronat_prototip`, `element_id`. Se compară doar cheile prezente și nenule.
- Ieșire: coloanele `id, sursa, tip, metoda_cod, decizie, scor, origine, slaba, treapta, eronat, ok`; `-` = lipsă; `ok` = da/nu/- (fără `asteptat`).
- Coloana `element_id` (doar comparată, nu afișată) = elementul referit: `pasi[potrivire].element_id`, apoi `referinta.element_id` din extracție, apoi `modificari[0].element_id`; elementul creat de motor e în `element_modificat` (JSON).
- De unde citește: `modificari[0].origine`, `predictie.slaba/treapta`, `eronat_prototip` din rezultat, `pasi[extractie].metoda_cod`.

## Decizii
- API-ul doar transmite; nu calculează origine, slabă, treaptă, eronat (sunt ale motorului). Până apar, coloanele sunt `-`.
- Zona are rezervă (centroid + weights) ca UI-ul să poată desena cercul înainte de B1.
- Bancul rulează fără AI implicit, ca să fie rapid și determinist (fără cheie, fără `claude`).
- Nicio schimbare în `contracts/` din partea mea.

## Limite (stare curentă)
- Degradat: `/geocodeaza` dă 501 până la A1/B2 (`backend.geo` lipsește); `zona` vine din centroid până la `engine.zona` (B1); `origine`, `slaba`, `treapta`, `eronat_prototip`, pasul `geocodare` apar doar când motorul le produce.
- Bancul e **schelet**: `data/golden/` nu există încă (A6). Pe fallback: 29 cazuri, 22 ok, 7 diferite (`mnt-04, inv-05, rac-04, cer-02, apl-04, om-01, om-02`), 0 erori, toate `ai_cache`. Cauza celor 7 nu e cercetată: `asteptat` din exemple-dummy e orientativ, posibil se compară `element_id` diferit. Nu le trata ca regresii.
- `trace_params` nu e validat pe intervale în API (doar tip numeric); intervalele le va impune motorul / `weights.limits.yaml` (B6).

## Ce trebuie să știe ceilalți
- **@Victor** (contract): `api.openapi.yaml` nu descrie `trace_params` în `POST /rapoarte`, nici `GET /geocodeaza`, nici `GET /reguli`; `zona` e doar în summary-ul `/retea`. Contractul zice „/stare", dar endpoint-ul real e `/retea` (zona e pusă acolo). Banca citește `modificari[0].origine`, `predictie.slaba/treapta` și `out.eronat_prototip`; spune dacă le pui altundeva.
- **@Patrick**: formatul `data/golden` de mai sus; spune dacă diferă.
- Lovable: promptul sesiunii 3 rămâne netrimis.

## C3 runda 1 (2026-11-15)
Comenzi: `python3 -m backend.api.banc_logica` (și `--json`, `--doar-diferente`); `.venv/bin/python -m backend.api.smoke_api` (și cu `API_EXTRACTIE=stub`); `python3 -m backend.engine.smoke_engine` (36 verificări). Toate verzi.
Rezultat banc (fallback exemple-dummy, B3 + A zona_ok intrate): 29 cazuri, **28 ok, 1 diferit** (era 22/7). `origine` apare (`retea_start` / `generat_model`) din `modificari[0].origine`, cum a pus-o B3; nu a trebuit ajustare.
Cauzele celor 7:
- `mnt-04, rac-04, apl-04` (ID inexistent 9999xxx): **banc greșit**. Citea `modificari[0].element_id` (nu există, motorul nu aplică); `asteptat.element_id` e ID-ul din text. Reparat: element referit = potrivire, apoi `referinta.element_id`.
- `om-01, om-02` (NOU-0001/0002): același defect de banc; potrivirea e corectă (`decizie_om`), dar nu există predicția în memorie -> `neaplicat` (așteptat, tinta e „exemplu").
- `cer-02`: banc; motorul creează `NOU-EV-LIVE-004-S1` (lanț din nodul 7101969), așteptatul e nodul de start. Acum ok. Rămâne divergența de logică: nota așteptatului zice „actualizare directă", motorul dă predicție 0,787 (de arătat lui B).
- `inv-05`: **extracție/cache**: „stâlp nou pe Strada Viilor, lângă școală, fără coordonate" -> `linie_planificata` (încredere 0,4), așteptat `nod_lipsa`. Neatins (A2/A6).
`GET /geocodeaza` (TestClient, cu `backend.geo`): „Strada Liviu Rebreanu" -> gasit, osm_cache, 150 m, 0,4; „Strada Regina Maria 5" -> gasit, interpolat, 25 m, 0,55; „strada" și „Strada Inexistenta 99" -> necunoscut; „Rebreanu" -> ai_estimare 0,32; „Calea Victoriei 10 Bucuresti" -> gasit pe „Strada București" (fals pozitiv, 150 m). Semnătura din main.py e corectă; niciun caz in_afara_zonei obținut din text (geo marchează doar coordonate din afara zonei).
Pasul `geocodare` din pipeline: apare doar dacă Event-ul are `detalii.geocodare`; motorul nu cheamă încă `geocodeaza` (doar `match.py` pomenește geocodarea), deci nu apare la niciun caz. Doar raportat.
