# Design

## Context

Există potrivire pe coordonate (rază 15 m), regula nod nou (2,5 m), propunerile de traseu pe străzi (`osm.py`, `urmeaza_strada`) și semnalul negativ de scor (−0,20 × fiabilitate × calitate potrivire). Lipsește un eveniment care vizează o zonă, nu un singur element.

## Goals / Non-Goals

**Goals:**
- Un mesaj despre o zonă coboară încrederea tuturor elementelor din ea.
- Se propune vizibil un traseu nou, fără a-l aplica.

**Non-Goals:**
- Nu detectăm sensuri giratorii din OSM; locația vine din mesaj sau clic.
- Nu rutăm exact în jurul inelului giratoriului; traseul urmează străzile OSM apropiate.

## Decisions

- Raza implicită 40 m, luată din `weights.yaml` (`potrivire.raza_mutare_m`), suprascriere din mesaj dacă există.
- Fiecare element din rază primește semnal negativ ca la `avarie_semnalata`, scalat cu fiabilitatea sursei; nu e șters.
- Propunerea de traseu leagă nodurile din afara razei care rămân conectate la zonă, pe cea mai scurtă cale pe străzi OSM; apare ca predicție cu scor de propunere și nu se aplică sub prag.
- Locația: dacă mesajul nu are coordonate, UI-ul cere clic pe hartă și le trimite ca `detalii.centru`.

## Risks / Trade-offs

- Dacă OSM nu are străzi lângă zonă, doar marcăm elementele și spunem asta în jurnal.
- Raza arbitrară poate marca prea multe elemente; se limitează numărul de elemente marcate pe eveniment (plafon în `weights.yaml`).
