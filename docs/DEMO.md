# Demo (repetat de B pe UI-ul plan B, cu motorul real și `events.json` al lui A)

Date FICTIVE: rețea demonstrativă PTAB 7812. Spune asta la început.

## Pornire
```bash
.venv/bin/uvicorn backend.api.main:app --port 8000      # apoi deschide http://localhost:8000/ui/
```
`/health` trebuie să arate `retea=motor, evenimente=motor, motor=real`. `extractie=stub` pe laptopurile fără cheia OpenRouter (A are `claude`). Reporniți serverul înainte de demo: rapoartele live rămân în memorie până la repornire.

## Scenariul de 60 de secunde (Play durează ~29 s)
| Timp | Pe ecran | Ce spui |
|---|---|---|
| 0–5 s | Harta pe date 4 aug., rețeaua galben-verzuie | „530 de elemente, toate la încredere 0,6: nimeni nu le-a verificat recent. Culoarea e încrederea." |
| 5–10 s | Apasă Play. Apare un punct violet (4 și 18 aug.) | „Două rapoarte spun că lipsește un nod în curba străzii. Nu avem coordonate, deci îl propunem punctat, cu scor 0,74, apoi 0,81. Nu intră în model." |
| 10–16 s | 5–20 aug.: elemente devin mai verzi | „Verificările din teren cresc încrederea." |
| 16–20 s | 29 aug.: un element roșu | „Două echipe spun lucruri diferite despre aceeași secțiune: conflict. Nu aplicăm nimic, îl marcăm «de verificat»." (necesită `detalii.sectiune_noua` la EV-010, vezi board) |
| 20–23 s | 10 sept.: aplicat | „Investiții a înlocuit cablul. Formular cu scor 0,90: se aplică." |
| 23–29 s | 23 oct.: punctul violet devine solid | „Un raport cu coordonate confirmă nodul: predicția intră în model, cu legăturile către vecini. Apelurile din octombrie scad puțin încrederea; ce nu e verificat se estompează." |
| 29–45 s | Pauză. **Proces raport**, lipește primul text (vag) de mai jos | „Un raport nou, scris liber, trece prin pași vizibili." |
| 45–60 s | Rezultat: punct violet nou; lipește al doilea raport; „Vezi pe hartă" | „Un raport vag, doar cu coordonate = predicție (~0,65, sub pragul 0,75). Al doilea, de la altă echipă, cu ID și vecini, o promovează în model." |

Texte de lipit (primul: sursa mentenanță, data 2026-10-29; al doilea: sursa racordări, data 2026-10-31):
> (1, mentenanță) Lipsește din GIS un stâlp nou la coordonatele 44.281738, 26.064996, pe strada din colț.
> (2, racordări) Nod lipsă din GIS: stâlpul nou 7011223 la coordonatele 44.281738, 26.064996, între nodurile 7322194 și 7456900. Lucrare executată.

Rezultat verificat (simulat cu extracția Claude, încredere 0,75–0,9, text liber): primul = `predictie` 0,60–0,65 (fără ID și fără vecini în text, poziția e cunoscută, vecinii sunt deduși); al doilea = `adaugat` 0,90–0,95, nodul `7011223` și legăturile în model, predicția veche retrasă. Punctul 44.281738, 26.064996 e la ~34 m de orice element (nod nou real, nu o potrivire cu un vecin). Cu extracția stub (încredere 0,45–0,6) primul iese tot predicție.

## Verificat la repetiție (14 nov.)
- Play de la 4 aug. la 27 oct. durează ~29 s; slider-ul și lista de evenimente se actualizează; consola fără erori.
- Culoarea e continuă (0,3 roșu → 0,8 verde), deci scăderea în timp și confirmările se văd.
- Un raport live apare pe hartă și în timeline cu data corectă.

