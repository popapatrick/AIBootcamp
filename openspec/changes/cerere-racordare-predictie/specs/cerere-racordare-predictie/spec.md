# Spec Delta

## Purpose
Rețeaua reacționează la o cerere de racordare a unei case: se actualizează direct sau încearcă să prezică traseul.

## ADDED Requirements

### Requirement: Cerere de racordare
The system SHALL accept a house connection request as an event of type `cerere_racordare` with the house location given as text, coordinates or a map click.

#### Scenario: Locație din clic
- **WHEN** utilizatorul apasă „Cerere racordare casă" și face clic pe hartă
- **THEN** evenimentul are coordonatele clicului ca locație

### Requirement: Actualizare directă când există date
The system SHALL apply the connection immediately through the entry rule when the request references an existing node or coordinates that match the network with sufficient score.

#### Scenario: Nod cunoscut
- **WHEN** cererea indică un nod existent și scorul trece pragul de aplicare
- **THEN** racordul apare în model și harta se actualizează imediat

### Requirement: Predicție când lipsesc date
The system SHALL, when the house or its poles are not in the model, predict a chain of poles and cables along nearby streets from the closest network node, each as a dotted prediction with a score.

#### Scenario: Casă fără stâlpi în GIS
- **WHEN** cererea e la 120 m de cel mai apropiat nod și nu există stâlpi între ele
- **THEN** harta arată punctat un lanț de stâlpi spre casă, cu scor pe fiecare și motivul în „De ce?"

#### Scenario: Fără străzi apropiate
- **WHEN** nu există străzi OSM apropiate
- **THEN** traseul e linie dreaptă cu scor mai mic și jurnalul spune „fără stradă"

### Requirement: Acceptare parțială
The system SHALL allow each predicted pole to be accepted or rejected individually.

#### Scenario: Doar primul stâlp acceptat
- **WHEN** omul acceptă primul stâlp și respinge restul
- **THEN** doar primul devine real, iar ceilalți sunt retrași
