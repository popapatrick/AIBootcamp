# Design

## Context

Timeline-ul se construiește din `events.json` (29 evenimente, 4 august - 27 octombrie), iar `GridModel.timeline()` întoarce instantanee pe date. Scorul scade cu 0,05 la 30 de zile, deci elementele neatinse ajung „static". Un apel singur are pondere 0,25.

## Goals / Non-Goals

**Goals:**
- Un scenariu de ~60 s cu cazuri vizibil diferite, nu doar variații de scor.
- Elementele verificate devin verzi, cele neatinse rămân galbene.

**Non-Goals:**
- Nu măsurăm acuratețea pe date reale; datele sunt fictive.

## Decisions

- Cele 4 cazuri: (1) ramură nouă în 3-4 etape: predicție punctată, apoi confirmată; (2) sens giratoriu: fire mutate (vezi `mutare-fire-sens-giratoriu`); (3) segment demontat: după 2 rapoarte de la echipe diferite tronsonul trece în `scos_din_uz`, iar o singură mențiune rămâne doar semnal; (4) val de apeluri: cel puțin 3 apeluri din aceeași zonă în 7 zile cresc semnalul negativ agregat, cu plafon, tot cu ponderea `apel_client`.
- Scenariul extrem e un fișier separat (`events.extreme.json`) selectat cu un parametru, ca să nu stricăm demo-ul de 60 s existent.
- Pragurile noi (nr. de apeluri, fereastra de 7 zile, plafon) merg în `contracts/weights.yaml`, nu în cod.

## Risks / Trade-offs

- Timeline mai lung depășește 1 minut: Play se rulează accelerat (sub 45 s) sau pe etape.
- Valul de apeluri poate părea „inventat" dacă pragurile sunt arbitrare; se documentează ca nu e calibrat.
