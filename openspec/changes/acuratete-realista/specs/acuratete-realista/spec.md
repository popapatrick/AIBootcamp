# Spec Delta

## ADDED Requirements

### Requirement: Rețea GIS stabilă
The system SHALL start KMZ elements at `acuratete.initial_gis` and decay them by `scadere_gis_per_30_zile` without going below `minim_gis` unless a report contradicts them.

#### Scenario: GIS neatins
- **WHEN** un stâlp din KMZ nu are niciun raport până la 15 nov.
- **THEN** scorul lui e ≥ 0,92 și banda e verde

### Requirement: Plafon după sursa locației
The system SHALL cap the score of any element created or moved from a report at `plafon_locatie[sursa_locatie]`, and raise the cap when a later report brings a better location source.

#### Scenario: Adresă, apoi GPS
- **WHEN** un stâlp nou executat e raportat doar cu adresă, apoi confirmat cu coordonate GPS
- **THEN** întâi e aplicat galben (≤ 0,70), apoi poate trece în verde (≤ 0,85)

### Requirement: Raport executat aplicat
The system SHALL apply elements from executed field reports (mentenanță/investiții, status executat) from `acuratete.aplicat_raport_executat`, while requests and non-executed reports stay predictions below `praguri.aplicat`.

#### Scenario: Cerere vs lucrare
- **WHEN** aceeași locație vine o dată ca cerere și o dată ca lucrare finalizată
- **THEN** cererea e predicție punctată, lucrarea e element aplicat cu linie plină

### Requirement: Bandă de culoare
The system SHALL write `banda` (verde/galben/portocaliu/rosu) from `weights.culori` on every element state and journal entry.

#### Scenario: Scor 0,55
- **WHEN** un element are scorul 0,55
- **THEN** banda e portocaliu

### Requirement: Verificat de om
The system SHALL set any element to `verificat_om.scor` with `verificat_om: true` on a `verificare_om` event, and clear the flag when a later report contradicts it.

#### Scenario: Verificare și contradicție
- **WHEN** un stâlp galben e verificat de om, apoi un raport ulterior îl contrazice
- **THEN** întâi e 1,0 verde cu insignă, apoi pierde insigna și scorul se recalculează
