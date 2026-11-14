# Spec Delta

## Purpose
O cerere de racordare fără locație exactă poate folosi poziția simulată a operatorului ca indiciu, cu scor redus, marcată peste tot ca simulată.

## ADDED Requirements

### Requirement: Poziție simulată a operatorului
The system SHALL generate, on explicit request, a deterministic dummy operator position on the street named in the address, with a small GPS noise, marked `simulata: true` and with its precision in meters.

#### Scenario: Stradă cunoscută
- **WHEN** se cere `GET /locatie-operator-demo?adresa=Strada Liviu Rebreanu`
- **THEN** răspunsul are `lat`, `lon`, `precizie_m`, `simulata: true`, `strada` și `motiv`, iar o a doua cerere identică dă același punct

#### Scenario: Adresă necunoscută
- **WHEN** adresa nu conține niciun nume de stradă OSM cunoscut
- **THEN** răspunsul e o eroare clară („adresa nu se poate localiza, dă clic pe hartă") și nu se inventează niciun punct

### Requirement: Folosirea poziției în cererea de racordare
The system SHALL use `detalii.locatie_operator` for a `cerere_racordare` only when the text has no coordinates and no map click was given, and SHALL report the location source as `sursa_locatie` (`text`, `clic` or `operator_simulat`).

#### Scenario: Fără coordonate, cu operator
- **WHEN** cererea „casă pe Strada Liviu Rebreanu" nu are coordonate și vine cu `locatie_operator`
- **THEN** lanțul de racordare pornește spre acea poziție și pașii arată `sursa_locatie: operator_simulat`

#### Scenario: Clicul are prioritate
- **WHEN** cererea are și clic pe hartă, și `locatie_operator`
- **THEN** se folosește clicul și `sursa_locatie` e `clic`

### Requirement: Scor mai mic și rezultat neaplicat
The system SHALL score a prediction from the simulated operator position lower than the same prediction from exact coordinates, using the same scoring calculation and `contracts/weights.yaml`, and SHALL NOT apply it to the model without a human decision.

#### Scenario: Comparație cu clicul
- **WHEN** aceeași cerere se rulează o dată cu clic și o dată cu poziția operatorului
- **THEN** scorul cu operatorul e mai mic și nivelul e `predictie`

#### Scenario: Jurnal „de ce"
- **WHEN** predicția vine din poziția operatorului
- **THEN** jurnalul spune că locația e din poziția simulată a operatorului, cu precizia în metri
