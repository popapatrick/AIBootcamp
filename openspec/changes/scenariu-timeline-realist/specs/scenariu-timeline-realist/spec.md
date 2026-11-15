# Spec Delta

## ADDED Requirements

### Requirement: Evenimente din texte
The system SHALL build the timeline from report texts standardized by AI, each entry keeping its original text and extracted fields.

#### Scenario: Intrare în timeline
- **WHEN** UI-ul cere `GET /evenimente`
- **THEN** fiecare intrare are `text_original` și `standardizare`

### Requirement: Distribuție realistă
The calibration check SHALL fail when the color distribution at the present date leaves the target ranges.

#### Scenario: Țintă
- **WHEN** se rulează `verifica_reglaje` pe scenariul nou
- **THEN** verde 70–82 %, galben 8–15 %, portocaliu 5–10 %, roșu 2–6 %
