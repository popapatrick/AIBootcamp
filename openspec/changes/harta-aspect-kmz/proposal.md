# Proposal

## Why

Harta din UI arată acum nodurile ca puncte colorate doar după scorul de încredere. Fișierul KMZ (format GIS) are simbolistică proprie: noduri de casă (serie 7, verde), noduri mai importante (serie 6 gri, serie 5, origine plecare JT portocaliu, post de transformare) și cabluri colorate pe categorie (aerian albastru, ramuri turcoaz, subteran roșu). Harta de demo trebuie să semene cu ce vede un om în GIS, iar starea de verificare (verde = verificat acum, galben = static, punctat = predicție) să apară peste, fără să piardă tipul elementului.

## What Changes

- Motorul (B) adaugă în GeoJSON-ul de stare proprietăți derivate: `clasa` pentru noduri (casa, important, origine, post) și `clasa` pentru tronsoane (aerian, ramura, subteran).
- UI-ul (C, Lovable) desenează simbolurile ca în KMZ și o stare de verificare ca halou/contur peste simbol.
- Legendă pe hartă cu cele două straturi vizuale: tipul elementului (KMZ) și starea (halou).
- Presupunere de confirmat cu omul: serie 7 = „casă", restul = „important". KMZ-ul nu spune explicit „casă"; se citește doar simbolul.

## Capabilities

### New Capabilities
- `aspect-harta-kmz`: harta afișează tipul elementelor ca în KMZ și starea de verificare ca halou separat.

### Modified Capabilities

## Impact

- `contracts/state.schema.json`: proprietăți noi aditive (`clasa`); commit `contract:`.
- `backend/engine/network.py` / `model.py` (B): derivare `clasa` din `serie` și `categorie`.
- Frontend Lovable (C): simboluri, halou, legendă.
- Nu se schimbă scorurile sau ponderile.
