# Spec Delta

## Purpose
Niciun punct nu iese din zona de 3 km a prototipului; un punct din afară e marcat eronat în cadrul prototipului.

## ADDED Requirements

### Requirement: Zonă de 3 km în jurul rețelei de start
The system SHALL define the prototype zone as a circle around the centroid of the start network with the radius from the weights configuration.

#### Scenario: Zonă calculată
- **WHEN** modelul se încarcă
- **THEN** centrul e centroidul rețelei de start și raza e `zona.raza_max_m`

### Requirement: Punct în afara zonei nu se aplică
The system SHALL NOT apply any event whose location lies outside the zone and SHALL mark it as erroneous within the prototype, with the distance and the limit in the log.

#### Scenario: Coordonate la 40 km
- **WHEN** un raport are coordonate la 40 km de centroid
- **THEN** evenimentul are `eronat_prototip: true`, nu intră în model și jurnalul spune distanța și limita

#### Scenario: Geocodare care ar ieși din zonă
- **WHEN** geocodarea unei adrese ar da un punct la 5 km
- **THEN** rezultatul e `in_afara_zonei`, fără coordonate folosite

### Requirement: Fără excepții pe sursă
The system SHALL apply the zone check to every source, including field-human decisions and customer calls.

#### Scenario: Om din teren
- **WHEN** o decizie `om_teren` e legată de un punct din afara zonei
- **THEN** se aplică aceeași regulă

### Requirement: Zonă în API
The system SHALL expose the zone center and radius and the `eronat_prototip` flag so the UI can display them.

#### Scenario: UI
- **WHEN** UI-ul cere starea
- **THEN** primește centrul, raza și evenimentele marcate eronate
