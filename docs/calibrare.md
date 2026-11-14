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
