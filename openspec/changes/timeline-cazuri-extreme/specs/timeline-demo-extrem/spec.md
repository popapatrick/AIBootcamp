# Spec Delta

## Purpose
Un scenariu de evenimente cu cazuri extreme, redat pe timeline, în care contrastul dintre verificat și neatins e clar.

## ADDED Requirements

### Requirement: Încărcare scenariu
The system SHALL provide a "Încarcă rețeaua cu evenimente" action that loads the extreme-case scenario and plays it along the timeline.

#### Scenario: Pornire
- **WHEN** utilizatorul apasă butonul
- **THEN** modelul se reface din evenimentele scenariului și Play parcurge datele în mai puțin de 45 de secunde

### Requirement: Verificat versus static
The system SHALL colour the status halo green for elements verified or applied up to the selected date and yellow for elements untouched by any event up to that date.

#### Scenario: Mijlocul timeline-ului
- **WHEN** slider-ul e la jumătate
- **THEN** elementele atinse de evenimentele de până atunci sunt verzi, iar restul galbene

### Requirement: Ramură construită pe etape
The system SHALL show a branch built across several reports first as dotted predictions and then as confirmed elements when later reports confirm them.

#### Scenario: A doua confirmare
- **WHEN** un al doilea raport confirmă nodul propus anterior
- **THEN** nodul trece din punctat în plin și primește ID real

### Requirement: Segment demontat
The system SHALL support an event of type `activ_demontat` and mark a section as out of service only when the combined score passes the apply threshold.

#### Scenario: O singură mențiune
- **WHEN** un singur raport spune că un tronson a fost demontat
- **THEN** tronsonul rămâne în model, cu semnal negativ și motiv, fără a fi scos

### Requirement: Val de apeluri
The system SHALL aggregate calls from the same area within a configurable window so repeated calls weigh more than one, still using the call source weight and a cap.

#### Scenario: Trei apeluri în aceeași zonă
- **WHEN** trei apeluri apar în 7 zile în raza de potrivire a aceluiași element
- **THEN** semnalul negativ agregat e mai mare decât al unui singur apel și nu depășește plafonul
