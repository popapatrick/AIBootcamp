# Spec Delta

## Purpose
Din adresă sau stradă se deduc coordonate geografice aproximative în zona modelului, iar acuratețea reflectă cât de standardizat e textul.

## ADDED Requirements

### Requirement: Coordonate din adresă
The system SHALL derive approximate coordinates and a precision in meters from a structured address using only the local OSM street cache, with AI used only to choose among cached streets.

#### Scenario: Stradă cu număr
- **WHEN** raportul spune „Strada Liviu Rebreanu nr. 12"
- **THEN** se întorc coordonate pe acea stradă, `metoda` „osm_cache", precizie în metri și acuratețe din tabelul `geocodare`

#### Scenario: Ortografie diferită
- **WHEN** raportul spune „str liviu rebrianu" și nicio stradă nu se potrivește exact
- **THEN** AI alege strada cea mai probabilă dintre cele din cache, rezultatul are `metoda` „ai_estimare" și acuratețe înmulțită cu `factor_ai_fuzzy`

#### Scenario: Stradă necunoscută
- **WHEN** adresa nu corespunde niciunei străzi din cache
- **THEN** rezultatul e „necunoscut" cu motiv, fără coordonate inventate

### Requirement: Acuratețe după nivelul de standardizare
The system SHALL assign location accuracy from a configured table ordered ID, explicit coordinates, street with number, intersection, street only, landmark only, and SHALL cap extraction confidence by the best locator present in the text.

#### Scenario: Text apropiat de standard
- **WHEN** textul conține ID existent sau coordonate explicite
- **THEN** acuratețea e cea mai mare din tabel și nu se apelează geocodarea

#### Scenario: Text vag
- **WHEN** textul conține doar un reper („lângă școală")
- **THEN** acuratețea e cea mai mică din tabel și propunerea rămâne predicție, nu se aplică

### Requirement: Fără potrivire „doar adresă"
The system SHALL NOT end matching at "address only" when geocoding yields a location; it SHALL continue as a coordinate match with the geocoding accuracy as match quality.

#### Scenario: Adresă geocodată
- **WHEN** raportul are doar adresă și geocodarea reușește
- **THEN** pasul de potrivire arată „coordonate din adresă", precizia și motivul în „De ce?"

### Requirement: Fără chei și fără rețea externă
The system SHALL NOT call external geocoding services nor use an API key for geocoding.

#### Scenario: Offline
- **WHEN** nu există internet
- **THEN** geocodarea funcționează din cache-ul OSM local și din cache-ul AI
