# Prompt Lovable sesiunea 2: C2 + C3 (grupat, NETRIMIS)

- **Dependențe (pe `main` înainte de trimis):** B2 (`clasa` în `/retea`, gata, commit af07246); C1 în API: `GET /exemple?sursa=`, `schimbari[]` în răspunsul `POST /rapoarte`, `ultima_actualizare` în `GET /retea`, `/health`, `POST /rapoarte` (B3 la Victor: `schimbari` și `ultima_actualizare` din motor); A3.1 `data/reports/exemple-dummy.json` (acum lipsește; fără el `/exemple` e gol și UI-ul arată „fără exemple"). Fără B3/C1 promptul merge, dar „Show pipeline" nu are schimbări și data arată „—".
- **Cost estimat:** ~3-4 credite (un singur mesaj mare, ecran + hartă; prompturile anterioare au costat 0,9-2,8 fiecare). Nu se publică fără confirmarea omului.
- **Verificare după:** deschide `…lovable.app/?api=<tunel>` (tunelul din `demo_start.sh`, nu se scrie în repo): (1) nodurile au culori pe clasă, halou pe stare, legenda apare; (2) 4 butoane de sursă, „Generează exemplu" umple textul; (3) trimite un exemplu: harta se reîncarcă, „Show pipeline" arată pașii și `schimbari`; (4) scala continuă, Play, „De ce?", banner DATE FICTIVE funcționează ca înainte; (5) cu API vechi, UI nu crapă (afișează „—").

---

## PROMPT (de lipit în Lovable)

Modifică aplicația existentă (frontend, fără DB/auth, în română). Date FICTIVE. Datele vin doar din API (`API_BASE`). Fă ambele părți de mai jos într-o singură trecere.

### NU SCHIMBA (trebuie să rămână exact cum e)
- Scala continuă de culoare după scor (HSL, 0,3 roșu → 0,55 galben → 0,8 verde, cum e acum) rămâne disponibilă ca mod de colorare: adaugă un comutator „Colorare: tip (KMZ) / scor"; implicit „tip (KMZ)".
- Timeline-ul cu butonul Play (și selectarea datei, `GET /retea?data=`).
- Panoul „De ce?" la clic pe element (`GET /element/{id}`) și lista „Evenimente".
- Parametrul `?api=<URL>` din adresă care setează `API_BASE`, plus „Setări → API_BASE".
- Bannerul vizibil „DATE FICTIVE".
- Cele 3 exemple demo existente din „Proces raport" (textele 1, 2 și apelul cu coordonate) rămân, cu aceleași texte, surse și date; „Generează exemplu" se adaugă lângă ele.
- Mesajul „API indisponibil, setează API_BASE" și `mod` din `/health` în colț.

### PARTEA 1 (C2): aspectul hărții ca în KMZ
Fiecare feature din `GET /retea` are `properties.clasa`. Desenează după ea (două straturi independente: simbol = tip, halou = stare).

Noduri (Point), cerc cu contur alb subțire:
| `clasa` | culoare | rază | notă |
|---|---|---|---|
| `casa` | verde `#2ca02c` | mică (4 px) | serie 7 |
| `important` | gri `#7f7f7f` | medie (6 px) | serie 5 și 6 |
| `origine` | portocaliu `#ff7f0e` | medie (7 px) | origine plecare JT |
| `post` | pătrat negru `#111111` cu contur alb | mare (10 px) | post de transformare; formă diferită de cerc |

Tronsoane (LineString), grosime 2 px:
| `clasa` | culoare |
|---|---|
| `aerian` | albastru `#1f5fbf` |
| `ramura` | turcoaz `#17a2b8` |
| `subteran` | roșu `#d62728` |

Dacă `clasa` lipsește sau are altă valoare: nod = gri `#7f7f7f`, linie = albastru `#1f5fbf` (nu crăpa).

Halou de stare, desenat în jurul simbolului (contur gros 3 px, semi-transparent, în spatele cercului; la linii, o linie mai lată dedesubt), din `properties`:
- verde `#2e7d32`: `nivel` = `in_model` ȘI (`ultima_verificare` e în ultimele 45 de zile față de data selectată pe timeline SAU `confirmat_de` = `om`);
- galben `#f9a825`: `nivel` = `in_model` fără verificare recentă (static, neatins);
- punctat (contur `dashed`, culoarea clasei, fără umplere plină): `nivel` = `predictie`;
- roșu `#c62828`: `nivel` = `de_verificat` (conflict / de verificat);
- `scos_din_uz`: gri deschis, cu transparență.
Halo-urile apar doar de la zoom 15 în sus (la zoom mic doar simbolurile, ca să nu aglomerezi 265 de noduri). Elementele cu `confirmat_de` = `om` primesc un mic marcaj „✓ om" în tooltip.

