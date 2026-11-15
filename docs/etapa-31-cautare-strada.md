# Etapa 31: căutare pe stradă, partea geo + prompt (V6, D11)

Sesiunea 4, rol B. Modul nou `backend/geo/fereastra.py` + funcția publică `backend.geo.fereastra_strada`. **Integrarea în motor (pasul 3 din V6) e în „Partea 2” de la sfârșitul documentului.** Date FICTIVE.

## Ce face
Dintr-o adresă parțială („stâlp căzut pe Strada Viilor, lângă nr. 15”) întoarce o **fereastră pe stradă**: de unde până unde (în metri, de-a lungul străzii), un punct estimat, precizia, metoda și un motiv în română. Determinist, fără AI în funcție (AI doar extrage indiciul în prompt și, ca și azi, poate alege numele străzii din lista din cache).

```python
from backend.geo import fereastra_strada
fereastra_strada(referinta, strazi, cfg, ancore=None, net=None) -> dict
```
- `referinta`: `adresa_structurata {strada, numar, reper, indiciu}` sau `adresa` (text liber).
- `strazi`: `backend.engine.osm.strazi()`; `cfg`: `load_weights()` (secțiunile `cautare_strada`, `geocodare`, `zona`).
- `ancore`: `[{strada, numar, lat, lon}]` = adrese deja cunoscute din rapoarte anterioare (le dă motorul). Contează doar cele de pe aceeași stradă (potrivire pe nume normalizat: „Str. Viilor” = „Strada Viilor”); `numar` trebuie să fie întreg.
- `net`: rețeaua de start (centrul zonei, nodurile pentru indiciul `element`); `None` = `load_network()` o dată în modul.

Ieșire: `{status: gasit|necunoscut|in_afara_zonei, strada, de_la_m, pana_la_m, punct{lat,lon}, precizie_m, metoda: ancore|conventie|indiciu, indiciu{tip,numar,numar_2,strada_2,element_id,distanta_stalpi,paritate,sursa: extractie|regex}|None, ancore_folosite[{strada,numar,lat,lon,pozitie_m}], latura: par|impar|None, acuratete, motiv, linie[[lat,lon],...]}`. `necunoscut` = toate câmpurile goale (None / `[]`), nimic inventat.

`geocodeaza(referinta, strazi, cfg, net=None, ancore=None)` (semnătură extinsă cu `ancore` la coadă) are acum cheia aditivă `fereastra` (doar la `gasit`/`in_afara_zonei`) și, la adrese cu număr, ia poziția din fereastră (nu mai din fracția N/100). Celelalte chei sunt neschimbate.

## Cum se verifică
```
EXTRACT_CLI=0 .venv/bin/python -m backend.geo.smoke_geo     # așteptat: ultima linie „OK: 166 verificări”
EXTRACT_CLI=0 bash scripts/verifica_tot.sh
```
Exemplu real (Strada Viilor, „lângă nr. 15”, indiciu `langa`):
- fără ancore: `metoda conventie`, `de_la_m 0.0` – `pana_la_m 184.0` (nr 15 la 84 m, ±100 m, tăiat la 0), `latura impar`, `acuratete 0.36`;
- cu 2 ancore (nr 5 la 40 m, nr 45 la 200 m): `metoda ancore`, nr 15 la 80 m, `de_la_m 40.0` – `pana_la_m 120.0`, `precizie_m 40`, `acuratete 0.45`.

