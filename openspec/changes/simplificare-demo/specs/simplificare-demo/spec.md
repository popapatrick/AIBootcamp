# Spec Delta

## ADDED Requirements

### Requirement: Fără scenariu extrem
The system SHALL NOT expose the extreme scenario in the API or UI.

#### Scenario: Cerere veche
- **WHEN** UI-ul cere `GET /retea?scenariu=extrem`
- **THEN** parametrul e ignorat sau respins; nu există comutator în UI

### Requirement: Fără traseu generat
The system SHALL NOT generate a simulated trace for a report when `demo.trace_generat_activ` is 0.

#### Scenario: Raport nou
- **WHEN** se trimite un raport fără ID
- **THEN** în pași nu apare `trace`

### Requirement: Fără coduri în UI
The UI SHALL show color band, line style and badges instead of internal codes (`in_model`, `predictie`, `generat_model`).

#### Scenario: Element din raport
- **WHEN** un element are `origine: generat_model`
- **THEN** UI-ul scrie „Din raport”, nu codul
