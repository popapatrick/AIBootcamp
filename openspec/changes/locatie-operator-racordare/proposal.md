# Proposal

## Why

O cerere de racordare vine uneori fără locație exactă: textul are doar o adresă vagă (strada), iar pe hartă nu s-a făcut clic. Operatorul e însă la casă, cu tableta. Sistemul trebuie să poată folosi poziția lui ca indiciu pentru lanțul de stâlpi, fără să pretindă că o cunoaște exact. În prototip nu avem GPS real, deci poziția e simulată și marcată ca atare peste tot.

## What Changes

- Buton explicit „Folosește locația operatorului (simulată)" pe cererea de racordare fără coordonate.
- Endpoint nou `GET /locatie-operator-demo?adresa=&lat=&lon=`: generează determinist o poziție GPS dummy pe strada din adresă (nume OSM cunoscut), cu zgomot GPS mic. Adresă nelocalizabilă: eroare clară, fără punct inventat.
- `POST /rapoarte` acceptă `locatie_operator {lat, lon, precizie_m, simulata}`; motorul îl folosește pentru `cerere_racordare` doar dacă nu există coordonate în text și nici clic.
- Scorul predicției e mai mic decât la coordonate exacte (factor nou în `weights.yaml`), rezultatul rămâne mereu predicție (neaplicat) până confirmă omul.
- StepTrace arată `sursa_locatie: text | clic | operator_simulat`; jurnalul „de ce" spune că poziția e simulată, cu precizia.

## Capabilities

### New Capabilities
- `locatie-operator-racordare`: poziție simulată a operatorului ca indiciu de locație pentru cererea de racordare, cu scor redus și marcaj „simulată".

### Modified Capabilities
- `cerere-racordare-predictie`: sursa locației (`sursa_locatie`) și al treilea fel de locație.

## Impact

- `contracts/` (aditiv): `GET /locatie-operator-demo`, câmpul `locatie_operator`, `sursa_locatie`, `racordare.factor_locatie_operator`. Commit `contract:`.
- `backend/racordare` (A): funcția pură `locatie_operator_demo`. `backend/engine/sesiune2.py` (B): folosirea poziției și factorul de scor. `backend/api` (C): endpoint și câmp.
- Toate sarcinile le face C la cererea omului (excepție de la împărțirea pe foldere).
- Lovable (C): buton și marcaj „simulată" (prompt separat, nu în acest commit).
