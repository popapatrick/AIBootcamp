# Design

## Context

Există potrivire pe coordonate, regula nod nou, `osm.py` cu traseu pe străzi și regula de intrare. Distanța tipică între stâlpi se poate calcula din tronsoanele existente (mediana lungimii tronsoanelor).

## Goals / Non-Goals

**Goals:**
- O cerere cu date suficiente actualizează modelul imediat.
- O cerere fără date produce o predicție vizibilă, explicabilă și punctată.

**Non-Goals:**
- Nu dimensionăm cabluri și nu verificăm capacitatea postului.
- Nu geocodăm adrese (locația vine din coordonate sau clic).

## Decisions

- Algoritmul de lanț trăiește în `backend/racordare/` (folder nou, scrie doar A); B îl integrează în model. Împărțirea completă: `docs/plan-sesiune-2-openspec.md`.

- Nodul de racordare e cel mai apropiat nod existent cu clasa potrivită, în raza din `weights.yaml`; dacă sunt mai multe, scorul scade (ambiguitate).
- Lanțul de stâlpi se așază pe cea mai scurtă cale pe străzile OSM, la distanța mediană dintre stâlpii existenți (calculată, nu hardcodată), cu un nod ultim lângă casă.
- Scorul propunerii folosește aceleași ponderi (sursă, extragere, potrivire, urmărire stradă); sursa e `apel_client` sau `formular`, după cum vine cererea.
- Fiecare stâlp prezis e predicție individuală, ca omul să poată accepta lanțul sau doar o parte.

## Risks / Trade-offs

- Pe străzi fără date OSM propunerea cade pe linie dreaptă, marcată cu scor mai mic și „fără stradă" în jurnal.
- Lanțul poate traversa elemente existente; se evită prin regula 2,5 m (nu se creează noduri peste cele existente).
