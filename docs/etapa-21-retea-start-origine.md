# Etapa 21: rețeaua de start și originea elementelor (B, Sesiunea 3)

Date FICTIVE. Feature OpenSpec: `openspec/changes/retea-start-origine-model/`.

## Ce face (B3 complet)
- Fiecare element al rețelei de start (KMZ/OSM) are `origine: retea_start` și scor inițial `scor.initial_retea_start` (0,90). Tot ce adaugă sistemul (element adăugat, predicție, lanț de racordare, traseu propus) are `origine: generat_model`; `predictie.origine` e tot `generat_model`. `confirmat_de: om` rămâne separat: un element generat de model și confirmat de om are ambele.
- `origine` apare în snapshot (`properties.origine`) și în `modificari[]` din StepTrace. În UI, „Predicție AI" dispare: AI face doar standardizarea (extracție, geocodare); predicțiile sunt ale modelului.

## Cum se verifică
```bash
.venv/bin/python -m backend.engine.smoke_sesiune2   # blocul „origine" (40 verificări)
.venv/bin/python -m backend.engine.calibrare        # decizii neschimbate; scor mediu 0,90 -> 0,76 (27 oct.)
```

## Decizii și limite
- `origine` se pune în `_pune` (prima stare a unui element): rețeaua inițială o setează explicit `retea_start`, orice alt element primește implicit `generat_model`.
- Puncte simulate (A4): `network.incarca_puncte_simulare(net)` încarcă `data/simulare/puncte-simulare.json` (55 de noduri: 40 stâlpi serie 5, 15 case serie 7; 48 de tronsoane) în rețeaua de start când `GridModel()` pornește fără `net` dat; au `origine: retea_start`. Centroidul zonei se calculează după încărcare. Recalibrarea finală (B7) rămâne.
- Date: scorul mediu pornește la 0,90 pe 320 de noduri și 312 tronsoane.
- Impact pe calibrare: vezi `docs/calibrare.md`, secțiunea Sesiunea 3.
- Ce trebuie să știe ceilalți: C expune `origine` în API (C1) și schimbă etichetele (C4, prompt Lovable netrimis); A generează punctele simulate cu `origine: retea_start` implicit (le marchează motorul la încărcare).
