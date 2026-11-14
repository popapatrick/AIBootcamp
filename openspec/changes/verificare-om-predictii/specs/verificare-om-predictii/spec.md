# Spec Delta

## Purpose
Omul poate accepta sau respinge predicțiile AI-ului după verificarea în teren, iar rețeaua păstrează diferența dintre predicție și confirmare.

## ADDED Requirements

### Requirement: Butoane pe predicții
The system SHALL show "Acceptă (verificat în teren)" and "Respinge" actions on every unapplied prediction.

#### Scenario: Predicție selectată
- **WHEN** utilizatorul selectează o predicție pe hartă
- **THEN** panoul arată scorul, metoda și cele două butoane

### Requirement: Acceptarea aplică predicția
The system SHALL treat acceptance as an event from source `om_teren` scored by the same scoring calculation, apply the prediction as a real element, and mark it as confirmed by a human.

#### Scenario: Acceptare
- **WHEN** omul apasă „Acceptă" pe o predicție de nod lipsă
- **THEN** nodul devine element real, plin, cu halou verde și marcaj „confirmat de om", iar jurnalul spune cine, când și cu ce scor

### Requirement: Respingerea retrage predicția
The system SHALL withdraw a rejected prediction and lower confidence in the method that proposed it, without changing real elements.

#### Scenario: Respingere
- **WHEN** omul apasă „Respinge"
- **THEN** predicția dispare de pe hartă, jurnalul păstrează motivul, iar metoda propunătoare scade în încredere

### Requirement: Distincție AI versus om
The system SHALL keep predictions made only by the AI visually and in the journal distinct from elements confirmed by a human.

#### Scenario: Două elemente pe hartă
- **WHEN** harta conține o predicție neconfirmată și un element confirmat de om
- **THEN** primul e punctat, al doilea plin cu marcaj „om"

### Requirement: O singură decizie
The system MUST refuse a second decision on a prediction that was already accepted or rejected.

#### Scenario: A doua apăsare
- **WHEN** omul apasă din nou pe o predicție deja decisă
- **THEN** primește mesajul că predicția are deja o decizie
