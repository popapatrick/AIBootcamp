# data/events

- `events.json`: scenariul Sesiunii 4, 55 de evenimente `EV4-001…` din cele 55 de rapoarte (1 aug. – 14 nov. 2026), generat cu `scripts/genereaza_scenariu.py` din cache-ul Haiku (`data/cache/`). Nu se editează de mână; se regenerează. Date FICTIVE. Conține și 2 evenimente `tracking_tura` (`EV4-T01` mentenanta 2026-09-25, `EV4-T02` investitii 2026-10-30), intercalate cronologic.
- `ture-tracking.json`: definițiile turelor de tracking `{echipa, seed, data, ora_start}` plus `tura` (punctele GPS generate, ca scenariul să nu depindă de modificări viitoare ale generatorului). Se completează cu `EXTRACT_CLI=0 .venv/bin/python scripts/genereaza_ture_tracking.py`; `genereaza_scenariu.py` le citește de aici.
- `events.stub.json`: rezerva A (neschimbată).
- `arhiva/events-sesiune3.json`, `arhiva/events.extreme.json`: scenariile vechi (extrem scos, decizia D7). `engine.model_scenariu("extrem")` cere `events.extreme.json` în `data/events/` și ridică `FileNotFoundError` fără el.