## Decizii (convenții)
- **Capătul de start** = capătul căii cel mai apropiat de Șoseaua Principală dacă e la < 300 m; pentru Șoseaua Principală sau fără capăt la < 300 m: capătul cel mai apropiat de centrul rețelei (`zona.centru_retea`). Se folosește cea mai lungă cale a străzii (ca `_grupe`). Distanțele `de_la_m`/`pana_la_m` pornesc de aici.
- **Numere**: cresc de la start; fără ancore poziția = `(N // 2) * 2 * metri_per_numar` (nr 14 și 15 la același loc, nr 2 la 12 m), plafonată la lungimea căii. Precizie `precizie_conventie_m` (100), acuratețe `strada_numar x factor_numere_conventie` (0,36).
- **Par = stânga, impar = dreapta** privind în sensul de creștere a numerelor, la `decalaj_paritate_m` (8 m) de ax: două numere de parități diferite sunt la ~16 m una de alta.
- **Ancore**: proiectate pe cale; N interpolat liniar între ancorele vecine (după număr), extrapolat cu `metri_per_numar` de la cea mai apropiată dacă e în afara lor; precizie `precizie_ancore_m` (40), acuratețe `strada_numar` (fără factor).
- **Indicii**: `intre` = mijlocul, precizie jumătate din distanță (min 20 m); `dupa`/`inainte` = fereastră `fereastra_dupa_m` (60) după/înainte de N (după = spre numere mari); `capat` = capătul OPUS startului, `inceput` = capătul de start, precizie `precizie_capat_m`, acuratețe ca la numere cu convenție; `colt` = intersecția cu `strada_2` (ca în `geocodeaza`), precizie `precizie_intersectie_m`, acuratețe `intersectie`; `element` = nodul din `net` proiectat pe stradă, fereastră `distanta_stalpi x 40 m` (implicit 1 stâlp) în ambele sensuri sau doar spre capăt/început dacă textul zice „spre capăt/început”, acuratețe `strada_numar`; `vizavi` = același loc ca N, partea opusă; `parte` = toată strada, cu latura cerută; doar stradă = toată strada, precizie lungime/2, acuratețe `strada` (sau `reper`, dacă strada vine din reper).
- **Reveniri fără blocaj**: `strada_2` negăsită sau care nu se intersectează, element absent din rețea sau la > 150 m de ax = toată strada ca fereastră, cu motivul spus.
- **Indiciul**: se ia din `adresa_structurata.indiciu`; dacă lipsește sau e invalid, `deduce_indiciu` (regex, română cu/fără diacritice, vezi `smoke_geo`) din strada + reper + adresa; apoi `numar` din câmpul structurat. `sursa` arată de unde vine.
- **Safeguard**: punct în afara `zona.raza_max_m` = `in_afara_zonei` (motiv din `motiv_afara`; punctul rămâne). Exemplu: capătul opus al Șoselei Principale (4 km) iese din zonă.
- **Prompt** (`extract.py`, `SYSTEM`): extinderea care cere `referinta.adresa_structurata.indiciu` (cu 4 exemple) e scrisă, dar **amânată pentru Faza 2**: orice schimbare a promptului schimbă toate cheile din `data/cache/`, deci intră în același commit cu reumplerea cache-ului cu Haiku pe textele noi. Până atunci indiciul vine din `deduce_indiciu` (regex), care acoperă aceleași formulări.

## Limite
- OSM nu are numere de casă: poziția e convenție sau ancore, nu adevăr de teren. Pe străzi cu mai multe căi se folosește doar cea mai lungă (Strada Viilor: 376 din 734 m).
- „La capătul străzii” = capătul opus startului (convenție); „la intrarea pe stradă” = start. Dacă omul se referă la alt capăt, fereastra e greșită; sursa rămâne `indiciu`, acuratețe mică.
- `dupa`/`inainte` au fereastră fixă de 60 m, fără a lărgi cu incertitudinea poziției lui N.
- Regex-ul acoperă formulările din plan; altele dau `indiciu None` (toată strada). Numele străzii din text liber care conține „strada” în altă frază poate rata potrivirea (ca în `geocodeaza`).
- Promptul cu `indiciu` nu e încă activ (vezi mai sus): până la Faza 2, indiciul vine doar din regex. Cu promptul actual, `verifica_tot.sh` e verde.
- `data/reports/geo-test.json` (al lui C) are coordonate așteptate din vechea fracție N/100; la cazurile `strada_numar` smoke-ul verifică acum metoda (`conventie`, ±100 m), nu toleranța veche (gt-05: 260 m diferență față de așteptat).

## Pentru cel care integrează în motor
1. Apelează `fereastra_strada(referinta, strazi, cfg, ancore, net)` (sau citește `geocodeaza(...)["fereastra"]`) după ce nu există ID/coordonate.
2. Construiește `ancore` din adresele deja cunoscute: `{strada, numar, lat, lon}` din rapoarte cu adresă + element potrivit sigur, sau cu coordonate. Ordinea nu contează; același număr de două ori: rămâne prima.
3. Candidații = elementele de tipul cerut la `latime_laterala_m` de `linie` (sau între `de_la_m` și `pana_la_m` pe cale); `punct` = punctul față de care se ordonă distanța. `precizie_m` e semi-lățimea ferestrei.
4. `metoda` + `acuratete` + `motiv` merg în pasul `cautare_strada` (`{strada, de_la_m, pana_la_m, punct, precizie_m, metoda, indiciu, ancore[]}` din `ancore_folosite`). Pentru `in_afara_zonei`: `neaplicat`, ca la `geocodeaza`.
5. `geocodeaza` rămâne pentru rezerva „un punct”; are aceeași semnătură plus `ancore` opțional.

