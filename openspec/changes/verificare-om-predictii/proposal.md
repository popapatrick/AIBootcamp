# Proposal

## Why

O predicție a AI-ului rămâne neaplicată până o confirmă cineva. În realitate un om merge în teren și vede dacă stâlpul sau cablul există. Interfața trebuie să permită acest pas: omul acceptă sau respinge predicția, iar rețeaua arată clar ce a fost doar predicția AI-ului și ce a fost confirmat de un om.

## What Changes

- Pe fiecare predicție apar butoanele „Acceptă (verificat în teren)" și „Respinge".
- Decizia omului este un input în același calcul de scor, cu sursă nouă `om_teren` și pondere mare din `weights.yaml`.
- Acceptarea transformă predicția în element real, marcat „confirmat de om"; respingerea o retrage și scade încrederea în metoda care a propus-o.
- Jurnalul și „De ce?" arată cine a decis, când și cu ce scor.
- Se păstrează distincția vizuală: predicție AI (punctat), confirmat de om (plin, halou verde, marcaj „om").

## Capabilities

### New Capabilities
- `verificare-om-predictii`: decizia omului asupra predicțiilor și efectul ei în model.

### Modified Capabilities

## Impact

- `contracts/weights.yaml`: sursa `om_teren`; `contracts/event.schema.json`: `tip_sursa_pondere` include `om_teren`; `detalii.decizie` pentru evenimentul `verificare`; commit `contract:`.
- `backend/engine` (B): aplică decizia; `backend/api` (C): endpoint de decizie; Lovable (C): butoane.
- Refolosește tipul de eveniment `verificare` deja existent.
