# backend/tracking (rol B)

Tracking echipe (Sesiunea 4b, `docs/plan-tracking-echipe.md`): tură simulată a tabletei unei echipe. Pur, determinist pe seed, fără rețea și fără AI. Parametrii vin din `contracts/weights.yaml`, secțiunea `tracking` (plus `trace.raza_oprire_m`, `culori`, `zona`).

- `genereaza_tura(net, strazi, cfg, echipa, seed, data, scoruri=None, ora_start="08:00:00")` (`genereaza.py`, exportată din `__init__.py`): 3–5 stâlpi existenți + un loc fără stâlp, pe străzi OSM, puncte GPS la `pas_s` secunde cu zgomot. Întoarce `{tura_id, echipa, data, seed, puncte, plan, lungime_m, durata_min, linie_dreapta}`. `plan` e doar pentru depanare și teste; motorul (B2, `backend/engine/tracking.py`, urmează) detectează singur opririle din `puncte` cu `backend.trace.gaseste_opriri`.
- `net` = `load_network()` + `incarca_puncte_simulare(net)`; `strazi` = `backend.engine.osm.strazi()`; `scoruri` = {element_id: scor curent} dat de cine apelează (stâlpii cu bandă nu-verde sunt preferați).

Verificare: `.venv/bin/python -m backend.tracking.smoke_tracking` (rezultat așteptat: `OK: 140 verificări`; intră și în `verifica_reglaje`). Doc: `docs/etapa-32-tracking-echipe.md`.
