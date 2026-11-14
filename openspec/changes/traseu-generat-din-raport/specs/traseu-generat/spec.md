# Spec Delta

## Purpose
La crearea unui raport se generează un traseu simulat al tabletei lângă punctul din raport, iar parametrii lui cresc sau scad acuratețea locației.

## ADDED Requirements

### Requirement: Generare la crearea raportului
The system SHALL generate a deterministic simulated last-hour trace near the report location whenever a report with a location is created, labelled as simulated.

#### Scenario: Raport cu adresă
- **WHEN** se creează un raport cu stradă și fără trace
- **THEN** se generează un traseu de 60 de minute lângă locația geocodată și raportul indică `trace_sursa: simulat`

#### Scenario: Același raport, același traseu
- **WHEN** același raport e procesat de două ori
- **THEN** traseul generat e identic

### Requirement: Parametri configurabili
The system SHALL take trace generation parameters (points, GPS noise, stop duration, coverage, offset) from the weights configuration and allow overriding them per report.

#### Scenario: Suprascriere per raport
- **WHEN** API-ul primește `trace_params` cu zgomot 30 m
- **THEN** traseul folosește 30 m în loc de valoarea implicită

### Requirement: Efectul asupra acurateței
The system SHALL raise location accuracy for long, low-noise, well-covered stops consistent with the address, up to a configured cap, and SHALL lower it for noisy or sparse traces or when the stop contradicts the address.

#### Scenario: Oprire lungă, zgomot mic
- **WHEN** oprirea durează 15 minute, zgomotul e 3 m și oprirea e la 10 m de adresa geocodată
- **THEN** acuratețea locației crește față de cazul fără trace, fără a depăși plafonul de bonus

#### Scenario: Contradicție
- **WHEN** oprirea e la mai mult de `toleranta_adresa_m` de adresa geocodată
- **THEN** acuratețea scade și „De ce?" arată contradicția

### Requirement: Complementar, nu obligatoriu
The system SHALL keep working with the same rules when no trace exists.

#### Scenario: Fără trace
- **WHEN** generarea e oprită sau nu există locație
- **THEN** potrivirea merge pe adresă sau coordonate, fără eroare
