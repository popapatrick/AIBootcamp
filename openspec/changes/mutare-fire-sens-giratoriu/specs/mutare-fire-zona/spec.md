# Spec Delta

## Purpose
Sistemul tratează un mesaj despre fire mutate într-o zonă și îl reflectă în model fără a distruge date.

## ADDED Requirements

### Requirement: Mesaj de mutare fire
The system SHALL accept a report that wires were moved in an area (for example an intersection that became a roundabout) as an event of type `mutare_fire` with area centre, radius and reason.

#### Scenario: Centrul din text
- **WHEN** mesajul conține coordonate și cuvinte ca „sens giratoriu" și „firele nu mai sunt"
- **THEN** evenimentul standardizat are tipul `mutare_fire`, centrul din text și motivul

#### Scenario: Centrul din clic
- **WHEN** mesajul nu conține locația și utilizatorul face clic pe hartă
- **THEN** coordonatele clicului devin centrul zonei

### Requirement: Elemente din zonă devin de verificat
The system SHALL lower the confidence of all elements within the radius, mark them as "de verificat" with a journal entry and a "de ce", and SHALL NOT delete them.

#### Scenario: Zonă cu mai multe elemente
- **WHEN** evenimentul acoperă 6 elemente
- **THEN** toate 6 apar galbene, cu scor scăzut și motivul „mutare fire în zonă"

### Requirement: Traseu nou propus pe străzi
The system SHALL propose a dotted new route along nearby streets for the affected connections, with a proposal score, and SHALL NOT apply it unless its score passes the apply threshold.

#### Scenario: Străzi OSM disponibile
- **WHEN** există străzi OSM în jurul zonei
- **THEN** harta arată traseul propus punctat și pipeline-ul îi explică scorul

#### Scenario: Fără străzi
- **WHEN** nu există străzi apropiate
- **THEN** elementele sunt doar marcate, iar jurnalul spune că nu s-a putut propune traseu

### Requirement: Confirmare ulterioară
The system SHALL let a later confirming report restore or replace the affected elements through the normal confirmation rule.

#### Scenario: Raport de confirmare
- **WHEN** un raport ulterior confirmă un element din zonă
- **THEN** scorul lui crește conform regulii de confirmare și starea ajunge verde
