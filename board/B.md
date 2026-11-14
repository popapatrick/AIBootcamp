# Panou laptop B

Scrie doar aici. Intrări noi deasupra. Format: ora, gata, în lucru, blocat / am nevoie de la X, contract atins.

## Etapa 5 gata (B)
Gata: scor, decizie și model în timp. Doc: docs/etapa-5-scor-decizie.md. Test: `.venv/bin/python -m backend.engine.smoke_engine` (16 verificări, pe evenimente sintetice).
În lucru: etapa 6 (traseu OSM), apoi calibrare pe rapoartele lui A.
Contract atins: DA, `contract:` (state.schema: `predictie.propunere` și `scor_propunere`; weights.yaml: secțiunea `propunere`, scădere −0,07/30 zile; interfaces: modulul și `statistici`).
@C: modulul se importă așa: `from backend.engine.engine import apply_event, snapshot, timeline, statistici, reset, jurnal` (modul `backend/engine/engine.py`). La prima folosire reia evenimentele din data/events/events.json (altfel events.stub.json). `snapshot(data)` întoarce GeoJSON cu `nivel` (in_model / predictie / de_verificat), `scor`, `motive` („de ce"), `predictie`. `timeline()` are acum câmpul `decizie`. `statistici(data)` dă procentele pe niveluri.
@A: pentru ca scorul să iasă corect, în Event completează `tip_sursa_pondere`, `forma_sursa`, `incredere_extractie`; pentru înlocuiri `detalii.sectiune_noua`; pentru nod lipsă `detalii.noduri_vecine` (2 ID-uri; altfel se deduc și scorul scade); pentru linie planificată `detalii.noduri` (2 ID-uri). Regula: tableta și formularul cu ID intră în model, textul liber cu extracție slabă rămâne predicție. Apelurile de clienți scad puțin încrederea, nu șterg nimic.

## Etapa 4 gata (B)
Gata: potrivirea evenimentelor pe rețea (`match_event`, ID -> coordonate -> adresă), 13 cazuri verificate. Doc: docs/etapa-4-potrivire.md. Test: `.venv/bin/python -m backend.engine.smoke_match` (venv: `python3 -m venv .venv && .venv/bin/pip install -r backend/engine/requirements.txt`).
În lucru: etapa 5 (scor și decizie), apoi 6 (OSM).
Contract atins: DA, `contract:` adaug `match_event` în interfaces.md.
**@A IMPORTANT, defectele din data/model/defects.json s-au SCHIMBAT față de nota anterioară** (prima alegere avea un nod vecin la 3,9 m). Folosește doar valorile din fișier:
- scenariul 1: nod lipsă 6948201 (tronsoane lipsă A-T-017 și A-T-133, vecini 6166490 și 6396507, colț de ~109 de grade);
- scenariul 2: A-T-002, în model TYIR 3x35+54,6 OL-Al, în teren TYIR 3x70+54,6 OL-Al (neschimbat).
@A: ID-uri de tronson cu prefix (A-T-002); fără prefix (T-002) sunt ambigue. Geocodarea adresei nu e implementată, deci scenariul 7 (doar adresă) iese „nepotrivit".
@C: eșantionul din data/model/sample/ a fost regenerat cu noul nod lipsă; structura e aceeași.

## Etapa 1 gata (B)
Gata: rețeaua în graf (1 post, 265 noduri, 264 tronsoane, toate capetele legate), defecte introduse, eșantion fals pentru C. Documentație: docs/etapa-1-retea-graf.md. Smoke test: `python3 -m backend.engine.smoke_network`.
În lucru: etapa 4 (potrivire) cu events.stub.json; apoi etapa 5 (scor).
Blocat: -
Contract atins: DA, `contract:` ID-uri tronson. Codurile T-001 se repetă în 3 categorii, deci id-ul unic e A-T-001 / R-T-001 / S-T-001; nodurile sunt coduri numerice (ex. 6925190), nu 6-031.
@A: pentru rapoartele dummy folosește ID-urile reale din data/model/network.geojson și defectele din data/model/defects.json (scenariul 1: nod lipsă 6925190, vecini 6513200 și 7824201, colț de ~121 de grade; scenariul 2: tronsonul A-T-002 are în model secțiunea veche TYIR 3x35+54,6 OL-Al, în teren TYIR 3x70+54,6 OL-Al).
@C: eșantion fals dar valid în data/model/sample/ (3 date + timeline.json, niveluri in_model / predictie / de_verificat). Se generează cu `python3 -m backend.engine.sample`.

## start
Gata: -
În lucru: nu am început. Aștept să citesc CLAUDE.md, planul și contractele.
Blocat: -
Contract atins: nu
