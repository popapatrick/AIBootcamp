# Spec Delta

## Purpose
O cerere de racordare fără locație exactă poate folosi poziția simulată a operatorului ca indiciu, cu scor redus, marcată peste tot ca simulată.

## ADDED Requirements

### Requirement: Poziție simulată a operatorului
The system SHALL generate, on explicit request, a deterministic dummy operator position from the text written by the operator, inside the zone it describes (street, street corner, neighborhood or a combination), with a small GPS noise, marked `simulata: true`, with a precision in meters that reflects how vague the zone is, and with the hints it used (`indicii`) and the applied constraint (`zona`).

#### Scenario: Stradă singură
- **WHEN** se cere `GET /locatie-operator-demo?text=casă pe Strada Liviu Rebreanu`
- **THEN** răspunsul are `lat`, `lon`, `precizie_m`, `simulata: true`, `strada`, `motiv`, `indicii` cu strada `gasit: true` și `zona`, punctul e pe acea stradă, iar o a doua cerere identică dă același punct

#### Scenario: Intersecție
- **WHEN** textul e „strada Liviu Rebreanu colț cu strada Ion Luca Caragiale"
- **THEN** punctul e lângă intersecția celor două străzi, `indicii` conține o `intersectie` cu `gasit: true`, iar `precizie_m` e mai mică decât la o stradă singură

#### Scenario: Cartier
- **WHEN** textul e „cartierul 1 Decembrie" (zonă OSM `is_in` existentă)
- **THEN** punctul e doar în acea zonă, `strada` e null și `precizie_m` e cea mai mare

#### Scenario: Combinație
- **WHEN** textul e „Strada Viilor din cartierul 1 Decembrie"
- **THEN** punctul respectă ambele constrângeri; dacă se contrazic, răspunsul e eroare, nu un punct

#### Scenario: Indiciu negăsit
- **WHEN** textul pomenește o stradă, un cartier sau un reper care nu există în datele locale, alături de un indiciu găsit
- **THEN** indiciul negăsit apare cu `gasit: false` în `indicii` și în `motiv`, nu e ignorat în tăcere

#### Scenario: Niciun indiciu găsit
- **WHEN** niciun indiciu din text nu se găsește în datele locale
- **THEN** răspunsul e o eroare 422 clară („dă clic pe hartă") cu indiciile căutate, și nu se inventează niciun punct

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
