# Etapa 2: date dummy (A)

Date FICTIVE (PTAB 7812).

## Ce face
`data/reports/` conține 29 de rapoarte fictive (.txt): ~12 fișe cu câmpuri, restul text liber și transcrieri de apeluri. Acoperă scenariile 1–7; scenariul 8 este rutină. `2026-10-23_mentenanta_11.txt` închide scenariul 1 (nod 6925190 confirmat pe teren, lipsă din GIS, cu coordonate). Fiecare fișier începe cu `DATE FICTIVE`.

## Distribuție pe sursă
| sursa | nr. |
|---|---|
| mentenanta | 11 |
| racordari | 7 |
| apel_client | 6 |
| investitii | 5 |

## Nume fișiere
`YYYY-MM-DD_<sursa>_<nn>.txt`, ex. `2026-08-04_mentenanta_01.txt`. Extracția (etapa 3) citește sursa și data din nume.

## Ground truth
`data/reports/index.json`: pentru fiecare fișier, `sursa`, `data`, `scenariu`, `element_id_asteptat`, `tip_asteptat`. `null` = nu se poate stabili din text.
- Tronson fără prefix (ex. `T-054`): ambiguu, așteptat `null` (nu `A-T-054`).
- `T-002` → `A-T-002`.

## Evenimente stub pentru B
`data/events/events.stub.json`: 5 evenimente, `EV-S01`..`EV-S05`, acoperă `nod_lipsa`, `activ_inlocuit`, `racord_nou`, `avarie_semnalata`, `linie_planificata`. Valori greșite voit: `EV-S03` are lat/lon inversate (`de_verificat`). Respectă `contracts/event.schema.json` (verificat pe câmpuri și enum-uri; validatorul nu a fost rulat).

## Limite cunoscute
- Rapoartele sunt scrise de mână, nu de sistem reale: niciun nume real, nicio adresă reală.
- Numărul de fișe (~12) nu e verificat într-un script.
- `events.stub.json` e scris manual, nu extras din rapoarte.

## Ce trebuie să știe ceilalți
- B: folosește `events.stub.json` la etapa 4; ID-urile de tronson din rapoarte sunt cele din `data/model/network.geojson`.
- A (etapa 3): rezultatul extracției trebuie comparat cu `index.json` pentru cel puțin 3 rapoarte.
