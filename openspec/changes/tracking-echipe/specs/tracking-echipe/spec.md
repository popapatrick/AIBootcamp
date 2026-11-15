# Spec Delta

## ADDED Requirements

### Requirement: Tură simulată pe străzi
The system SHALL generate a deterministic simulated tablet tour for a team along local OSM streets, with stops near existing poles, one long stop at a place without a pole and short stops, all inside the prototype zone.

#### Scenario: Aceeași sămânță
- **WHEN** se generează de două ori o tură cu aceeași echipă, dată și seed
- **THEN** punctele sunt identice

### Requirement: Validare prin oprire
The system SHALL confirm an existing pole when a stop of at least `tracking.durata_validare_min` lies within `tracking.raza_validare_m` of it, raising its score through the same scoring rules with source reliability `tracking_gps`.

#### Scenario: Stâlp portocaliu confirmat
- **WHEN** tableta stă 8 minute la 4 m de un stâlp cu scorul 0,50
- **THEN** scorul stâlpului crește (ex. la ~0,64, galben), iar „De ce?” pomenește tura și durata

### Requirement: Stâlp presupus
The system SHALL propose a new pole as a dashed prediction, capped at `tracking.plafon_stalp_presupus`, when a stop of at least `tracking.durata_stalp_nou_min` has no pole within `tracking.raza_fara_stalp_m`.

#### Scenario: Oprire lungă fără stâlp
- **WHEN** tableta stă 15 minute într-un loc fără stâlp în 25 m
- **THEN** apare o predicție `TRK-*` punctată, cu scor ≤ 0,45 și legătură prezisă pe străzi

### Requirement: Opriri scurte ignorate
The system SHALL ignore stops shorter than `tracking.durata_validare_min`.

#### Scenario: Semafor
- **WHEN** tableta stă 1 minut
- **THEN** nu se schimbă niciun scor

### Requirement: Tura în timeline
The system SHALL record each applied tour as a timeline event labelled `tracking`, with per-stop results.

#### Scenario: Tură aplicată
- **WHEN** se aplică o tură
- **THEN** timeline-ul are un eveniment „Tracking echipă” cu validările și presupunerile ei
