# Calibrare pe cele 28 de rapoarte (B)

Date FICTIVE. Rulare: `.venv/bin/python -m backend.engine.calibrare --oracol`.

## Ce am comparat și cu ce
Rapoartele lui A sunt în `data/reports/` cu adevărul în `index.json`. `events.json` (extracția Claude a lui A) nu era pe `main`, iar eu nu am cheia OpenRouter. Am construit deci evenimente **„oracol"**: tip, ID și sursă din `index.json`, restul (coordonate, secțiune, status, formă) din text prin regex. Asta verifică **politica de scor presupunând extracție corectă**, nu extracția. A a măsurat extracția reală separat: tip corect 21/28, `element_id` corect 18/28. Când apare `events.json`, scriptul îl folosește singur.

## Rezultat (28 de rapoarte)
| Decizie | Nr. |
|---|---|
| scor actualizat (confirmare / semnal) | 12 |
| neaplicat | 9 |
| predicție | 3 |
| fără efect (planificat) | 2 |
| conflict | 1 |
| aplicat | 1 |

- **Scenariul 1 (nod lipsă `6925190`)**: cele 2 rapoarte au ID și vecini, dar **fără coordonate**. Rezultat: predicție (0,73, apoi 0,80 la al doilea raport), nu aplicat. Poziția nodului nu o știm, deci nu o aplicăm: motorul o pune la mijlocul dintre vecini ca ghid. Cu un raport cu coordonate (cum e `EV-S01` din stub) ar trece.
- **Scenariul 2 (înlocuire `A-T-002`)**: formularul de investiții se aplică (0,87); al doilea raport (text liber, aceeași secțiune) doar confirmă (0,84).
- **Scenariul 3 (coordonate greșite)**: lat/lon inversate se corectează; punctul zecimal pierdut (`4427960, 2606510`) se repară. Ambele marcate cu semnal și calitate redusă.
- **Scenariul 4 (apeluri)**: scad scorul puțin (la ~0,46–0,47 pe tronsoanele lovite), nu șterg nimic. 3 din 5 apeluri n-au putut fi potrivite: unul fără coordonate și două la > 40 m de orice element.
- **Scenariul 5 (două echipe, `A-T-021`)**: conflict detectat (0,51), nimic aplicat.
- **Scenariul 6 (verificări)**: tratate ca `verificare`: confirmă elementul (0,72–0,78).
- **Scenariul 7 (doar adresă)**: 4 rapoarte rămân **neaplicate** (geocodarea nu e implementată). Celelalte 5 „neaplicat": 3 apeluri nepotrivite (vezi mai sus), `racordari_06` (nicio referință) și `mentenanta_07` (cod `T-054` fără ID în oracol).