---

# Partea 2: integrarea în motor (V6, pasul 3 + scara de localizare)

Sesiunea 4, rol B. Cod în `backend/engine/sesiune2.py` (căutarea) și `backend/engine/model.py` (ramura din `apply_event`, `self.ancore`, `self.pinuri`). Fără AI, determinist; rulează cu `EXTRACT_CLI=0`. Date FICTIVE.

## Ce face
„Stâlp căzut pe Strada Viilor nr. 12” (fără ID, fără coordonate) nu mai iese `neaplicat`. Când locația vine din adresă cu stradă (număr, indiciu relativ, intersecție, reper sau doar stradă), motorul ia fereastra de pe stradă (`geocodeaza(...)["fereastra"]`, cu `ancore=self.ancore`) și **caută elementele din ea**:

| Candidați în fereastră | Rezultat |
|---|---|
| 1 | `potrivit`, metoda `cautare_strada`, calitate `cautare_strada.calitate_cautare_unic` (0,6); raportul se aplică pe el prin `_efect_pe_element` (la `activ_demontat`: `_demontat`). Scorul elementelor non-GIS rămâne plafonat de `sursa_locatie` a elementului (V1); GIS nu are plafon. |
| 2..`max_candidati_predictie` (4) | decizie `predictie`: cel mai apropiat de `punct` primește „probabil acest element” (marcaj, vezi mai jos); raportul **nu** se aplică. |
| peste 4 | decizie `de_verificat` pe fereastră, niciun element atins; motivul spune strada și fereastra (`de_la_m`–`pana_la_m`). |
| 0, tip care creează element (`nod_lipsa`, `racord_nou`) | element nou la `fereastra.punct`, prin `_propune_element_nou`; `sursa_locatie` = `adresa_numar` (număr sau indiciu cu număr), `intersectie` (colț), `reper` sau `strada`. |
| **Tipuri noi (`nod_lipsa`, `racord_nou`), orice număr de candidați** | **Decizia lui Victor, 15 nov.:** mereu element nou la `fereastra.punct` (rândurile 1, 2–4 și > 4 de mai sus se aplică doar tipurilor despre elemente existente). Stâlpii existenți din fereastră NU se potrivesc și NU dau `de_verificat`; apar doar informativ (vezi mai jos). |
| 0, tip despre un element existent (`avarie_semnalata`, `activ_inlocuit`, `verificare`, `activ_demontat`) | **pin „de verificat”**: element nou `VER-<event_id>`, `nivel de_verificat`, scor = plafon(sursa) × 0,5, motiv „Nu există stâlp în fereastra de pe <strada>”. |

Tipurile `cerere_racordare`, `mutare_fire`, `linie_planificata` și `verificare_om` nu caută pe stradă (comportament neschimbat). ID sau coordonate în text: neschimbat (nu trec prin geocodare). `neaplicat` rămâne doar fără niciun indiciu de loc, la stradă necunoscută în cache (fără indiciu, ca azi) sau în afara zonei de 3 km (`eronat_prototip`).

**Ce e candidat.** Noduri din `self.net["noduri"]` (stâlpi și orice nod adăugat din rapoarte), fără predicții, fără elemente retrase și fără `*-casa`; tronsoane dacă evenimentul vizează un cablu (`detalii.sectiune_*` dată, sau textul spune tronson/cablu/linie/conductor fără stâlp/nod/post), altfel noduri. Un element e în fereastră dacă e la cel mult `latime_laterala_m` (15 m) de porțiunea de stradă dintre `de_la_m` și `pana_la_m` (`fereastra["linie"]`); capetele ferestrei se extind deci cu cel mult 15 m. Tronsoane: orice punct al lor (eșantion la 5 m). `distanta_m` = distanța la `fereastra.punct`; `pozitie_m` = metri de la capătul de start al străzii.

**Predicția „probabil acest element” (decizia de reprezentare).** Nu schimbăm `nivel`, `scor` și `sursa_locatie` ale elementului existent (un stâlp GIS verde nu devine punctat din cauza unui raport vag). Starea lui primește doar `predictie` = `{metoda: "cautare_strada", propunere: {proprietate: "element_probabil", valoare: <id>}, scor_propunere, pondere, alternative: [{element_id, distanta_m, pondere, scor_propunere, motiv}], strada, indiciu}`, plus un motiv în „De ce?”. Scorul propunerii = `scor_propunere(event, acuratete fereastră)` plafonat de sursă, înmulțit cu ponderea ∝ 1/(d+10) normalizată (cel mai apropiat ia cel mai mult; ponderile sumează 1). Dacă propunerea e sub `praguri.predictie` (0,40): `de_verificat`. În `schimbari`: `ce: "predictie"`. Un raport ulterior sigur pe același element (ID, coordonate, candidat unic) șterge marcajul (`_fara_marker`). Marcajul nu e acceptabil prin `POST /predictii/{id}/decizie` (elementul e deja în model: 409 `deja_decis`).

