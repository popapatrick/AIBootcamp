# Proposal

## Why

Stâlpii de curent nu au adresă exactă, iar harta trebuie să arate poziția exactă a stâlpului. Când operatorul raportează pe tabletă lucrarea finalizată, adresa introdusă poate fi inexactă sau incompletă. Telefonul/tableta știe unde a stat operatorul în ultima oră: locul în care a stat cel mai mult e cel mai probabil locul stâlpului.

## What Changes

- La un raport de lucrare finalizată de pe tabletă se preia traseul (trace) din ultima oră și se corelează cu adresa introdusă.
- Adresa dă strada (potrivire cu numele străzilor din OSM); traseul dă locul exact: oprirea cea mai lungă pe strada respectivă.
- Dacă oprirea e lângă un stâlp existent, acela e confirmat; dacă e într-un loc fără stâlp, se prezice un stâlp nou (punctat, cu scor).
- Opririle scurte lângă stâlpi existenți pot fi folosite ca verificări suplimentare ale lor.
- Fallback: se folosește doar când adresa nu ajunge pentru potrivire.
- Pentru demo, traseul GPS e simulat (buton „Generează traseu ultima oră", editabil cu clic pe hartă) plus trasee gata făcute într-un fișier.

## Capabilities

### New Capabilities
- `locatie-din-trace`: poziția exactă a stâlpului dedusă din traseul tabletei din ultima oră și adresa introdusă.

### Modified Capabilities

## Impact

- `contracts/event.schema.json`: `detalii.trace` (listă de puncte cu timp) și `detalii.trace_rezumat`; commit `contract:`.
- `backend/engine` (B): `trace.py` (opriri, potrivire cu strada, alegerea locului), integrat în potrivire.
- `data/reports` (A): trasee dummy; `backend/api` și Lovable (C): trace în raport, generare și editare pe hartă.
- Folosește `osm.py` pentru străzi și regula nod nou (2,5 m).
