# Proposal

## Why

Timeline-ul are 29 de evenimente, aproape toate „scor actualizat”; rețeaua nu se schimbă vizibil. Evenimentele trebuie să vină din rapoarte text standardizate cu AI.

## What Changes

- ~55 de rapoarte text (1 aug. → 14 nov.) după o rețetă care adaugă, scoate, mută și verifică elemente.
- Standardizare cu Haiku (`ai_cli`) în cache, `events.json` generat determinist din texte + cache.
- Distribuția culorilor la 15 nov. verificată automat.
- Texte noi pentru butoanele echipelor (5/echipă, o treime doar stradă + indiciu) și cardurile paginii de intro.

## Capabilities

### New Capabilities
- `scenariu-timeline-realist`

### Modified Capabilities

## Impact

- C: textele în `data/reports/` (preluat de la A), `exemple-dummy.json`, `demo-intro.json`.
- B: cache (`fill_cache`), `scripts/genereaza_scenariu.py`, `data/events/events.json`, calibrare, `verifica_reglaje` (distribuție), referința de aur.
