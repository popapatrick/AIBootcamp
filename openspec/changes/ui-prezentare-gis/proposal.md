# Proposal

## Why

UI-ul nu arată prototipul bine: nu există pagină de start, rapoartele nu se văd dinamic pe hartă, nu se vede ce extrage AI-ul, harta nu arată ca un GIS și timeline-ul nu se derulează orizontal.

## What Changes

- Pagină de intro cu 4 exemple („Vezi pe hartă”) și „Resetează demo”.
- Butoanele celor 3 echipe: text → standardizare pas cu pas → zbor la zonă → pulsare → pop-up-uri → timeline la prezent.
- Panoul „Ce a înțeles AI-ul”.
- Hartă tip GIS: straturi, legendă, căutare, panou Identificare cu „Marchează verificat de om”, scară, coordonate.
- Timeline orizontal derulabil, implicit la prezent; vizualizarea căutării pe stradă și a analizei hărții.
- Accesibilitate WCAG 2.1 AA.

## Capabilities

### New Capabilities
- `ui-prezentare-gis`

### Modified Capabilities

## Impact

- C: API (`GET /demo/exemple`, `POST /demo/reset`, `standardizare`, `focus`), 3 prompturi Lovable (P1–P3), checklist, `docs/DEMO.md`.
- B: câmpurile din motor de care depinde (`banda`, pașii noi).
