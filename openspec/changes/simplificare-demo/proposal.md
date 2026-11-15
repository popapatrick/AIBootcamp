# Proposal

## Why

Demo-ul are funcții care încurcă: scenariul extrem, traseul de ultima oră (buton și parametri), plasarea prin clic, bannerul „DATE FICTIVE” de sus, coduri brute (`in_model`, „Predicție AI”, „generat de model”).

## What Changes

- Scos scenariul extrem (API, motor, UI; fișierul mutat în `data/events/arhiva/`).
- Scos traseul de ultima oră din UI și API; motorul nu mai generează traseu (`demo.trace_generat_activ: 0`), codul rămâne.
- Scoasă plasarea prin clic din UI (`locatie` rămâne în API pentru teste).
- Doar 3 butoane de echipă; apelurile clienților doar în timeline.
- UI fără coduri brute și fără bannerul de sus.

## Capabilities

### New Capabilities
- `simplificare-demo`

### Modified Capabilities

## Impact

- B: `engine.py` (scenariul extrem), `sesiune2.py` (`_trace_generat` oprit), teste.
- C: `backend/api` (endpointuri și câmpuri scoase), prompturile Lovable P1.
