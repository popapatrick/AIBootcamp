# Spec Delta

## ADDED Requirements

### Requirement: Căutare pe stradă din indicii parțiale
The system SHALL turn a street plus a partial hint into a search window on that street and look for elements of the requested type in it, instead of requiring exact coordinates.

#### Scenario: Un candidat
- **WHEN** „stâlp căzut pe Strada Viilor nr. 12” fără coordonate și un singur stâlp în fereastră
- **THEN** raportul se potrivește cu acel stâlp, scor ≤ plafonul adresei, nu `neaplicat`

#### Scenario: Mai mulți candidați
- **WHEN** în fereastră sunt 3 stâlpi
- **THEN** iese predicție pe cel mai apropiat, cu celelalte 2 ca alternative

#### Scenario: Ancoră
- **WHEN** pe aceeași stradă există o adresă cunoscută dintr-un raport anterior
- **THEN** precizia ferestrei e ±40 m, nu ±100 m

### Requirement: Predicție pe străzi
The system SHALL predict connections (racordare, distant missing node, rerouted wires) along the local OSM street graph, reusing existing poles on the way, and mark a straight line only when no street path exists.

#### Scenario: Casă departe
- **WHEN** o casă e la ~300 m de rețea
- **THEN** lanțul prezis urmează străzile, iar scorul scade cu lungimea drumului

#### Scenario: Fără drum
- **WHEN** punctul nu e legat de rețea prin străzi
- **THEN** linie dreaptă cu scor `fara_drum`, de verificat

### Requirement: Fire mutate din document
The system SHALL locate a `mutare_fire` described only in text from the named intersection and propose a new route that avoids the zone, preferring the street named in the text.

#### Scenario: Sens giratoriu
- **WHEN** textul spune că firele de la intersecția Șoseaua Principală cu Strada Liviu Rebreanu au fost mutate pe Strada Crinului
- **THEN** tronsoanele din zonă devin de verificat, iar traseul nou ocolește centrul pe străzi

### Requirement: Neaplicat doar fără loc
The system SHALL return `neaplicat` only when the text has no location hint at all or the point is outside the prototype zone.

#### Scenario: Doar stradă
- **WHEN** textul are doar numele străzii
- **THEN** rezultatul e predicție sau „de verificat” pe stradă, nu `neaplicat`
