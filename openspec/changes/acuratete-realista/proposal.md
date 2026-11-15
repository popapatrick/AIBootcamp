# Proposal

## Why

La 15 nov. 620 din 630 de elemente de start sunt la 0,72 (galben) din cauza scăderii în timp, iar elementele adăugate de model sunt verzi (0,96) fără coordonate exacte. Rețeaua nu arată realist și nu se schimbă vizibil.

## What Changes

- Rețeaua GIS (KMZ) pornește la 0,95, scade cu 0,01/30 zile, nu sub 0,85.
- Punctele simulate SIM-* sunt „din rapoarte mai vechi”, cu scoruri amestecate (galben/portocaliu/roșu).
- Plafon de scor după sursa locației (coordonate 0,85, adresă cu număr 0,70, intersecție 0,60, stradă 0,55, analiză hartă 0,40, reper 0,35).
- Raport de teren executat aplică de la 0,50; culoarea arată acuratețea poziției.
- 4 benzi de culoare (`banda`), calculate de motor.
- „Verificat de om” pe orice element: 1,0, insignă, se pierde la contradicție.

## Capabilities

### New Capabilities
- `acuratete-realista`

### Modified Capabilities

## Impact

- B: `model.py`, `scoring.py`, `network.py`, `weights.yaml` (contract sesiunea 4), `smoke_sesiune4.py`.
- C: `banda`, `verificat_om`, `sursa_locatie`, `eticheta_origine` în API; `POST /element/{id}/verificare`; UI.
- Extinde `verificare-om-predictii` (sesiunea 2).
