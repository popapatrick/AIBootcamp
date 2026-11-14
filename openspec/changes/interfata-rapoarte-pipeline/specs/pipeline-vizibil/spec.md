# Spec Delta

## Purpose
Utilizatorul vede de ce s-a schimbat rețeaua: pașii parcurși și diferențele produse.

## ADDED Requirements

### Requirement: Buton Show pipeline
The system SHALL provide a "Show pipeline" action after each processed report that lists, in order, the steps run (extraction, standardisation, element matching, scoring, decision) with the key input and output of each step.

#### Scenario: Raport procesat
- **WHEN** utilizatorul apasă „Show pipeline" după un raport
- **THEN** apar pașii cu rezultatele lor, inclusiv metoda de potrivire și scorul

### Requirement: Lista schimbărilor din rețea
The system SHALL list every change the event produced in the network (added, updated, prediction, not applied, conflict) with score before and after and a "de ce" explanation.

#### Scenario: Predicție neaplicată
- **WHEN** scorul e între pragul de predicție și pragul de aplicare
- **THEN** schimbarea apare ca predicție neaplicată, cu scorul și motivul

### Requirement: Data ultimei actualizări
The system SHALL display the date of the last network update, computed from the last applied event.

#### Scenario: După un raport
- **WHEN** un raport modifică modelul
- **THEN** data ultimei actualizări afișată devine data evenimentului aplicat