## Riscuri la demo
- **Harta de bază cere internet** (plăci OpenStreetMap). La repetiție, într-un moment plăcile nu s-au încărcat și fundalul a fost gri; liniile rămân vizibile. Plan B: înregistrare video a unei rulări reușite.
- **Standardizare AI fără cheie (`ai_cli`):** pe laptopul demo rulează o dată `claude auth login` (abonament). Apoi orice text nou e standardizat de Haiku (câteva secunde) și intră în cache. Verifică `/health` -> `extractie_cod: ai_cli`. Fără login, regex e ultima rezervă și UI-ul o arată.
- **Cheie demo:** Victor alocă o cheie doar în ziua demo-ului; până atunci, nicio cheie. Cu cheia (`EXTRACT_ALLOW_API=1`) un text nou iese `ai_api`; fără ea, din cache `ai_cache` sau `regex`. UI-ul arată oricare dintre ele.
- **Fără cheie API (decis 14 nov.):** extracția live = cache din `data/cache/` (generat de subagenți Haiku) sau stub regex; un text nou care nu e în cache iese cu stub. Folosește doar textele pregătite.
- **Extracția live depinde de laptop:** cu `stub regex` unele texte primesc alt tip (aici raportul de mai sus iese «avarie»), dar motorul îl tratează tot ca nod lipsă pentru că ID-ul numeric nu există în model. Cu Claude iese `nod_lipsa`.
- **Scenariul 1 se închide acum în timeline** (EV-028 al lui A, 23 oct.), deci partea live folosește alt nod, `7011223`. Nu mai folosi textul vechi cu `6925190`: nodul e deja în model și raportul ar doar confirma.
- **Apelurile:** 3 din 5 nu s-au putut potrivi (unul fără coordonate, două la peste 40 m de orice element); în timeline scad doar două elemente.
- **Proiectul Lovable** al lui C e netestat și nepublicat; demo-ul de mai sus rulează pe UI-ul plan B (Leaflet servit de FastAPI).

## Sesiunea 2: cazuri live noi (motorul real, verificate de B)
Toate cu motorul de pe `main`; sursa se alege din butoanele noi. Date FICTIVE.
1. **Cerere racordare, apel de client** (sursa `apel_client`, locația la 44.2850305, 26.0595998, Strada Liviu Rebreanu): lanț prezis de 2 stâlpi plus casa, punctat, scor ~0,64 (predicție). Apoi **cerere racordare de la racordări** la aceleași coordonate: cu extracția Claude (încredere ~0,7) iese tot predicție, ~0,74, sub pragul 0,75; dacă raportul vine structurat (formular/câmpuri, încredere 0,9) iese `adaugat` ~0,84, în timp real. Pentru demo cel mai sigur e să o accepți din UI (pasul 2). Mesaj: „fără date în GIS, rețeaua încearcă să prezică; cu date complete, se actualizează direct; omul poate confirma".
2. **Acceptă/Respinge:** pe un stâlp prezis de la pasul 1, „Acceptă": devine plin, halou verde, marcaj „om", scor ~0,98. Poți accepta doar primul stâlp și respinge restul.
3. **Fire mutate (sens giratoriu):** centrul la nodul 6513200 (44.2830448, 26.0636533), motiv „sens giratoriu", rază implicită 40 m: ~16 elemente trec „de verificat" (galben) și apar ~4 traseuri propuse punctat pe străzi. Un raport de verificare pe unul dintre ele îl readuce verde.
4. **Trace tabletă:** traseul `trace-1` din „Generează traseu ultima oră" (adresa „Strada Liviu Rebreanu, în dreptul curții", sursa tabletă, raport `nod_lipsa` executat): operatorul a verificat 3 stâlpi (devin verzi) și a stat ~22 min fără stâlp: apare un stâlp prezis la oprirea aceea (scor ~0,71).
5. **Demontat:** raport de la mentenanță că A-T-014 e demontat: rămâne, cu semnal; al doilea raport de la investiții: `scos_din_uz`.
6. **Val de apeluri:** 3 apeluri în 7 zile pe același element (ex. A-T-030): al 3-lea scade scorul dublu față de un apel singur, cu plafon.
7. **Locația operatorului (simulată):** cerere racordare fără coordonate, text „casă pe Strada Liviu Rebreanu"; buton „Folosește locația operatorului (simulată)": punct dummy pe stradă, ±40 m, marcat „simulată", cu indiciile găsite; lanț punctat, scor ~0,57 (cu clic ~0,71), tot predicție. Un text care nu se găsește în datele locale (ex. „strada Foo") dă eroare clară și cere clic, nu un punct inventat. Detalii: `docs/etapa-17-locatie-operator-racordare.md`.
Scenariul cu Play pe `?scenariu=extrem` depinde de `data/events/events.extreme.json` (A6).
