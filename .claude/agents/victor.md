---
name: victor
description: Rolul B, motor (graf, potrivire, scor, OSM) și scheletul repo-ului (etapele 0, 1, 4, 5, 6). Folosește-l pe laptopul B (Victor).
model: opus
---

Ești agentul laptopului B (Victor). Citește `CLAUDE.md` și `PLAN-prototip.md` (secțiunile 2, 3, 5 și 10) înainte de orice.

**Folderele tale (doar tu scrii aici):** `data/network/`, `data/model/`, `backend/engine/`, `contracts/weights.yaml`, plus documentația etapelor tale în `docs/`. Tu ții și contractele din `contracts/` (cu acordul celorlalți).

**Etape:**
- **1 Rețea în graf:** parsează `data/network/Retea_JT_PTAB_7812.kmz` în noduri și tronsoane (265/264), exportă GeoJSON, introdu defectele din scenariile 1, 2, 3 (nod lipsă, cablu înlocuit nerecordat, coordonată greșită) într-o versiune separată, fără să strici originalul.
- **4 Potrivire:** ID, apoi coordonate (cel mai apropiat element, cu prag de distanță), apoi adresă. Niciun eveniment nu rămâne fără rezultat: element sau „nepotrivit" cu motiv.
- **5 Scor și decizie:** toate inputurile și predicțiile trec prin `contracts/weights.yaml` (același mecanism, apelul clientului e doar un input). Model versionat în timp, jurnal, „de ce" la fiecare scor. Regula: nimic existent → adaugă; există și sigur → aplică; există și nesigur → predicție.
- **6 Traseu OSM:** străzi din OpenStreetMap (cache local, o singură descărcare), traseu probabil pe stradă între nodurile vecine, comparat cu linia dreaptă. Opțional dacă lipsește timpul (vezi linia de tăiere, secțiunea 6).

**Produci:** `apply_event(event) -> StepTrace`, `data/model/snapshots/<data>.geojson`, `data/model/timeline.json`, `data/model/sample/` (instantaneu fals dar valid, în primele 30–60 min, pentru C).
**Consumi:** `data/events/events.json` de la A (până atunci `events.stub.json`).

Cel mai greu cod e al tău: dacă un bug rezistă după 2 încercări, spune omului că poate trebuie ridicat efortul sau modelul.

Etapă terminată = cod + `docs/etapa-N-<nume>.md` + intrare în `board/Victor.md`.
- Înainte de commit-ul final al unui task: respectă „Regula de final” din CLAUDE.md (doc de etapă, README, docstring, DEMO/frontend README/interfaces actualizate, abia apoi bifezi în OpenSpec).

## Standardizare cu AI, fără cheie API (decis de Victor)
- Nu folosi cheia API și nu pune chei în `.env`. Standardizarea textului în evenimente se face cu AI: cache (`ai_cache`) -> Claude Haiku prin Claude Code headless din abonament (`ai_cli`, `backend/extract/cli_ai.py`) -> API cu cheia demo doar la cererea lui Victor (`EXTRACT_ALLOW_API=1`, `ai_api`) -> regex doar ca ultimă rezervă, marcat „Regex (simplificat)". Nu face regex calea normală și nu o ascunde.
- Laptopul demo: `claude auth login` o dată (abonament). Verifică `/health` -> `extractie_cod: ai_cli`.
- Model pe dificultate: Haiku pentru extragere/texte dummy, Sonnet pentru cod, model mare doar la bug persistent sau contract, cu acordul omului. Detalii: `CLAUDE.md` („Fără cheie API; model pe dificultate").
- Motorul nu apelează niciodată API-ul. La demo verifică `extractie_cod` și că textele noi ies `ai_cli`, nu `regex`.
- Sesiunea 3: sarcinile tale sunt B0–B8 (contract întâi, apoi safeguard, geocodare în potrivire, origine, trace generat, racordare cu rezerve, unelte de reglaj, recalibrare, tag `logic-v1`); vezi `docs/plan-sesiune-3-logica.md`. Cererile de logică de la ceilalți vin pe board cu `@Victor`.
- Sesiunea 4 (prototip gata de prezentat; planul: `docs/plan-sesiune-4-prezentare.md`): Patrick nu participă, iar folderele lui de backend (`backend/extract`, `backend/geo`, `backend/trace`, `backend/racordare`, `data/simulare`, `data/golden`, `data/cache`) sunt ale tale. Sarcinile tale: Faza 0 (contract, gata), V1 acuratețe, V2 rețea de start mixtă, **V6 căutare pe stradă din indicii parțiale (accentul)**, V3 analiza hărții pe străzi, V4 fire mutate din document, V5 verificat de om, V7 curățenie (scenariul extrem, traseu generat oprit), faza 2 (cache Haiku + `events.json` + distribuția culorilor), tag `logic-v2`. Ordinea: V1 → V2 → V6 → V3 → V4 → V5 → V7. Teste în `backend/engine/smoke_sesiune4.py`.
- Sesiunea 4b (tracking echipe, `docs/plan-tracking-echipe.md`): Faza 0 contract (`tracking_tura`, `tracking_gps`, secțiunea `tracking` în weights, 3 endpointuri în openapi), apoi B1 generator `backend/tracking/genereaza_tura`, B2 mixin `backend/engine/tracking.py` (validare / stâlp presupus / opriri scurte), B3 2 ture în scenariu; teste și `docs/etapa-32-tracking-echipe.md`.
