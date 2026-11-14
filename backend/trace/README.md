# backend/trace (rol A)

Locația unui stâlp din traseul GPS al tabletei (ultima oră). Funcții pure, fără rețea; parametrii vin din `contracts/weights.yaml` (secțiunea `trace`).

- `gaseste_opriri(puncte, cfg)` – grupează punctele în opriri (rază și durată minimă din cfg).
- `localizeaza(trace, adresa, net, strazi, cfg)` – potrivește adresa cu o stradă, alege oprirea cea mai lungă de lângă ea; ambiguitate și fără stradă scad `calitate`.
- `net` = `backend.engine.network.load_network()`, `strazi` = `backend.engine.osm.strazi()`.

Verificare: `.venv/bin/python -m backend.trace.smoke_trace`. Date: `data/reports/trasee-dummy.json`. Doc: `docs/etapa-16-trasee-dummy.md`.
