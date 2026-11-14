# Design

## Context

Predicțiile (scor 0,40-0,75) sunt neaplicate. Promovarea există deja când un raport ulterior confirmă elementul. Tipul de eveniment `verificare` există în schemă. Ponderile surselor: tableta 0,90, formular 0,75, text liber 0,55, apel client 0,25.

## Goals / Non-Goals

**Goals:**
- Decizia omului intră prin același calcul de scor, nu ocolește sistemul.
- Se vede în orice moment ce e predicție AI și ce e confirmat de om.

**Non-Goals:**
- Nu construim conturi sau roluri; „omul" e un buton în demo.

## Decisions

- Decizia este un eveniment `verificare` cu `detalii.decizie` (`accepta` sau `respinge`), `referinta` către predicție și sursa `om_teren` (pondere 0,95).
- Acceptare: scor = confirmare × 0,95; trece pragul de aplicare, predicția devine element real cu ID real (sau cel din text), marcaj `confirmat_de: om`.
- Respingere: predicția se retrage; semnalul negativ coboară încrederea în metoda care a produs-o (`metoda` din predicție), nu în elemente reale.
- Decizia se poate lua o singură dată per predicție; a doua încercare e refuzată cu mesaj clar.

## Risks / Trade-offs

- Un om poate greși; de aceea decizia are scor și jurnal, nu e „adevăr absolut". Un raport ulterior contrar o poate contrazice prin regula normală de conflict.
