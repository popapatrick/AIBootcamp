# Spec Delta

## Purpose
Cererea de racordare produce o predicție din datele disponibile; punctul casei rămâne pe hartă chiar când datele sunt puține.

## ADDED Requirements

### Requirement: Scară de rezerve pentru locația casei
The system SHALL resolve the house location by trying, in order, explicit coordinates, a map click, address geocoding, a generated trace, and the simulated operator position.

#### Scenario: Doar adresă
- **WHEN** cererea are doar adresă
- **THEN** locația vine din geocodare, cu precizia ei, și lanțul se prezice de acolo

### Requirement: Scară de rezerve pentru lanț
The system SHALL try a street chain from a node within the normal radius, then within the extended radius, then a straight line to the nearest node in the zone, then only the house point.

#### Scenario: Niciun nod în rază
- **WHEN** nu există nod la mai puțin de `raza_nod_m`
- **THEN** se încearcă raza extinsă, apoi linia dreaptă; rezultatul nu e `neaplicat`

#### Scenario: Niciun nod în zonă
- **WHEN** nu există niciun nod utilizabil
- **THEN** casa rămâne pe hartă ca predicție fără lanț, cu motiv

### Requirement: Predicție slabă, nu neaplicat
The system SHALL show a prediction whose score is below the normal prediction threshold but above the display threshold as a weak prediction, never applied without a human decision.

#### Scenario: Scor 0,25
- **WHEN** scorul propunerii e 0,25
- **THEN** elementul apare ca predicție slabă, punctat, cu scorul, treapta și motivul

### Requirement: Singurele cazuri neaplicate
The system SHALL mark a racordare request as not applied only when no location can be derived or the location is outside the prototype zone, and SHALL state which data is missing.

#### Scenario: Fără locație
- **WHEN** cererea nu are coordonate, adresă geocodabilă, clic sau trace
- **THEN** `neaplicat` cu motivul „lipsește locația casei" și lista surselor încercate
