# Rapoarte fictive (sesiunea 4, scenariul timeline)

Toate fișierele sunt **DATE FICTIVE**: prima linie a fiecărui .txt este `DATE FICTIVE`. Rețeaua e fictivă (PTAB 7812, din KMZ-ul demo).

## Fișierele
- `AAAA-LL-ZZ_<sursa>_NN.txt`, de ex. `2026-08-03_mentenanta_01.txt`. `sursa` ∈ `mentenanta`, `investitii`, `racordari`, `apel_client`. `NN` = numărul din sursă, în ordine cronologică.
- **Scenariul timeline: 55 de rapoarte, 1 aug. → 14 nov. 2026** (rețeta din `docs/plan-sesiune-4-prezentare.md`, 7.1). Pe fel:

| Fel | Sursă | Nr. | `tip_asteptat` |
|---|---|---|---|
| Verificare de rutină cu ID | mentenanta | 10 | `verificare` |
| Stâlp înlocuit sau nod lipsă, cu adresă sau indiciu | mentenanta | 6 | `nod_lipsa` (4), `activ_inlocuit` (2) |
| Defect (avarie) | mentenanta | 5 | `avarie_semnalata` |
| Mutare fire (sens giratoriu, încă unul) | mentenanta | 2 | `mutare_fire` |
| Verificat de om | mentenanta | 4 | `verificare_om` |
| Investiții, linie nouă executată | investitii | 4 | `nod_lipsa` |
| Investiții, linie planificată | investitii | 3 | `linie_planificata` |
| Investiții, demontare | investitii | 4 | `activ_demontat` |
| Racordări, cereri (adresă, stradă, departe) | racordari | 8 | `cerere_racordare` |
| Racordări, executate | racordari | 4 | `racord_nou` |
| Apeluri clienți (rafală de 3 pe Strada Liviu Rebreanu, 2 Oct.) | apel_client | 5 | — |

- Cel puțin o treime (21 din 55) sunt doar **stradă + indiciu** („lângă nr. 9”, „între nr. 10 și 20”, „capătul străzii”, „vizavi de nr. 8”, „colț cu Strada X”), fără coordonate și fără ID. Restul: coordonate GPS în zona rețelei (sub 3 km de centroid), adresă cu număr, sau ID de element existent în rețea.
- Textele trec prin standardizare (cache `ai_cache` → Haiku `ai_cli`); `fill_cache --lipsa` le listează. Textele care lipsesc din cache cad pe regex, marcat „Regex (simplificat)”: de aceea cache-ul se pregătește înainte de demo.

## Regula străzilor
Doar cele 24 de străzi din `backend.engine.osm.strazi()` (cache-ul OSM local). Un nume în afara listei iese „necunoscut” la geocodare, deci nu se folosește nicio altă stradă. Lista:
Aleea Bălții · Intrarea Energiei · Intrarea Plopilor · Strada 1 Mai · Strada București · Strada Bălții · Strada Carpati · Strada Crinului · Strada Fagului · Strada Ion Luca Caragiale · Strada Liliacului · Strada Liviu Rebreanu · Strada Oituz · Strada Orhideelor · Strada Orizont · Strada Primăverii · Strada Regina Maria · Strada Soarelui · Strada Speranței · Strada Teiului · Strada Tineretului · Strada Ulmului · Strada Viilor · Șoseaua Principală.

Verificare: script în afara repo (scratchpad) care verifică numele de străzi, ID-urile (`network.geojson`), coordonatele (≤ 3 km de centroid), datele din nume și că fiecare fișier e în `index.json`.

## index.json
Ground truth pentru fiecare raport: `fisier`, `sursa`, `data`, `scenariu` (`null` pentru scenariul timeline, care nu e un test), `element_id_asteptat` (ID-ul din text sau `null`), `tip_asteptat`. `null` = nu se poate stabili din text. Pentru `apel_client`, `tip_asteptat` e `null`.

## exemple-dummy.json
Texte pentru butoanele echipelor. Obiect cu cheile `mentenanta`, `investitii`, `racordari` (5 texte fiecare, `GET /exemple?sursa=`), plus `apel_client` și `om_teren` (neschimbate). Item: `{id, titlu, text, data, asteptat: {tip, element_id|null, nota}}`. Nivelul de standardizare variază: coordonate, adresă cu număr, doar stradă + indiciu, intersecție, reper (PTAB 7812). `nota` descrie efectul așteptat pe hartă, nu e ground truth. Textele au greșeli de scriere intenționate (text messy).

## demo-intro.json
4 carduri pentru pagina de intro (`GET /demo/exemple`): `{id, titlu, descriere, sursa, text, data_moment, focus}`. Primul e „Stâlp căzut lângă nr. 15” pe Strada Viilor, fără coordonate. `focus: null`: îl calculează API-ul din `schimbari`.

## Alte fișiere
- `geo-test.json` și `genereaza_geo_test.py`: calibrarea geocodării (A/B), nu fac parte din scenariu.
- `trasee-dummy.json`: trasee GPS dummy (etapa 16).
