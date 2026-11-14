# Proposal

## Why

Timeline-ul actual arată mai ales schimbări mici de scor. Pentru demo trebuie evidențiate cazuri extreme: o ramură care se construiește pe etape, fire mutate, un segment scos din uz, un val de apeluri din aceeași zonă. Ce a fost verificat devine verde, iar ce n-a fost atins rămâne galben, ca să se vadă contrastul.

## What Changes

- Buton „Încarcă rețeaua cu evenimente" care pornește un scenariu cu Play și arată evoluția pe date.
- Set nou de evenimente și rapoarte dummy (A) cu 4 cazuri extreme, peste cele 29 existente.
- Motorul (B) tratează un tip nou de eveniment, `activ_demontat`, și un semnal agregat pentru un val de apeluri din aceeași zonă.
- Pe timeline: halou verde pentru elementele verificate până la data aleasă, galben pentru cele neatinse.

## Capabilities

### New Capabilities
- `timeline-demo-extrem`: scenariu de evenimente cu cazuri extreme, redat pe timeline cu Play și halou de stare.

### Modified Capabilities

## Impact

- `contracts/event.schema.json`: tip nou `activ_demontat`; commit `contract:`.
- `data/events/` și `data/reports/` (A): `events.extreme.json` și rapoartele aferente.
- `backend/engine` (B): regula pentru `activ_demontat` și pentru valul de apeluri; recalibrare.
- Frontend Lovable (C): butonul de încărcare și redarea.
- Depinde de `harta-aspect-kmz` (halou) și de `mutare-fire-sens-giratoriu` (cazul sens giratoriu).
