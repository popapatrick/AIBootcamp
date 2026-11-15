# Etapa 31: căutare pe stradă, partea geo + prompt (V6, D11)

Sesiunea 4, rol B. Modul nou `backend/geo/fereastra.py` + funcția publică `backend.geo.fereastra_strada`. **Integrarea în motor (pasul 3 din V6: candidații din fereastră) nu e făcută aici.** Date FICTIVE.

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
