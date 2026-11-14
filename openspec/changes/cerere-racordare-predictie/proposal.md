# Proposal

## Why

Când un client cere să fie racordat o casă, rețeaua trebuie să reacționeze. Dacă există date de intrare (nod, coordonate), modelul se actualizează imediat. Dacă lipsesc date în GIS (stâlpii dintre rețea și casă nu apar nicăieri), sistemul trebuie să încerce să prezică cum ar ajunge rețeaua la casă: ce stâlpi și pe unde, urmând străzile.

## What Changes

- Buton „Cerere racordare casă" cu locația casei (text, coordonate sau clic pe hartă).
- Tip nou de eveniment `cerere_racordare`.
- Dacă există nod sau coordonate care se potrivesc cu rețeaua, racordul se aplică în timp real prin regula de intrare existentă.
- Altfel, sistemul alege cel mai apropiat nod de rețea și propune punctat un lanț de stâlpi și cabluri pe străzile OSM spre casă, cu scor.
- Predicția poate fi acceptată sau respinsă de om (vezi `verificare-om-predictii`).

## Capabilities

### New Capabilities
- `cerere-racordare-predictie`: reacția rețelei la o cerere de racordare, cu actualizare directă sau predicție de traseu.

### Modified Capabilities

## Impact

- `contracts/event.schema.json`: tip `cerere_racordare`; commit `contract:`.
- `backend/engine` (B): propunere de lanț de stâlpi pe străzi (refolosește `osm.py`).
- `backend/extract` (A): prompt și exemple; Lovable (C): buton și clic pe hartă.
