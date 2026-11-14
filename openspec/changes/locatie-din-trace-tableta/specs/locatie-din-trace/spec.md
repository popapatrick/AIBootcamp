# Spec Delta

## Purpose
Poziția exactă a stâlpului se deduce din traseul tabletei din ultima oră când adresa introdusă nu e exactă sau completă.

## ADDED Requirements

### Requirement: Preluarea traseului din ultima oră
The system SHALL accept, with a finished-work report from a tablet, the location trace of the last 60 minutes as timestamped points.

#### Scenario: Raport cu trace
- **WHEN** operatorul trimite raportul de lucrare finalizată
- **THEN** raportul conține adresa introdusă și punctele traseului din ultima oră

### Requirement: Detectarea opririlor
The system SHALL group trace points into stops using a radius and a minimum duration taken from the weights configuration, and compute each stop's position and total dwell time.

#### Scenario: Două opriri
- **WHEN** traseul conține o oprire de 12 minute lângă un stâlp existent și una de 25 de minute într-un loc fără stâlp
- **THEN** sunt detectate două opriri cu timpii lor

### Requirement: Corelarea cu adresa
The system SHALL match the entered address to a street by name and prefer stops within 40 m of that street.

#### Scenario: Adresă fără număr exact
- **WHEN** adresa e „Strada Primăverii" fără număr
- **THEN** sistemul reține doar opririle de lângă acea stradă

### Requirement: Locul cel mai lung câștigă
The system SHALL pick the stop with the longest dwell time among the candidate stops as the exact location of the pole.

#### Scenario: Oprire lungă fără stâlp
- **WHEN** oprirea câștigătoare nu are niciun element la cel mult 15 m
- **THEN** se propune un stâlp nou, punctat, la acea poziție, cu scor și explicație (strada, timpul, celelalte opriri)

#### Scenario: Oprire lungă lângă stâlp existent
- **WHEN** oprirea câștigătoare e la cel mult 15 m de un stâlp existent
- **THEN** stâlpul existent e confirmat prin regula normală de confirmare

### Requirement: Fallback, nu înlocuire
The system SHALL use the trace only when the address alone does not match an element, and SHALL mark in the journal that the position came from the trace.

#### Scenario: Adresă suficientă
- **WHEN** raportul are ID sau coordonate valide
- **THEN** trace-ul nu schimbă potrivirea

### Requirement: Ambiguitate scade scorul
The system MUST lower the match quality when the two longest candidate stops have close dwell times.

#### Scenario: Două opriri aproape egale
- **WHEN** diferența de timp dintre primele două opriri e sub prag
- **THEN** scorul scade și rezultatul poate rămâne doar predicție

### Requirement: Traseu simulat în demo
The system SHALL let the demo generate a simulated last-hour trace that is editable on the map, and SHALL provide ready-made traces including a case where the operator verified existing poles and also stayed at a place with no pole.

#### Scenario: Cazul de demo
- **WHEN** se alege traseul „verificat stâlpi și oprit unde nu era stâlp"
- **THEN** stâlpii existenți vizitați primesc confirmare, iar oprirea fără stâlp produce un stâlp prezis punctat