## Ce am schimbat în urma calibrării
1. **Nod lipsă lângă un vecin:** nodul `6925190` are un vecin la 3,9 m. O coordonată la el se potrivea cu vecinul și „confirma" vecinul în loc să propună un nod nou. Acum `nod_lipsa` se potrivește pe coordonate doar sub 2,5 m (`distanta_max_element_nou_m`), altfel e element nou. (Fixat și `defects.py` pe `6925190`, pentru că rapoartele lui A îl folosesc.)
2. **Nod fără coordonate:** cu doi vecini în text, se propune la mijlocul dintre ei, cu calitate ×0,5, și nu se aplică niciodată în model.
3. **Punct zecimal pierdut** în coordonate: reparat (calitate ×0,7).
4. **Conflict între rapoarte:** se compară cu orice observație anterioară a secțiunii (nu doar cu o modificare aplicată). Fără asta, scenariul 5 ieșea „predicție", nu „conflict".
5. **Raport de teren doar „semnalat"** (ex. defect găsit) confirmă elementul la jumătate (`factor_semnalat_teren`).
6. **Raza pentru apeluri:** 40 m (clientul e în clădire, nu pe linie), față de 15 m la rapoarte.
7. **Planificat pe un element existent** (ex. `R-T-006`, înlocuire în 2027): doar notă în „de ce", fără schimbare de scor.
8. **Scăderea în timp: −0,05 la 30 de zile** (rămâne cea inițială). La −0,07, în ziua a 87-a toate cele 530 de elemente neverificate treceau simultan sub 0,40 (97,6 % „de verificat"), un precipiciu. La −0,05, scorul mediu coboară lin: 0,60 → 0,53 (15 sept.) → 0,46 (27 oct.).
9. Tipul `verificare` adăugat în schema de eveniment (cerut de A).

## Ce nu e calibrat sau nu merge
- Pragurile 0,75 / 0,40 și ponderile propunerii sunt tot puncte de plecare: pe oracol nu am găsit cazuri unde să le mut, dar 28 de rapoarte sunt prea puține pentru a le „potrivi".
- Fără extracția reală (`events.json`) nu știm cum cad erorile ei de tip și ID în scor.
- Cod de tronson fără prefix (ex. `T-054` din `mentenanta_07`): rămâne ambiguu sau se potrivește cu categoria greșită; nu folosim încă nodurile din text ca să alegem categoria.
- Adresa nu e geocodată (scenariul 7), apelurile la > 40 m de orice element nu produc propuneri.
- Pozițiile deduse din vecini nu sunt la „curba" reală; punctul e doar un ghid.
- Nu am verificat vizual pe hartă.

## Sesiunea 2 (B9): scenariul extrem și reguli noi
Rulat `engine.model_scenariu("extrem")` (29 evenimente de bază + EV-X01..X10 ale lui A, `data/events/events.extreme.json`):
- Ramura pe etape: EV-X01 planificat -> `predictie` 0,8 (nu se aplică); EV-X02 `adaugat` 0,75; EV-X03 `adaugat` 0,93.
- Demontat: EV-X04 (investitii) -> `scor_actualizat` cu semnal („1 din 2 echipe necesare", scor combinat 0,85); EV-X05 (mentenanta) -> `aplicat`, `scos_din_uz`, scor combinat 0,97.
- Val de apeluri: EV-X07, X08 -> ~−0,035 fiecare; X09 -> −0,068; X10 -> −0,082 (agregare de la al 3-lea apel, plafon 0,40 cumulat).
- Lipsește din scenariu un caz `mutare_fire` (sens giratoriu); cerut lui A în board.
Pragurile noi (`mutare_fire`, `demontat`, `val_apeluri`, `racordare`, `trace`) sunt valori de pornire, necalibrate pe date reale; rezultatele de mai sus sunt doar pe date fictive.
Pe cele 29 de evenimente de bază rezultatul e neschimbat: 13 scor_actualizat, 8 neaplicat, 3 predicție, 2 fără efect, 1 conflict, 1 aplicat, 1 adăugat.

## Sesiunea 3: scor inițial al rețelei de start 0,90 (B3)
`scor.initial_retea_start: 0.90` înlocuiește 0,60 pentru elementele rețelei de start (`origine: retea_start`); `initial_element_kmz` rămâne în fișier, nefolosit de motor. Efecte măsurate cu `python -m backend.engine.calibrare`: deciziile pe cele 29 de evenimente de bază sunt neschimbate (13 scor_actualizat, 8 neaplicat, 3 predicție, 2 fără efect, 1 conflict, 1 aplicat, 1 adăugat); scorul mediu pornește de la 0,90 și coboară lin: 0,90 → 0,83 (15 sept.) → 0,76 (27 oct.). Cu −0,05 la 30 de zile, un element neverificat trece sub 0,40 („de verificat") abia după ~300 de zile (înainte ~120), deci scenariul „scade în timp" din `smoke_engine` se verifică acum la 365 de zile. Valorile rămân puncte de plecare, necalibrate pe date reale.

## Sesiunea 3: geocodarea pe `data/reports/geo-test.json` (B7, parțial)
Măsurat cu `backend.geo.geocodeaza` pe cele 15 adrese de test (fără AI: `EXTRACT_CLI=0`; cazurile cu ortografie cer AI) față de coordonatele așteptate din geometria OSM:

| grad | cazuri | eroare măsurată | acuratețe/precizie înainte | după |
|---|---|---|---|---|
| id, coordonate | 2 | 0 m | neapelată / 0,7 | neschimbat |
| stradă + număr | 3 | 143-245 m (mediană 197) | 0,55, ±25 m | **0,45, ±200 m** |
| stradă | 2 | 0 m față de mijlocul străzii; ±127-150 m | 0,40 | neschimbat |
| intersecție | 2 | 104 și 506 m (așteptat ≤ 30 m) | 0,60 declarat, cade pe stradă (0,40) | neschimbat; **de verificat de A** |
| ortografie | 3 | 2 necunoscute fără AI, 1 fals pozitiv la 1,9 km | 0,40 × 0,8 cu AI | neschimbat; de verificat cu `ai_cli` |
| reper, necunoscut, lipsă | 3 | corect `necunoscut` | - | - |

Concluzie: interpolarea numărului pe stradă nu e mai precisă decât strada, deci precizia declarată era prea optimistă (±25 m față de ~200 m reali). Am pus `geocodare.acuratete.strada_numar` 0,45 (ca să nu depășească mult „doar strada" 0,40) și `precizie_numar_m` 200 (limitele din `weights.limits.yaml` lărgite la [5, 500]). Deciziile pe cele 29 de evenimente de bază nu se schimbă (`verifica_reglaje`: 0 evenimente schimbate). Rămân de verificat: intersecțiile (A) și ortografia cu AI real (`ai_cli`). Valorile rămân puncte de plecare, necalibrate pe date reale.

## Sesiunea 4: scenariul din 55 de rapoarte
**Cum se generează.** `EXTRACT_CLI=0 .venv/bin/python scripts/genereaza_scenariu.py` citește `data/reports/index.json` și `.txt`-urile, ia extracțiile Haiku din `data/cache/` (fără AI; dacă lipsește un text din cache, se oprește), pune `event_id` `EV4-001`… (ordinea: dată, apoi nume fișier) și `text_original`, apoi scrie `data/events/events.json` sortat. Nu corectează tipurile. Diferă de `tip_asteptat`: `2026-08-13_mentenanta_06` (nod_lipsa în loc de activ_inlocuit), `2026-09-10_investitii_03` (linie_planificata în loc de nod_lipsa), `2026-11-06_investitii_10` (racord_nou în loc de nod_lipsa). Vechile evenimente sunt în `data/events/arhiva/` (scenariul extrem e scos, D7).

**Decizii (55 de evenimente).** scor_actualizat 27, adaugat 9, predictie 9, de_verificat 5, neaplicat 4, fara_efect 1. `neaplicat`: 3 × `linie_planificata` (EV4-010, 021, 045: nimic de aplicat, doar planificat) și 1 × `mutare_fire` (EV4-026). Cele 4 `verificare_om` ies `scor_actualizat` (motorul din acest branch nu are încă `verificare_om`).

**Distribuție (setul de bază, înainte de reglaj, total la 15 nov.).** verde 72,2 %, galben 0,7 %, portocaliu 9,0 %, roșu 18,2 %: în afara țintei (verde 70-82, galben 8-15, portocaliu 5-10, roșu 2-6). Cauze: (1) cele 103 SIM-* scad cu -0,05/30 zile și ajung 0 % galben, 53 % roșu; (2) ~67 de elemente prezise pe străzi (`analiza_harta`, plafon 0,40, scoruri 0,14-0,37) sunt roșii.

**Propunere de reglaj (NEaplicată):** `scor.scadere_per_30_zile` -0,05 → -0,02; `retea_start.fractie_galben` 0,45 → 0,60; `retea_start.fractie_portocaliu` 0,35 → 0,30; `plafon_locatie.strada` 0,55 → 0,68; `plafon_locatie.analiza_harta` 0,40 → 0,66. Rezultat la ultima dată (13 nov.): verde 72,2 %, galben 14,0 %, portocaliu 8,1 %, roșu 5,6 %: în țintă. Atenție: smoke_sesiune4 pică la 3 aserțiuni (plafon `analiza_harta` 0,40 hardcodat, minim GIS, racordare ≤ 0,40) și trebuie actualizat odată cu reglajul.

**Verificare.** `verifica_reglaje` tipărește „Distribuție culori la <ultima dată>: …: în țintă / în afara țintei” (ținta e `TINTA_DISTRIBUTIE` în cod). Eșec doar cu `--strict-distributie`; `--rapid` o sare. Referința de aur `data/golden/calibrare-referinta.json` a fost rescrisă (ID-urile vechi `EV-0xx` nu mai există, deci nu are rost o diferență).

**Reglaj final al distribuției (decizia lui Victor: se măsoară doar rețeaua).** Criteriul din `distributie_culori` (`backend/engine/verifica_reglaje.py`): intră în procent elementele care fac parte din rețea la data respectivă = ID în `model._elemente()` (GIS, SIM-*, plus ce s-a adăugat/aplicat din rapoarte, căci `net` crește la aplicare) cu nivel `in_model` sau `de_verificat`. NU intră: predicțiile punctate (nivel `predictie`: element_nou, stâlpi prezisi, `PLAN-*`, `MUT-*`), pinurile `VER-*` și elementele retrase; sunt marcaje, nu rețea, și pot rămâne roșii/portocalii. Ele se afișează separat, informativ („predicții: N (verde/galben/portocaliu/roșu)”). Plafoanele `plafon_locatie.*` NU s-au schimbat (D6), deci propunerea veche de mai sus (strada 0,68, analiza_harta 0,66) NU se mai aplică.

Încercări (rețea: verde/galben/portocaliu/roșu la 2026-09-15 | 2026-10-15 | 2026-11-13; ținta 70-82 / 8-15 / 5-10 / 2-6):

| # | Valori | 15 sept. | 15 oct. | 13 nov. |
|---|---|---|---|---|
| 0 | actuale (scădere -0,05; galben 0,45; portocaliu 0,35) | 82,2/7,8/7,7/2,3 | 81,6/0,5/9,3/8,6 | 80,7/0,5/9,9/8,9 (galben și roșu în afara țintei) |
| 1 | scădere -0,02 | 82,2/8,3/7,2/2,3 | 81,6/8,4/7,6/2,3 | 80,7/8,0/8,6/2,6 (în țintă, galben la limită) |
| 2 | -0,02; galben 0,60; portocaliu 0,30 | 82,2/11,6/5,3/0,9 | 81,6/11,7/5,8/0,9 | 80,7/11,2/6,8/1,2 (roșu sub 2) |
| 3 | -0,03; galben 0,60; portocaliu 0,30 | 82,2/11,6/5,3/0,9 | 81,6/11,2/6,2/0,9 | 80,7/0,6/13,1/5,5 (galbenul se prăbușește în nov.) |
| 4 | -0,03; galben 0,50; portocaliu 0,35; scor_galben 0,74 | 82,2/9,7/6,6/1,6 | 81,6/9,3/7,5/1,6 | 80,7/9,4/2,5/7,4 |
| 5 | -0,02; galben 0,55; portocaliu 0,30 | 82,2/10,6/5,6/1,6 | 81,6/10,7/6,1/1,6 | 80,7/10,3/7,1/1,8 (roșu sub 2) |
| 6 | -0,025; galben 0,55; portocaliu 0,30 | 82,2/10,6/5,6/1,6 | 81,6/10,7/6,1/1,6 | 80,7/0,6/16,8/1,8 |
| 7 | -0,03; galben 0,55; portocaliu 0,30; scor_galben 0,72 | 82,2/10,6/5,6/1,6 | 81,6/10,3/6,5/1,6 | 80,7/10,3/2,5/6,5 |
| 8 | -0,02; galben 0,50; portocaliu 0,32 | 82,2/9,7/6,1/2,0 | 81,6/9,8/6,5/2,0 | 80,7/9,4/7,6/2,3 |
| 9 | -0,02; galben 0,50; portocaliu 0,35 | 82,2/9,7/6,6/1,6 | 81,6/9,8/7,0/1,6 | 80,7/9,4/8,0/1,8 (roșu sub 2) |
| **10 (ales)** | **-0,02; galben 0,50; portocaliu 0,30** | **82,2/9,7/5,8/2,3** | **81,6/9,8/6,2/2,3** | **80,7/9,4/7,2/2,6** (în țintă) |

Valori alese: `scor.scadere_per_30_zile` -0,05 → -0,02, `retea_start.fractie_galben` 0,45 → 0,50, `retea_start.fractie_portocaliu` 0,35 → 0,30 (restul SIM = roșu, 20 %). Predicțiile (în afara procentului) la cele 3 date: 33 (1 portocaliu, 32 roșii), 56 (1 galben, 1 portocaliu, 54 roșii), 77 (2 galbene, 1 portocaliu, 74 roșii). Observații: la 15 sept. verdele e 82,2 % (cu 0,2 peste țintă; ținta contează doar la ultima dată). Rețeaua își schimbă culorile în timp mai ales prin ce intră din rapoarte (verde 82,2 → 80,7 %, portocaliu 5,8 → 7,2 %, roșu 2,3 → 2,6 %), nu din scăderea GIS (stabilă, 0,95).

Efect pe calibrare: 2 evenimente schimbă scorul față de referința de aur, nu și decizia: EV4-032 `avarie_semnalata` 0,455 → 0,504 și EV4-033 `avarie_semnalata` 0,425 → 0,474 (scăderea mai mică în timp a elementelor SIM atinse). Referința NU a fost rescrisă (o face verificatorul). Singura aserțiune de test schimbată: `smoke_sesiune4`, „scor_la_data: minim GIS...”, care codifica -0,05 (0,85); acum citește `scor.scadere_per_30_zile` din weights.

Verificare: `EXTRACT_CLI=0 .venv/bin/python -m backend.engine.verifica_reglaje --strict-distributie` tipărește „Distribuție culori (doar rețea) la 2026-11-13: verde 80.7 %, galben 9.4 %, portocaliu 7.2 %, roșu 2.6 % ...: în țintă” și linia „predicții (nu intră în procent): 77 (...)”; cod 0. `scripts/verifica_tot.sh` rulează acum verificarea cu `--strict-distributie` și iese TOT VERDE; dacă un reglaj viitor scoate rețeaua din țintă, scriptul pică.

**Sesiunea 4, corecție (scoase din uz nu sunt rețea).** După EV4-039 (sens giratoriu Crinului × Rebreanu) scenariul are 12 tronsoane `nivel: scos_din_uz` („demontat probabil”, scor 0,35, traseul vechi al firelor mutate; vezi `docs/etapa-28-mutare-fire-document.md`). Numărate ca rețea, ele erau roșii (7,3 %) și scoteau distribuția din țintă. Criteriul din `distributie_culori` (`backend/engine/verifica_reglaje.py`) s-a schimbat: elementele cu `nivel: scos_din_uz` (demontate sau „demontat probabil”) NU sunt rețea la acea dată, deci nu intră în procent și nici în „predicții”; se afișează separat, informativ („scoase din uz: N”), ca predicțiile. `weights.yaml` și ținta (`TINTA_DISTRIBUTIE`) neschimbate. Rezultat la 2026-11-14: rețea verde 76,9 %, galben 9,1 %, portocaliu 8,4 %, roșu 5,6 % (în țintă); înainte: 75,8 / 9,0 / 7,8 / 7,3. Predicții: 63 înainte de linia planificată (după ea, 66); scoase din uz: 12. `distributie_culori` întoarce acum și `scoase_din_uz` în dicționarul de predicții.

**Sesiunea 4, linia planificată pe hartă.** Rapoartele `linie_planificata` (EV4-010, 028, 046) ies acum predicții punctate `PLAN-<event>` pe străzi (`docs/etapa-27-analiza-harta.md`, secțiunea „Linie planificată”): EV4-010 neaplicat -> predicție 0,503, EV4-028 fara_efect 0,932 -> predicție 0,8, EV4-046 neaplicat -> predicție 0,475. Predicțiile nu intră în procentul rețelei (distribuția rămâne în țintă). În diferența de calibrare apare și EV4-021 `nod_lipsa` (neaplicat -> adaugat 0,626, decizia „element nou” din căutarea pe stradă, nelegată de linia planificată); referința de aur NU a fost rescrisă.

**Sesiunea 4b, ture de tracking (B3).** Scenariul are acum 2 evenimente `tracking_tura` (`EV4-T01`, `EV4-T02`); calibrarea nu raportează diferențe pe evenimentele vechi, cele 2 ture sunt noi față de referință (nu rescrisă), iar distribuția „doar rețea” rămâne în țintă (verde 76,9 %, galben 9,1 %, portocaliu 8,7 %, roșu 5,3 % la 2026-11-14; stâlpii presupuși `TRK-*` sunt predicții și nu intră în procent).
