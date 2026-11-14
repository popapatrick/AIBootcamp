# Proposal

## Why

Azi, când cererea de racordare nu are nod în rază sau scorul e sub prag, evenimentul ajunge `neaplicat` și nu se desenează nimic. Utilizatorul vrea ca sistemul să prezică din datele disponibile; iar dacă datele chiar lipsesc, punctul casei să rămână pe hartă și sistemul să încerce în continuare.

## What Changes

- Scară de rezerve pentru locația casei: coordonate din text > clic pe hartă > geocodare din adresă > traseu generat/trace > poziția simulată a operatorului.
- Scară de rezerve pentru lanț: (1) nod în `raza_nod_m` pe stradă; (2) nod în `raza_extinsa_m`; (3) cel mai apropiat nod din zonă, linie dreaptă; (4) doar casa, ca predicție fără lanț.
- Predicțiile slabe nu mai sunt `neaplicat`: sub pragul normal de predicție dar peste `racordare.prag_afisare` apar ca „predicție slabă" (punctate, subțiri), cu scorul și motivul. Nu se aplică niciodată fără decizia omului.
- Punctul casei rămâne pe hartă oricând locația e cunoscută și în zonă.
- Singurele cazuri `neaplicat`: nicio locație deducibilă sau punct în afara zonei prototipului; jurnalul spune exact ce lipsește.

## Capabilities

### New Capabilities
- `racordare-cu-rezerve`: cererea de racordare produce întotdeauna o predicție când se poate, cu scară de rezerve și predicție slabă.

### Modified Capabilities

## Impact

- A: `backend/racordare` (scara de rezerve pentru lanț, `prezice_lant` întoarce `treapta`).
- B: `sesiune2.py::_cerere_racordare` (scara pentru locație, nivel „predicție slabă"), `weights.yaml` (`racordare.raza_extinsa_m`, `prag_afisare`), `scoring.py`.
- C: afișare „predicție slabă" și motiv (după înghețarea logicii); teste API.
- Contract (`contract:`, B): `predictie.slaba`, `racordare.treapta`.
- În afara scopului: calibrare pe date reale, decizia omului (există deja).
