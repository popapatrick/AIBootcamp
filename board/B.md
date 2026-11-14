# Panou laptop B

Scrie doar aici. Intrări noi deasupra. Format: ora, gata, în lucru, blocat / am nevoie de la X, contract atins.

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
