# backend/trace (rol A)

Locația unui stâlp din traseul GPS al tabletei (ultima oră). Funcții pure, fără rețea; parametrii vin din `contracts/weights.yaml` (secțiunea `trace`).

- `gaseste_opriri(puncte, cfg)` – grupează punctele în opriri (rază și durată minimă din cfg).
- `localizeaza(trace, adresa, net, strazi, cfg)` – potrivește adresa cu o stradă, alege oprirea cea mai lungă de lângă ea; ambiguitate și fără stradă scad `calitate`.
- `net` = `backend.engine.network.load_network()`, `strazi` = `backend.engine.osm.strazi()`.
- `genereaza_traseu(punct, strazi, params, seed)` – traseu simulat de 60 min (`genereaza.py`): merge pe cea mai apropiată stradă OSM, oprește la punct (+`decalaj_m`) ~`durata_oprire_min`, merge mai departe. `params` = `cfg["trace_generat"]` suprascris: `puncte`, `zgomot_m` (sigma GPS), `durata_oprire_min`, `acoperire` (fracția păstrată), `decalaj_m`. Determinist (seed prin sha256). `punct["t"]` opțional = sfârșitul traseului. Zgomot mare (~>10 m, peste `raza_oprire_m`) sau oprire sub `durata_min_min` => `fara_opriri`.

Verificare: `.venv/bin/python -m backend.trace.smoke_trace`. Date: `data/reports/trasee-dummy.json`. Doc: `docs/etapa-16-trasee-dummy.md`.
