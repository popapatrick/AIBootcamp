# Proposal

## Why

Victor vrea o funcție separată de rapoarte care arată cum poziția GPS a tabletei unei echipe validează rețeaua: unde echipa stă lângă un stâlp, stâlpul e confirmat; unde stă mult fără stâlp, sistemul presupune unul. Nu avem tablete reale, deci traseele sunt simulate.

## What Changes

- Generator de ture simulate pe străzile OSM locale, determinist pe seed (`backend/tracking/`).
- Eveniment nou `tracking_tura`: opririle detectate din puncte confirmă stâlpii apropiați (acuratețea crește, poziție GPS) sau presupun stâlpi noi (predicție punctată).
- Sursă nouă `tracking_gps` (fiabilitate 0,60) și secțiunea `tracking` în `weights.yaml`.
- API: `POST /tracking/genereaza`, `POST /tracking/aplica`, `GET /tracking/ture`.
- UI: tab „Tracking echipe” cu animația tabletei și rezultatele dezvăluite la fiecare oprire.
- 2 ture în scenariul timeline.

## Capabilities

### New Capabilities
- `tracking-echipe`

### Modified Capabilities

## Impact

- B: contract, `backend/tracking/` (nou), `backend/engine/tracking.py` (mixin), `scripts/genereaza_scenariu.py`, `data/events/ture-tracking.json`.
- C: `backend/api` (3 endpointuri), prompt Lovable P4, `docs/DEMO.md` (pas nou).
- Independent de rapoarte și de „traseul de ultima oră” (scos în sesiunea 4).
