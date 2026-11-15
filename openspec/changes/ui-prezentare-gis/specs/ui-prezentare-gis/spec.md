# Spec Delta

## ADDED Requirements

### Requirement: Pagină de intro
The UI SHALL open on an intro page with example cards that open the map at the example's moment and location.

#### Scenario: Exemplu
- **WHEN** omul apasă „Vezi pe hartă” pe cardul căutării pe stradă
- **THEN** harta trece la data exemplului, zboară la `focus` și arată pop-up-ul și standardizarea

### Requirement: Raport de echipă dinamic
The UI SHALL show, after a team report, the AI standardization, fly to `focus`, highlight touched elements with popups and move the timeline to the present.

#### Scenario: Mentenanță
- **WHEN** omul trimite un text de mentenanță
- **THEN** apar câmpurile extrase, harta zboară la zonă și apar maxim 3 pop-up-uri

### Requirement: Timeline orizontal
The UI SHALL show a horizontally scrollable timeline that starts at the present and returns there after every new report.

#### Scenario: Raport nou
- **WHEN** se trimite un raport
- **THEN** timeline-ul sare la capătul din dreapta și evidențiază punctul nou

### Requirement: Accesibilitate
The UI SHALL meet WCAG 2.1 AA: color is never the only signal, full keyboard navigation, visible focus, reduced motion honored.

#### Scenario: Fără animații
- **WHEN** browserul are `prefers-reduced-motion`
- **THEN** harta schimbă vederea fără zbor și fără pulsare
