# Spec Delta

## Purpose
Valorile logicii se schimbă din configurație, validat, fără cod; restul schimbărilor trec prin cerere; logica se îngheață cu tag.

## ADDED Requirements

### Requirement: Reglaj validat
The system SHALL provide a verification command that rejects changes to the weights file that add or remove keys or leave configured limits.

#### Scenario: Valoare în afara limitei
- **WHEN** `praguri.aplicat` e pus la 1,5
- **THEN** comanda eșuează și numește cheia și limitele

#### Scenario: Reglaj valid
- **WHEN** `scor.scadere_per_30_zile` e schimbat în limite
- **THEN** comanda trece, arată diferența de calibrare și tipărește linia pentru `board/`

### Requirement: Diferența de calibrare vizibilă
The system SHALL show, for every tuning, which base events change decision or score against the golden reference.

#### Scenario: Prag mutat
- **WHEN** `praguri.predictie` crește
- **THEN** tabelul listează evenimentele care trec din predicție în neaplicat

### Requirement: Cerere de logică
The system SHALL accept non-value logic changes only through a written request with example input and expected output, addressed to the engine owner.

#### Scenario: Regulă nouă
- **WHEN** cineva vrea o regulă nouă
- **THEN** scrie cererea în `board/` cu `@Victor`, nu modifică motorul

### Requirement: Banc de test fără UI
The system SHALL provide a command that runs texts through the full pipeline and prints extraction method, coordinates, accuracy, level and reason.

#### Scenario: Zece texte
- **WHEN** se rulează bancul pe `data/golden/`
- **THEN** se tipărește câte o linie per text și un sumar cu diferențele față de așteptat

### Requirement: Înghețarea logicii
The system SHALL mark the verified logic with a tag and SHALL allow later logic changes only through tuning or an approved request.

#### Scenario: După tag
- **WHEN** `logic-v1` există
- **THEN** o schimbare de cod în motor cere cerere aprobată de Victor
