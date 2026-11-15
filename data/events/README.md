# data/events

- `events.json`: scenariul Sesiunii 4, 55 de evenimente `EV4-001…` din cele 55 de rapoarte (1 aug. – 14 nov. 2026), generat cu `scripts/genereaza_scenariu.py` din cache-ul Haiku (`data/cache/`). Nu se editează de mână; se regenerează. Date FICTIVE.
- `events.stub.json`: rezerva A (neschimbată).
- `arhiva/events-sesiune3.json`, `arhiva/events.extreme.json`: scenariile vechi (extrem scos, decizia D7). `engine.model_scenariu("extrem")` cere `events.extreme.json` în `data/events/` și ridică `FileNotFoundError` fără el.
