# Etapa 9: aspectul hărții ca în KMZ (B)

Date FICTIVE. Parte din schimbarea OpenSpec `harta-aspect-kmz`.

## Ce face
Fiecare element din `network.geojson` și din `snapshot()` are `clasa`, derivată de motor (`network.clasa_element`):
- noduri: serie 7 = `casa` (verde în KMZ), serie 5 și 6 = `important` (gri), origine plecare JT = `origine` (portocaliu), post = `post`;
- tronsoane: `aerian` (albastru 1f5fbf), `ramura` (turcoaz 17a2b8), `subteran` (roșu d62728);
- elemente fără serie/categorie (adăugate sau prezise din rapoarte): nod = `casa`, tronson = `aerian`.

Starea de verificare rămâne separată (`nivel`, `scor`, `ultima_verificare`, `confirmat_de`): UI-ul o desenează ca halou peste simbolul clasei.

## Cum se verifică
```bash
.venv/bin/python -m backend.engine.smoke_network   # așteptat: OK + OK: clase KMZ
```

## Decizii și limite
- „Casă" = serie 7 e o presupunere din simbolul KMZ (nu scrie explicit nicăieri).
- `clasa` e calculată în motor, ca toți clienții (Lovable, plan-B) să folosească aceeași regulă.
- Tronsoanele noi sunt mereu `aerian` (simplificare).

## Ce trebuie să știe ceilalți
- C: folosiți `properties.clasa` pentru simbol; paleta e în `openspec/changes/harta-aspect-kmz/design.md`. Halou: verde = verificat recent sau `confirmat_de: om`, galben = neatins, punctat = `nivel: predictie`, roșu = conflict.
