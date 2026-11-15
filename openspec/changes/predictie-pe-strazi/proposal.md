# Proposal

## Why

Modelul se blochează când nu știe poziția exactă: numărul de casă e pus orbește la N/100 din stradă (±200 m), o adresă mai vagă de 15 m nu se poate potrivi cu niciun element, iar legăturile prezise merg în linie dreaptă prin case. 8 din 29 de evenimente ies `neaplicat`.

## What Changes

- Căutare pe stradă din indicii parțiale („la nr. 12”, „lângă nr. 15”, „între 10 și 20”, „vizavi”, „capătul străzii”, „colț cu”, „lângă stâlpul X”): fereastră pe stradă (ancore sau convenția de numerotare), apoi elementele din fereastră.
- Analiza hărții: legăturile prezise merg pe graful de străzi OSM local, cu stâlpi la ~40 m și alternative explicate.
- Fire mutate descrise doar în text (sens giratoriu): zona din intersecție, traseul nou ocolește pe străzi.
- `neaplicat` doar fără niciun indiciu de loc sau în afara zonei.

## Capabilities

### New Capabilities
- `predictie-pe-strazi`

### Modified Capabilities

## Impact

- B: `backend/geo` (preluat de la A), promptul din `backend/extract/extract.py`, `backend/engine/analiza_harta.py` (nou), `match.py`, `sesiune2.py`, `model.py`.
- C: pașii `cautare_strada`, `analiza_harta` în API și UI; golden.
- Extinde `racordare-fara-neaplicat`, `mutare-fire-sens-giratoriu`, `geocodare-adresa-acuratete`.
