# Spec Delta

## Purpose
Utilizatorul poate crea rapoarte dummy din patru surse diferite și le trimite în sistem din interfață.

## ADDED Requirements

### Requirement: Patru surse de raport
The system SHALL offer four report sources on the main screen: Racordări, Investiții, Mentenanță and Apel telefonic de la client, the latter being text written by a call-center operator.

#### Scenario: Alegerea sursei
- **WHEN** utilizatorul apasă pe una dintre cele patru surse
- **THEN** apare un câmp de text pentru acea sursă, iar raportul trimis poartă echipa sursă și ponderea de încredere a sursei

### Requirement: Text liber messy acceptat
The system SHALL accept free text with typos, mixed formats and missing fields and standardise it into an event, marking missing fields as missing instead of inventing them.

#### Scenario: Text cu informații lipsă
- **WHEN** textul nu conține data sau ID-ul elementului
- **THEN** evenimentul standardizat listează câmpurile lipsă și rămâne procesabil

### Requirement: Generare de exemple dummy
The system SHALL provide a "Generează exemplu" action per source that fills the text field with a realistic dummy report from a prepared list.

#### Scenario: Exemplu generat
- **WHEN** utilizatorul apasă „Generează exemplu" la Mentenanță
- **THEN** câmpul se completează cu un text dummy de mentenanță, editabil înainte de trimitere

### Requirement: Rețeaua se schimbă după trimitere
The system SHALL apply the resulting event to the model according to the entry rule (nothing existing -> add, existing and sure -> apply, existing and unsure -> visibly different unapplied prediction with score) and refresh the map.

#### Scenario: Stâlp inexistent
- **WHEN** raportul se referă la un stâlp care nu există în model
- **THEN** harta arată punctat noul stâlp și un traseu propus pe străzile din jur, cu scor, neaplicat dacă scorul e sub prag
