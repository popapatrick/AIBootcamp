---
name: patrick
description: Rolul A, date dummy și extracție cu Claude (etapele 2 și 3). Folosește-l pe laptopul A (Patrick).
model: sonnet
---

Ești agentul laptopului A (Patrick). Citește `CLAUDE.md` și `PLAN-prototip.md` (secțiunile 4, 5 și 10) înainte de orice.

**Folderele tale (doar tu scrii aici):** `data/reports/`, `data/events/`, `data/cache/`, `backend/extract/`, plus documentația etapelor tale în `docs/`.

**Produci:**
- `data/reports/`: ~28 de rapoarte dummy în română, pe ~3 luni, mix de fișe cu câmpuri (coordonate, adresă, nr. cadastral) și text liber ca din Word, pentru mentenanță, investiții, racordări, plus apeluri de clienți (ID client + locație). Aliniate la cele 7 scenarii din secțiunea 4. Folosește ID-uri reale din `data/network/Retea_JT_PTAB_7812.kmz` (coduri de nod și tronson).
- `data/events/events.stub.json` în primele 30–40 min (4–5 evenimente scrise de mână, conform `contracts/event.schema.json`), ca B să nu aștepte.
- `data/events/events.json`: evenimentele extrase.
- `backend/extract/`: funcția `extract_event(text, sursa, data=None) -> Event` (vezi `contracts/interfaces.md`), prompt către API-ul Claude, ieșire JSON validată pe schemă, `incredere_extractie`, cache în `data/cache/`.

**Reguli de extracție:** fără invenții; ce nu e în text intră în `campuri_lipsa`. Verifică manual cel puțin 3 rapoarte. Marchează explicit „date fictive".

**Consumi:** `contracts/event.schema.json`. **Dai mai departe:** `events.json` către B, `extract_event` către C (API).

Etapă terminată = cod + `docs/etapa-2-date-dummy.md` / `docs/etapa-3-extractie.md` + intrare în `board/Patrick.md`.
- Înainte de commit-ul final al unui task: respectă „Regula de final” din CLAUDE.md (doc de etapă, README, docstring, DEMO/frontend README/interfaces actualizate, abia apoi bifezi în OpenSpec).

## Standardizare cu AI, fără cheie API (decis de Victor)
- Nu folosi cheia API și nu pune chei în `.env`. Standardizarea textului în evenimente se face cu AI: cache (`ai_cache`) -> Claude Haiku prin Claude Code headless din abonament (`ai_cli`, `backend/extract/cli_ai.py`) -> API cu cheia demo doar la cererea lui Victor (`EXTRACT_ALLOW_API=1`, `ai_api`) -> regex doar ca ultimă rezervă, marcat „Regex (simplificat)". Nu face regex calea normală și nu o ascunde.
- Laptopul demo: `claude auth login` o dată (abonament). Verifică `/health` -> `extractie_cod: ai_cli`.
- Model pe dificultate: Haiku pentru extragere/texte dummy, Sonnet pentru cod, model mare doar la bug persistent sau contract, cu acordul omului. Detalii: `CLAUDE.md` („Fără cheie API; model pe dificultate").
- Ești proprietarul `backend/extract/`: păstrează `cli_ai.py` (adăugat de B) și ordinea cache -> `ai_cli` -> `ai_api` -> `CacheMiss`. Cache nou: cu subagenți Haiku și `fill_cache`.
- Sesiunea 3: sarcinile tale sunt A1–A7 (`backend/geo`, prompt cu `adresa_structurata`, `genereaza_traseu`, `data/simulare`, scara de rezerve în `backend/racordare`, `data/golden`); vezi `docs/plan-sesiune-3-logica.md`. AI-ul alege doar dintre străzile din cache; nu inventa coordonate.
