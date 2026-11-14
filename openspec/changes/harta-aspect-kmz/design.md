# Design

## Context

`data/model/network.geojson` are deja `serie` pe noduri și `categorie` pe tronsoane. Stilurile KMZ: `#s7` verde (148 noduri), `#s6` gri (112), `#s5` (1), `#orig` portocaliu (4), `#pt` post (1); linii `#aer` albastru 1f5fbf, `#ram` turcoaz 17a2b8, `#sub` roșu d62728. Starea de verificare vine din scorul existent (`contracts/weights.yaml`, praguri 0,75 / 0,40).

## Goals / Non-Goals

**Goals:**
- Hartă recognoscibilă față de KMZ.
- Două straturi independente: tip (formă și culoare de bază) și stare (halou).

**Non-Goals:**
- Nu importăm iconițele PNG din KMZ în Lovable; folosim cercuri colorate cu aceleași culori.
- Nu schimbăm calculul scorului.

## Decisions

- `clasa` se calculează în motor, nu în UI, ca toți consumatorii (API, Lovable, plan-B) să folosească aceeași regulă.
- Mapare: serie 7 -> `casa` (verde); serie 6 -> `important` (gri); serie 5 și origine -> `important`/`origine` (portocaliu); post -> `post`.
- Starea: halou verde = verificat în ultimele 45 de zile (sau aplicat), galben = static, contur punctat = predicție, roșu = conflict. Pragurile de „static" se iau din `weights.yaml`, nu se hardcodează în UI.
- Plan-B (Leaflet) se aliniază și el la aceleași proprietăți, ca să avem rezervă.

## Risks / Trade-offs

- Interpretarea „serie 7 = casă" e o presupunere. Dacă e greșită, se schimbă doar tabelul de mapare în motor.
- Halou + simbol pe 265 de noduri poate aglomera harta la zoom mic: se afișează halou doar de la un zoom minim.