**Pinul „de verificat”.** Nu intră în `self.predictii` (ca să nu fie „întărit” de rapoarte apropiate și să nu fie acceptabil), ci în `self.pinuri` (`{geometrie}`); apare în `snapshot()` ca Point, `nivel de_verificat`, `origine generat_model`, `t0 false`, banda din scor (de obicei portocaliu/roșu). Scade în timp ca orice element din raport.

**Ancore.** `self.ancore` (inițial goală, determinist) primește `{strada, numar, lat, lon}` când un raport cu `adresa_structurata.strada` + `numar` întreg ajunge la o locație sigură: potrivit cu ID (nod), coordonate explicite în același raport (nu din geocodare/trace), sau 1 candidat unic în fereastră cu indiciul `numar`. Predicțiile, „de verificat” și elementele noi nu devin ancore. Același număr pe aceeași stradă: rămâne prima. Rapoartele următoare pe stradă primesc fereastra cu `metoda ancore`, ±40 m.

**Corecție de sursă.** `detalii.geocodare.tip` e acum setat din fereastră (`adresa_numar` | `intersectie` | `strada` | `reper`). Înainte, motivul geocodării cu număr nu mai conținea „interpolat”, deci `_sursa_din_geocodare` cădea pe `strada` și plafonul `adresa_numar` (0,70) nu se aplica unui element nou din adresă cu număr.

**Informativ la tipurile noi.** Pasul `cautare_strada`: `candidati` rămâne completat, `ales` = null, motivul spune că elementul nou e la punctul estimat și enumeră stâlpii din fereastră. `potrivire`: `absent_din_model`. Elementul nou: dacă e predicție (planificat sau sub prag), `predictie.alternative` = `[{element_id, distanta_m, motiv: "poate fi unul dintre aceștia (stâlp existent în fereastră), la X m ..."}]` (fără pondere); dacă e aplicat (P1: executat de teren de la 0,50, plafon după sursă), lista e în motivul „De ce?” și în `rezultat.stalpi_existenti_in_fereastra` al pasului `predictie`. Aplicat/predicție se decide ca până acum (`_propune_element_nou`). Elementul nou din fereastră nu devine ancoră. Cod: `cs["actiune"]` rămâne None pentru tipurile noi; `event["_stalpi_fereastra"]` (intern) duce lista la `_propune_element_nou`.

## Ieșiri
Pas nou în `trace["pasi"]`, înaintea `potrivire` (și în `event["detalii"]["cautare_strada"]`, varianta compactă fără `ancore`/`indiciu`/`linie`):
`{"nume": "cautare_strada", "incredere": acuratete, "rezultat": {strada, de_la_m, pana_la_m, punct{lat,lon}, precizie_m, metoda (ancore|conventie|indiciu), indiciu {tip, numar, numar_2, strada_2, element_id, distanta_stalpi, paritate, sursa, text} (`text` în română: „nr. 12”, „lângă nr. 15”, „între nr. 10 și 20”, „la capătul străzii”, „doar strada” etc.; fără indiciu: obiect cu `tip: null`, `text: "doar strada"`), ancore [{strada, numar, lat, lon, pozitie_m}], tip_cautat (nod|tronson), sursa_locatie, candidati [{element_id, distanta_m, pozitie_m}], ales (element_id | null), linie [[lat, lon], ...], motiv}}`.
Exemplu real (Strada Crinului nr. 60, 1 candidat; `linie` omisă):
```json
{"strada": "Strada Crinului", "de_la_m": 260.0, "pana_la_m": 398.3, "punct": {"lat": 44.28126, "lon": 26.060126}, "precizie_m": 100.0, "metoda": "conventie",
 "indiciu": {"tip": "numar", "numar": "60", "numar_2": null, "strada_2": null, "element_id": null, "distanta_stalpi": null, "paritate": null, "sursa": "extractie", "text": "nr. 60"},
 "ancore": [], "tip_cautat": "nod", "sursa_locatie": "adresa_numar",
 "candidati": [{"element_id": "6784406", "distanta_m": 31.9, "pozitie_m": 388.0}], "ales": "6784406", "motiv": "Strada Crinului, nr. 60: la 360 m de capătul de start, ... Un singur stâlp în fereastră (nr. 60): 6784406."}
```
`potrivire` (după `cautare_strada`): `potrivit` (1), `ambiguu` (2+ sau peste maxim), `absent_din_model` (0), cu `metoda: cautare_strada` și `semnale` care conțin `cautare_strada`. Decizia: `scor_actualizat` | `predictie` | `de_verificat` | `adaugat`.

