# Proposal

## Why

Pentru demo trebuie să putem crea noi rapoarte dummy direct din interfață, nu doar să redăm un set fix. Un jurat trebuie să vadă ce se întâmplă în spate: textul messy devine eveniment standardizat, se leagă de un stâlp existent, iar dacă stâlpul nu există, sistemul simulează cum ar putea arăta rețeaua pe străzile din jur.

## What Changes

- Ecran principal cu 4 butoane de sursă: Racordări, Investiții, Mentenanță și Apel telefonic de la client (text scris de operatorul de call center).
- Fiecare buton deschide un câmp de text liber (poate fi messy) și un buton „Generează exemplu" cu texte dummy realiste pentru sursa aleasă.
- După trimitere, rețeaua se schimbă în spate, iar harta arată rețeaua nouă.
- Buton „Show pipeline": pașii parcurși (extragere, standardizare, potrivire pe stâlp, scor, decizie) și lista schimbărilor din rețea.
- Dacă stâlpul nu există, harta arată punctat un traseu propus pe străzile din jur (OSM).
- Pe interfață apare data ultimei actualizări a rețelei.

## Capabilities

### New Capabilities
- `raportare-interactiva`: introducerea de rapoarte dummy din 4 surse, cu generare de exemple.
- `pipeline-vizibil`: explicația pașilor și diferența dintre rețeaua dinainte și de după.

### Modified Capabilities

## Impact

- `backend/api` (C): câmp `ultima_actualizare`, diff-ul în răspunsul `/rapoarte`.
- `backend/engine` (B): `apply_event` întoarce lista schimbărilor structurată; `statistici` are data ultimei actualizări.
- `backend/extract` și `data/reports` (A): promptul tratează textul de call center; exemple dummy pe sursă.
- Frontend Lovable (C).
- Contracte atinse: răspunsul `POST /rapoarte` (câmp `schimbari`), `statistici` (câmp `ultima_actualizare`); commit `contract:`.