Predicțiile (`nivel` = `predictie`) se desenează cu linie PUNCTATĂ (`dashArray` „6 6") și opacitate redusă, indiferent de clasă. Dacă `properties.predictie.metoda` = `traseu_strada_osm`, linia urmează geometria străzii din feature (deja în GeoJSON), nu o linie dreaptă.

Legendă (colț hartă, pliabilă), cu două secțiuni:
1. „Tip element": casă (verde), nod important (gri), origine JT (portocaliu), post (pătrat negru), cablu aerian (albastru), ramură (turcoaz), subteran (roșu).
2. „Stare": verificat recent (halou verde), static (halou galben), predicție (punctat), de verificat/conflict (halou roșu).
Legenda se actualizează dacă modul de colorare e „scor" (arată scala continuă ca până acum).

### PARTEA 2 (C3): ecranul principal de rapoarte
În tab-ul „Proces raport" (sau ecranul principal de raport):

1. **4 butoane de sursă** (selectabile, unul activ): „Racordări" (`racordari`), „Investiții" (`investitii`), „Mentenanță" (`mentenanta`), „Apel telefonic de la client" (`apel_client`, subtitlu „text scris de operatorul call center").
2. Sub ele, un câmp de text mare (text liber, poate fi messy; placeholder în română) și butoane „Trimite raport" și „Generează exemplu".
3. **Generează exemplu:** `GET {API_BASE}/exemple?sursa=<sursa activă>`. Răspunsul e o listă de obiecte; ia câmpul `text` (dacă nu există, primul câmp șir). Alege un exemplu la întâmplare (altul la fiecare apăsare) și pune-l în câmp, editabil. Dacă lista e goală sau endpoint-ul dă eroare: mesaj discret „Fără exemple pentru această sursă".
4. **Trimite:** `POST {API_BASE}/rapoarte` cu `{"text": ..., "sursa": ...}`. Pe durata cererii, buton dezactivat. La succes: reîncarcă harta (`GET /retea`, data curentă/azi) și timeline-ul (`GET /evenimente`), centrează harta pe elementele atinse.
5. **Show pipeline:** buton care apare după un raport procesat și deschide un panou cu:
   - pașii din `pasi[]` în ordine (extracție, potrivire, predicție dacă există, scor): pentru fiecare `nume`, `rezultat` (cheile principale, lizibil, nu JSON brut), `incredere`; la potrivire arată `element_id` și `metoda`; la scor arată `scor_nou`, `nivel` și `motive`;
   - câmpurile lipsă din extracție (`campuri_lipsa`) marcate „lipsă", fără valori inventate;
   - **„Schimbări în rețea"**: tabel din `schimbari[]` cu coloanele `element_id` (clic = zoom pe hartă și deschide „De ce?"), `ce` (adaugat, actualizat, predictie, neaplicat, conflict, retras, scos_din_uz, de_verificat; badge colorat), `scor_inainte` → `scor_dupa`, `de_ce`. Dacă `schimbari` lipsește sau e goală: text „— (motorul nu a întors încă lista schimbărilor)", fără eroare. Opțional, ca rezervă, listează `modificari[]`.
6. **Data ultimei actualizări:** în bara de sus, text „Rețea actualizată la: <data>", luat din câmpul `ultima_actualizare` de la nivelul superior al răspunsului `GET /retea` (FeatureCollection; se schimbă cu data din timeline). Același câmp e și în `GET /health` și în răspunsul `POST /rapoarte`. Dacă câmpul lipsește: „Rețea actualizată la: —". Se reîmprospătează după fiecare raport.
7. **Traseu punctat pe străzi:** când raportul vizează un stâlp inexistent (potrivire `absent_din_model` sau element nou cu `nivel` = `predictie`), harta arată nodul nou și tronsonul propus ca linie punctată pe străzile din jur (geometria din `GET /retea`), cu tooltip: scor, „predicție neaplicată" și motivul. Zoom automat pe ele.

### Reguli generale
- Tot textul în română. Nu hardcoda URL-uri de API, tunel sau chei; doar `API_BASE`.
- Orice câmp opțional absent din răspuns => afișează „—", niciodată o eroare în consolă sau ecran alb.
- Nu adăuga autentificare, bază de date sau alte pagini în afară de cele descrise.
