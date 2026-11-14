# Proposal

## Why

Echipele firmei de electricitate au tablete cu locația din ultima oră. Când se creează un raport, traseul e un semnal complementar adresei. În prototip nu avem GPS real, deci traseul trebuie generat automat lângă punctul din raport, cu parametri care pot crește sau scădea acuratețea.

## What Changes

- La crearea oricărui raport cu o locație (coordonate, adresă geocodată, clic pe hartă), sistemul generează un traseu simulat de o oră lângă punct. Generatorul e determinist (seed) și nu inventează în raport; traseul e etichetat „simulat".
- Parametri: număr de puncte, zgomot GPS (m), durata opririi (min), acoperire (% puncte păstrate), poziția opririi față de punctul din raport (la punct sau decalată).
- Traseul modifică acuratețea locației: oprire lungă, zgomot mic, acoperire bună și oprire consistentă cu adresa cresc acuratețea (cu plafon de bonus); zgomot mare, acoperire slabă sau contradicție cu adresa o scad. Fără traseu, nimic nu se strică: traseul e complementar.
- Parametrii implicit vin din `weights.yaml`; pot fi suprascriși per raport (`trace_params`) din API/UI.

## Capabilities

### New Capabilities
- `traseu-generat`: generarea traseului simulat al tabletei lângă punctul din raport și efectul lui asupra acurateței.

### Modified Capabilities

## Impact

- A: `backend/trace/genereaza.py` (nou, în folderul lui A), `smoke_trace.py`.
- B: integrarea în potrivire/scor: `trace_generat` în `weights.yaml`, factor de acuratețe, jurnal.
- C: `trace_params` în `POST /rapoarte`; panou de parametri în UI (după înghețarea logicii).
- Contract (`contract:`, B): `detalii.trace_params`, `detalii.trace_sursa` („simulat" | „real"), secțiunea `trace_generat`.
- În afara scopului: GPS real, confidențialitate, calibrare pe date reale.
