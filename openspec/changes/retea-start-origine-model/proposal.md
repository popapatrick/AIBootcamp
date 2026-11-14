# Proposal

## Why

Rețeaua din KMZ/OSM e singura pe care o considerăm reală: știm că există. Azi toate elementele au scor inițial 0,60, la fel ca ce adaugă sistemul. Pentru demo vrem să se vadă clar diferența: rețeaua de start (cunoscută, acuratețe mare) față de punctele noi și predicțiile generate de model.

## What Changes

- Rețeaua actuală devine „rețeaua de start": fiecare element are `origine: retea_start` și scor inițial mare (`scor.initial_retea_start`, 0,90) în loc de 0,60.
- Se generează puncte suplimentare în zona rețelei (stâlpi și case de-a lungul străzilor OSM), o singură dată, apoi se hardcodează în `data/simulare/puncte-simulare.json` și se încarcă în rețeaua de start cu `origine: retea_start`. Sunt considerate reale, ca restul.
- Tot ce adaugă sistemul după aceea (elemente adăugate, predicții, lanțuri de racordare, trasee propuse) are `origine: generat_model`. Sursa omului din teren rămâne `om_teren` / `confirmat_de: om`.
- Etichetele din UI se schimbă din „Predicție AI" în „Generat de model": AI-ul face doar standardizarea (extracție, geocodare), predicțiile vin din logica noastră (scor, OSM, reguli).

## Capabilities

### New Capabilities
- `origine-elemente`: marcarea rețelei de start, a punctelor generate de model și a celor confirmate de om.

### Modified Capabilities

## Impact

- A: `data/simulare/genereaza_puncte.py` și `puncte-simulare.json` (folder nou al lui A).
- B: `network.py` (încarcă punctele simulate, `origine`), `model.py` (origine pe elemente noi), `weights.yaml`, recalibrare (scorul inițial se schimbă), snapshot și `state.schema.json`.
- C: câmpul `origine` în API, etichete în Lovable (într-un singur prompt, după înghețarea logicii).
- Contract (`contract:`, B): `origine` pe elemente, `predictie.origine`.
- În afara scopului: date reale PPC; punctele simulate rămân fictive.
