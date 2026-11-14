# Spec Delta

## Purpose
Harta de demo afișează tipul elementelor ca în fișierul KMZ și, separat, starea lor de verificare.

## ADDED Requirements

### Requirement: Simbolistica KMZ pe hartă
The system SHALL display each node and each section with the visual class it has in the KMZ source: house nodes in green, important nodes (series 5 and 6, plecare JT origin nodes, transformer post) with their KMZ colours, and sections coloured by category (aerian, ramuri, subteran).

#### Scenario: Încărcarea inițială
- **WHEN** harta se încarcă fără niciun eveniment aplicat
- **THEN** nodurile serie 7 apar verzi, cele de serie 6 gri, nodurile de origine portocalii, postul de transformare distinct, iar cablurile în albastru, turcoaz și roșu după categorie

### Requirement: Clasa elementului vine din motor
The system SHALL expose a derived `clasa` property on every node and section in the state GeoJSON, computed from `serie` and `categorie`, so every client renders the same class.

#### Scenario: Element nou adăugat
- **WHEN** un nod nou este adăugat în model de un raport
- **THEN** primește o `clasa` (implicit `casa` dacă tipul e un racord, altfel `important`) și apare cu simbolul corespunzător

### Requirement: Starea de verificare ca strat separat
The system SHALL show the verification state as a halo or outline on top of the KMZ symbol: green when verified recently or applied, yellow when static (not touched by any event), dotted when it is an unapplied prediction, red when in conflict.

#### Scenario: Element confirmat de un raport
- **WHEN** un raport confirmă un element existent
- **THEN** simbolul KMZ rămâne neschimbat și halou-l devine verde

#### Scenario: Element neatins
- **WHEN** niciun eveniment nu a atins elementul până la data selectată
- **THEN** halou-l este galben

### Requirement: Legendă
The system SHALL show a legend explaining both layers (element type and verification state).

#### Scenario: Legenda vizibilă
- **WHEN** utilizatorul deschide harta
- **THEN** o legendă listează tipurile de noduri/cabluri și cele patru stări
