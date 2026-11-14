# Spec Delta

## Purpose
Lista derulabilă de modificări ale rețelei, sincronizată cu harta, în locul butonului Play.

## ADDED Requirements

### Requirement: Listă cronologică de evenimente
The UI SHALL show all timeline events in chronological order in a vertical side panel, each with date, label, decision and the score change of the touched elements.

#### Scenario: Scenariul extrem
- **WHEN** se deschide timeline-ul pe scenariul extrem
- **THEN** panoul listează toate evenimentele, fiecare cu data, eticheta, decizia și scorul înainte -> după

### Requirement: Derularea mută harta
The UI SHALL update the map to the network state at the date of the event centered in the panel while the user scrolls, and SHALL highlight the elements touched by that event.

#### Scenario: Scroll
- **WHEN** utilizatorul derulează lista
- **THEN** harta trece la starea de la data evenimentului din centru, iar elementele atinse sunt evidențiate

### Requirement: „De ce?” la clic
The UI SHALL open the pipeline steps and reasons of an event when its entry is clicked, using the data already in the timeline entry.

#### Scenario: Clic pe un eveniment
- **WHEN** utilizatorul dă clic pe o intrare
- **THEN** apar pașii (extracție, geocodare, trace, potrivire, predicție, scor) și motivele, fără alt apel către server

### Requirement: Motorul dă schimbările și pașii
The engine SHALL include `schimbari`, `pasi` and `eronat_prototip` in every timeline entry.

#### Scenario: Eveniment eronat în prototip
- **WHEN** un eveniment cade în afara zonei prototipului
- **THEN** intrarea are `eronat_prototip: true` și decizia neaplicat, vizibile în listă