## Cum se verifică
```
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune4   # ultima linie: „smoke_sesiune4: 52/52 OK” (29 verificări de căutare pe stradă, 5 pentru tipurile noi)
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune2   # „OK: 65 verificări”
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_engine     # „OK: 38 verificări”
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_match      # „OK: 13 cazuri”
EXTRACT_CLI=0 .venv/bin/python -m backend.geo.smoke_geo           # „OK: 166 verificări”
```
Aserțiuni schimbate intenționat în `smoke_sesiune2.py` (3, la „geocodare”): potrivirea din adresă are acum metoda `cautare_strada` (nu `adresa`); „stradă fără număr” nu mai are semnalul `adresa_prea_imprecisa_pentru_element_existent`; avaria doar cu stradă nu mai e `nepotrivit`/`neaplicat`, ci `de_verificat` (pin).

## Decizii
- Fereastra se calculează o singură dată, în `_foloseste_geocodare`, și circulă ca cheie internă `event["_fereastra"]` (nu iese din motor, nu ajunge în jurnal).
- Nod lipsă / racord nou: mereu element nou, indiferent de candidați (decizia lui Victor, 15 nov.; înainte urmau regulile elementelor existente). Candidații rămân informativ.
- Traseul simulat (`trace_factor`) nu se aplică pe calea căutării pe stradă (e oprit oricum prin `demo.trace_generat_activ: 0`).
- Aprobarea omului pe pin nu există: se verifică printr-un raport nou sau prin `verificare_om` pe un element real.

## Limite
- Nodurile adăugate din rapoarte (`NOU-*`) devin candidați la fel ca stâlpii GIS; pe străzi dense (Bălții, Carpati, Șoseaua Principală) aproape orice fereastră are peste 4 candidați, deci rezultatul e `de_verificat`.
- Un `nod_lipsa` cu stâlpi în fereastră creează totuși un nod nou (decizie): dacă omul se referea la un stâlp existent, apare un duplicat lângă el; stâlpii posibili sunt listați informativ ca alternative.
- Pe străzi fără noduri în cache (Liviu Rebreanu, Plopilor, Fagului, Liliacului, Oituz etc.) orice avarie dă pin, orice nod lipsă dă element nou.
- Capetele ferestrei se extind cu `latime_laterala_m` (disc, nu tăiere dreaptă).
- Ancora unui candidat unic e poziția nodului, nu a casei cu numărul respectiv.
- Fără promptul cu `indiciu` activ (Faza 2), indiciul vine din regex: formulări necunoscute = doar strada.
- Calibrarea: `data/golden/calibrare-referinta.json` (28 de rapoarte, toate cu ID/coordonate) nu se schimbă. Schimbarea din 15 nov. (tipuri noi mereu element nou) mută 8 din cele 48 de evenimente din cache cu doar adresă (4 `nod_lipsa`, 4 `racord_nou`: toate devin `adaugat`). Înainte, pe cele 39 de evenimente din `data/cache/` care au doar adresă, 19 își schimbă decizia față de înainte (6 `neaplicat` -> `de_verificat`, 2 `neaplicat` -> `predictie`, 5 `adaugat` -> `de_verificat`, etc.).

## Pentru Claudiu (API/UI)
- `backend/api/prezentare.py` citește deja pasul: `strada`, `de_la_m`, `pana_la_m`, `precizie_m`, `metoda`, `indiciu.text`, `candidati`, `ales`. `indiciu` e mereu obiect cu `text` (la „doar strada”: `tip: null`).
- Decizia `de_verificat` apare acum și fără conflict (fereastră cu prea mulți candidați, pin); `DECIZII` din `prezentare.py` are deja text pentru ea.
- Pe hartă: „probabil acest element” = `predictie.metoda == "cautare_strada"` în `properties.predictie` al elementului (nivel `in_model` neschimbat); alternativele în `predictie.alternative`. Pinul = element `VER-<event_id>`, `nivel de_verificat`, Point.
- `schimbari[].ce` poate fi `predictie` pe un element existent (scor_inainte = scor_dupa) sau `de_verificat` pe un pin nou.

