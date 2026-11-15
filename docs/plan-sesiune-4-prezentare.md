# Plan sesiunea 4: prototip gata de prezentat (Victor B + Claudiu C, fără Patrick)

Stare: **propunere, de aprobat de Victor**. Până la aprobare nu se scrie cod.
Sursa: cererea lui Victor din 15 nov. + nota lui Claudiu („Modificări”) + 3 runde de întrebări (răspunsurile sunt în secțiunea 1).
Date: FICTIVE. Fără cheie API (AI = Haiku prin `ai_cli`, din abonament).

---

## 0. Pe scurt

Prototipul funcționează, dar arată prost la demo din patru motive măsurate pe `main` (15 nov.):

| Problemă | Cauză măsurată | Ce facem |
|---|---|---|
| Totul e galben, 50–70 % | rețeaua de start pornește la 0,90 și scade cu 0,05 la 30 de zile: la 15 nov., 620 din 630 de elemente sunt la 0,72 | GIS pornește la 0,95, scade cu 0,01 la 30 de zile, nu coboară sub 0,85 |
| Ce adaugă modelul iese verde fără coordonate | elementele noi au 0,96 indiferent cum au fost localizate | plafon de acuratețe după sursa locației (coordonate 0,85, adresă 0,70, stradă 0,55, analiză hartă 0,40) |
| Modelul „se blochează” | 8 din 29 de evenimente ies `neaplicat` | scară de localizare completă + predicție pe străzi; `neaplicat` doar fără niciun indiciu de loc sau în afara zonei |
| Rețeaua nu se schimbă vizibil în timp | 29 de evenimente, aproape toate „scor actualizat” | scenariu nou, ~55 de rapoarte text standardizate cu AI, care adaugă, scot, mută și verifică elemente |

Plus UI: pagină de intro, butoane pentru cele 3 echipe cu zoom și pop-up-uri, panou „Ce a înțeles AI-ul”, hartă tip GIS accesibilă, timeline orizontal derulabil. UI-ul se face **doar în Lovable**.

Se scot: scenariul extrem, traseul de ultima oră (buton și parametri; generarea din motor se oprește), plasarea prin clic, bannerul „DATE FICTIVE · rețea demonstrativă” de sus, etichetele de cod (`in_model`, „Predicție AI”, „generat de model”).

---

## 1. Decizii luate (15 nov.)

| # | Întrebare | Decizie |
|---|---|---|
| D1 | UI pentru demo | **Doar Lovable** (designul și interfața). Backend-ul livrează tot în API, ca UI-ul să doar afișeze. |
| D2 | Pagina de start | **Pagină separată de intro**, cu butonul „Intră în hartă”. |
| D3 | `in_model` | Rămâne în motor, **ascuns în UI**: se văd doar culoarea, linia plină/punctată și insignele „GIS”, „Din raport”, „Verificat de om”. |
| D4 | Analiza hărții | **Graful de străzi OSM local**: drumul cel mai scurt pe străzi, stâlpi la ~40 m, fără serviciu extern. |
| D5 | Culori | **4 benzi**: verde ≥ 0,80; galben 0,60–0,80; portocaliu 0,40–0,60; roșu < 0,40. |
| D6 | Acuratețe | GIS t0: 0,95, −0,01/30 zile, minim 0,85. Elemente din rapoarte: plafon după sursa locației. „Verificat de om” = 1,0. |
| D7 | Traseu | Butoanele și parametrii scoși din UI; generarea din motor **oprită** din `weights.yaml`; codul rămâne, nefolosit. |
| D8 | „din model” (nota lui Claudiu) | Dispare eticheta „generat de model”. Fiecare eveniment arată textul raportului și ce a extras AI-ul; elementele adăugate poartă „Din raport”. |
| D9 | Echipe | **Doar 3 butoane**: Mentenanță, Investiții, Racordări. Apelurile clienților rămân doar ca evenimente în timeline. |
| D10 | Verificat de om | Din panoul **oricărui** element: „Marchează verificat de om” → 1,0, insignă, intrare în timeline; se pierde doar dacă un raport ulterior îl contrazice. |

### Propuneri ale mele incluse în plan (confirmă sau schimbă)

- **P1. Două lucruri diferite: „există?” și „unde exact?”.** Azi același scor decide și dacă elementul intră în rețea, și culoarea. Cu plafoanele din D6, un stâlp nou raportat ca montat, dar cu adresă fără coordonate, n-ar intra niciodată (0,70 < pragul 0,75). Propun:
  - un raport de teren **executat** (lucrare finalizată, echipă de mentenanță sau investiții) adaugă elementul în rețea, linie plină, de la scorul 0,50 (`praguri.aplicat_raport_executat`);
  - culoarea arată acuratețea poziției (galben, portocaliu);
  - cererile și rapoartele neexecutate rămân predicții, linie punctată.

  Așa rețeaua iese „verde amestecat cu galben, portocaliu și ceva roșu”, cum cere Claudiu. Ideea vine din standardele de calitate a datelor GIS, care separă completitudinea (există) de acuratețea pozițională (unde).
- **P2. Rețeaua de la t0 e mixtă.** Claudiu scrie „majoritatea, dar nu toate” sunt puse de mână în GIS.
  - Elementele din KMZ (~527) = **GIS**, 0,95.
  - Cele 55 de puncte simulate SIM-* și 48 de tronsoane = **„Din raport” (rapoarte mai vechi)**, cu scoruri inițiale amestecate, deterministe: ~45 % galben, ~35 % portocaliu, ~20 % roșu.

  Harta de la t0 e deci deja realistă.
- **P3. „Nu se blochează” are o limită.** Dacă textul nu are niciun indiciu de loc (nici ID, nici coordonate, nici stradă, intersecție, reper sau cartier), nu inventăm un punct, conform principiului „nu inventa date lipsă”. Raportul intră în timeline cu „lipsă locație”, apare în lista „Fără locație” din UI și nu pe hartă. Orice alt raport produce ceva pe hartă, chiar și cu acuratețe mică.
- **P4. Buton „Resetează demo”.** `POST /demo/reset` + buton pe pagina de intro: după repetiții, modelul revine la starea de start fără repornirea serverului.
- **P5. Rezerve pentru ziua demo-ului.**
  - O înregistrare video de 3 minute a parcursului complet, ca rezervă dacă tunelul cade (alegerea D1 nu are plan-B actualizat).
  - Toate textele de demo pre-standardizate în cache, ca răspunsul să vină în sub o secundă.

---

## 2. Cine ce face

Patrick nu participă. Folderele lui trec temporar:

| Folder (al lui A) | Trece la | De ce |
|---|---|---|
| `backend/extract/` (prompt, `cli_ai`, `fill_cache`), `backend/geo/`, `backend/trace/`, `backend/racordare/`, `data/simulare/`, `data/golden/`, `data/cache/` | **Victor (B)** | sunt în lanțul logicii |
| `data/reports/` (textele rapoartelor, `exemple-dummy.json`) | **Claudiu (C)** | textele sunt conținut de demo, iar el le folosește în UI |

Rămân ale lor: B = motor (`backend/engine/`), `contracts/`, `data/model`, `data/network`, `data/events`, `scripts/`; C = `backend/api/`, `frontend/`, prompturile Lovable, banca de test.

**Laptopuri:** fiecare lucrează pe al lui, cu `git pull --rebase` la fiecare bloc, ca până acum. `claude auth login` (pentru `ai_cli`) trebuie făcut pe **ambele** laptopuri.

**Înghețarea logicii:** planul acesta, odată aprobat, ține loc de „cerere de logică aprobată” pentru `logic-v1`. La final Victor pune tag-ul `logic-v2`.

---

## 3. Faze și dependențe

```
Faza 0 (B, ~1 h)          contract sesiunea 4 + OpenSpec + CLAUDE.md
        │
        ├── Faza 1B (B, ~5-6 h)   acuratețe, origine t0, analiză hartă, mutare fire, verificat om, curățenie motor
        └── Faza 1C (C, ~4-5 h)   curățenie API + endpointuri noi, texte noi, scenariul de timeline
                 │
Faza 2 (B+C, ~2 h)        scenariu ~55 evenimente: texte (C) → standardizare Haiku + cache (B) → events.json → calibrare distribuție
        │
Faza 3 (C, ~3 h + credite) 3 prompturi Lovable, trimise pe rând DOAR după decizia lui Victor, verificate prin tunel
        │
Faza 4 (B+C, ~1,5 h)      repetiție completă, golden, `verifica_tot.sh`, tag `logic-v2`, video de rezervă
```

Faza 1C începe imediat după contract (Faza 0): API-ul poate expune câmpurile noi cu valori din motor sau „—”, ca la sesiunea 3.

---

## 4. Faza 0 (Victor): contractul sesiunii 4

Un singur commit `contract:`, cu `contracts/interfaces.md` actualizat și intrare în `board/Victor.md`.

### 4.1 `contracts/weights.yaml` (chei noi sau schimbate)
```yaml
scor:
  initial_retea_start: 0.95            # era 0.90
  scadere_retea_start_per_30_zile: -0.01
  minim_retea_start: 0.85              # scăderea în timp nu coboară GIS sub asta (contradicțiile pot)
  scadere_per_30_zile: -0.05           # rămâne pentru elementele din rapoarte
retea_start:
  sim_din_rapoarte: true               # P2: SIM-* = origine raport, scor inițial din lista de mai jos
  scoruri_initiale_sim: [0.74, 0.66, 0.55, 0.47, 0.36]   # alese determinist pe ID
plafon_locatie:                        # D6: acuratețea maximă a unui element din raport, după cum a fost localizat
  coordonate: 0.85
  id: 0.85
  adresa_numar: 0.70
  intersectie: 0.60
  strada: 0.55
  analiza_harta: 0.40
  reper: 0.35
praguri:
  aplicat: 0.75
  aplicat_raport_executat: 0.50        # P1
  predictie: 0.40
culori:                                # D5, folosit de API ca să trimită `banda`; UI-ul nu recalculează
  verde: 0.80
  galben: 0.60
  portocaliu: 0.40
verificat_om:                          # D10
  scor: 1.0
  scadere_per_30_zile: -0.01
  minim: 0.95
analiza_harta:                         # D4
  raza_cautare_m: 800                  # stâlpi existenți luați în calcul ca punct de plecare
  candidati: 5                         # câte drumuri alternative se calculează
  pas_stalp_m: 40
  reutilizare_stalp_m: 10              # dacă drumul trece la <10 m de un stâlp existent, îl folosește
  max_bransament_m: 40                 # ultima porțiune, de la stradă la casă, poate fi dreaptă
  lungime_referinta_m: 400             # acuratețea scade cu lungimea drumului: f = max(factor_min, exp(-L/400))
  factor_min: 0.30
  fara_drum: 0.25                      # rețeaua de străzi nu leagă punctele: linie dreaptă, marcată, roșu
mutare_fire:
  raza_m: 60                           # era 40; intersecție cu sens giratoriu
  ocolire: true                        # traseul nou ocolește centrul pe străzi
trace_generat:
  activ: false                         # D7
```
Limitele noi intră în `contracts/weights.limits.yaml`, iar `verifica_reglaje` le verifică.

### 4.2 `contracts/state.schema.json` (aditiv)
- `verificat_om` (bool), `verificat_om_data` (dată).
- `banda`: `verde` | `galben` | `portocaliu` | `rosu`.
- `sursa_locatie`: `gis` | `coordonate` | `id` | `adresa_numar` | `intersectie` | `strada` | `analiza_harta` | `reper`.
- `predictie.traseu`: lista de puncte a drumului pe străzi; `predictie.analiza_harta` (rezumatul de mai jos).
- `origine` rămâne `retea_start` | `generat_model` (valorile interne nu se schimbă; UI-ul afișează „GIS” / „Din raport”). SIM-* primesc `generat_model` + `t0: true`.

### 4.3 `contracts/event.schema.json` (aditiv)
- `mutare_fire.detalii`: `intersectie {strada_1, strada_2}`, `motiv`, `strada_noua` (opțional), `latura` (opțional: nord/sud/est/vest).
- Tip nou `verificare_om` (sursa `om_teren`, `tinta_id`, `motiv`).

### 4.4 `contracts/api.openapi.yaml`
- **Scoase:** `?scenariu=extrem` (la `/retea`, `/evenimente`), `GET /trasee-demo`, `trace_params` și `trace` din `POST /rapoarte`. `locatie` (clic) rămâne acceptat de API pentru teste, dar e marcat „neutilizat în UI”.
- **Noi:**
  - `POST /element/{id}/verificare` `{motiv?, data?}` → StepTrace.
  - `GET /demo/exemple` (cardurile paginii de intro).
  - `POST /demo/reset` (P4).
  - `GET /legenda` (benzi, stiluri, insigne, din `weights.culori`).
- **Câmpuri noi în răspunsuri:**
  - `POST /rapoarte`: `standardizare` (vezi 6.3) și `focus {lat, lon, zoom, bbox}`.
  - `GET /retea`: `banda`, `verificat_om` și `sursa_locatie` pe fiecare feature.
  - `GET /evenimente`: `text_original`, `standardizare`, `banda_inainte`, `banda_dupa`, `focus`.

### 4.5 OpenSpec (5 schimbări, create în același bloc)

| Schimbare | Proprietar | Conține |
|---|---|---|
| `acuratete-realista` | B | D5, D6, D10, P1, P2 |
| `predictie-pe-strazi` | B | D4, P3, mutare fire din document |
| `simplificare-demo` | B + C | D3, D7, D8, D9, scos scenariul extrem, clicul și bannerul |
| `scenariu-timeline-realist` | B + C | ~55 de evenimente, texte, cache, distribuția culorilor |
| `ui-prezentare-gis` | C | intro, butoane echipe, standardizare, hartă GIS, timeline orizontal, accesibilitate |

`mutare-fire-sens-giratoriu` și `verificare-om-predictii` (sesiunea 2) sunt extinse de acestea; se arhivează împreună la final.

**Și:** CLAUDE.md primește secțiunea „Sesiunea 4” (rezumatul planului, preluarea folderelor lui A, regulile noi), iar `.claude/agents/victor.md` și `claudiu.md` primesc sarcinile.

---

## 5. Faza 1B (Victor): motor

Fiecare sarcină are test în `backend/engine/smoke_sesiune4.py` (nou) și doc. Ordinea contează: V1 și V2 schimbă scorurile pe care le folosesc celelalte.

### V1. Modelul de acuratețe (`model.py`, `scoring.py`)
1. Scor inițial GIS 0,95. Scăderea în timp e separată pe origine: GIS −0,01/30 zile cu minim 0,85; „Din raport” −0,05/30 zile; „verificat de om” −0,01/30 zile cu minim 0,95.
2. `plafon_locatie`: orice element creat sau mutat dintr-un raport are scorul ≤ plafonul sursei locației. Sursa e cea mai bună dintre cele folosite (coordonate > id > adresă cu număr > intersecție > stradă > analiză hartă > reper). Un raport ulterior care confirmă elementul **cu o sursă mai bună** ridică plafonul (ex. echipa trimite coordonatele GPS ale stâlpului → plafon 0,85, deci poate ajunge verde).
3. P1: decizia „aplicat” pentru rapoarte executate de teren (mentenanță, investiții, cu `status: executat`) folosește 0,50; restul folosesc 0,75.
4. `banda` calculată în motor din `weights.culori`, scrisă în snapshot și în jurnal (înainte/după).
5. `sursa_locatie` pe fiecare element.

**Test:** stâlp nou executat cu adresă → aplicat, 0,70, galben, linie plină; aceeași cerere neexecutată → predicție; stâlp GIS neatins la 15 nov. ≥ 0,92; după un raport cu coordonate GPS, stâlpul cu adresă ajunge ≥ 0,80.

### V2. Rețeaua de start mixtă (P2; `network.py`, `model.py`)
- KMZ = `retea_start`; SIM-* = `generat_model` cu `t0: true`, scor ales determinist din `scoruri_initiale_sim` (hash pe ID), `sursa_locatie: adresa_numar` sau `strada`.
- Centrul zonei de 3 km se calculează ca acum, din toate nodurile de start.

**Test:** la 1 aug., KMZ 100 % verde; SIM-* distribuite între galben, portocaliu și roșu, fără verde; ID-urile și numărul de elemente neschimbate.

### V3. Analiza hărții: predicție pe străzi (D4; modul nou `backend/engine/analiza_harta.py`)
Funcția publică `traseu_pe_strazi(tinta, net, cfg, evita=None) -> dict`:
1. **Ținta pe stradă:** proiectează punctul țintă pe cel mai apropiat segment de stradă OSM (distanța = `bransament_m`). Peste `max_bransament_m`, scade acuratețea (casa e departe de stradă).
2. **Puncte de plecare:** primii `candidati` stâlpi existenți (orice origine, în afară de predicții) din `raza_cautare_m`, sortați după distanța în linie dreaptă, apoi proiectați pe stradă.
3. **Drumuri:** pentru fiecare, cel mai scurt drum pe graful de străzi (`osm.traseu`, extins să accepte muchii de evitat pentru mutare fire). Se alege drumul cel mai scurt; celelalte rămân ca alternative, cu motivul („mai lung cu 180 m”, „nu există legătură pe străzi”).
4. **Stâlpi:** la fiecare `pas_stalp_m` de-a lungul drumului. Dacă drumul trece la < `reutilizare_stalp_m` de un stâlp existent, îl folosește în loc de unul nou. Fiecare stâlp nou respectă distanța minimă de 2,5 m față de nodurile existente și e tăiat dacă iese din zona de 3 km.
5. **Acuratețe:** `plafon_locatie[sursa ținta]` × `max(factor_min, exp(−L/lungime_referinta_m))`, plafonat la `analiza_harta` (0,40) pentru stâlpii intermediari. Fără drum pe străzi: linie dreaptă, scor `fara_drum` (roșu), cu explicația „nu există drum pe străzi; linie dreaptă, de verificat”.
6. **Ieșire** (în `pasi` ca pas nou `analiza_harta`, ca UI-ul să o deseneze):
   ```json
   {"tinta": {...}, "bransament_m": 18, "ales": {"de_la": "7101969", "lungime_m": 260, "strazi": ["Strada Viilor", "Strada Teiului"], "stalpi_noi": 6, "stalpi_reutilizati": 1, "traseu": [[lat, lon], ...]},
    "alternative": [{"de_la": "SIM-014", "lungime_m": 440, "motiv": "mai lung cu 180 m", "traseu": [...]}],
    "acuratete": 0.38, "explicatie": ["Am găsit 4 stâlpi în 800 m.", "Drumul pe Strada Viilor și Strada Teiului e cel mai scurt (260 m).", "Am pus 6 stâlpi la 40 m; am refolosit stâlpul SIM-022."]}
   ```
**Unde se folosește:**
- **Racordare:** înlocuiește treptele 3 și 4 (linie dreaptă, doar casa). Ordinea nouă: raza normală → raza extinsă → analiza hărții → fără drum.
- **Nod lipsă departe de rețea:** nod nou la > 80 m de orice tronson → legătură prezisă pe străzi.
- **Mutare fire:** V4.

**Test:**
- o casă la ~300 m de rețea → traseul urmează străzile (fiecare punct la ≤ 15 m de o stradă OSM), nu linia dreaptă; scorul scade cu lungimea;
- un stâlp existent pe drum este refolosit;
- un punct fără legătură pe străzi → `fara_drum`, roșu;
- determinist (două rulări dau același rezultat).

### V4. Mutare fire din document (`sesiune2.py` → `_mutare_fire`; promptul din `backend/extract/extract.py`)
Intrare: doar text, fără clic. Exemplu (devine exemplul implicit de pe pagina de intro):
> „Ca urmare a construirii sensului giratoriu de la intersecția Șoseaua Principală cu Strada Liviu Rebreanu, rețeaua aeriană JT a fost mutată pe Strada Crinului. Lucrare finalizată 10.10.2026.”

(Intersecția și Strada Crinului există în cache-ul OSM local; Crinului se intersectează cu Liviu Rebreanu. V4 verifică pe hartă că ocolirea are sens înainte ca textul să devină exemplul de pe pagina de intro.)

1. **Prompt (Haiku):** extrage `tip: mutare_fire`, `detalii.intersectie {strada_1, strada_2}`, `motiv`, `strada_noua`, `latura`, `status`. Exemple noi în prompt; cache regenerat pentru texte.
2. **Geocodare:** intersecția prin `backend.geo` (acuratețe `intersectie` 0,60); dacă lipsește, se folosește strada.
3. **Zona afectată:** tronsoanele și nodurile la ≤ `raza_m` de centru devin `de_verificat`, scor ≤ 0,35 (roșu/portocaliu). Motiv: „Fire mutate: <motiv>”.
4. **Traseul nou prezis:** pentru fiecare tronson tăiat, capetele din afara zonei se leagă prin `traseu_pe_strazi(..., evita=zona)`, adică pe străzi care ocolesc intersecția. Dacă textul numește `strada_noua`, drumurile pe ea sunt preferate (cost redus). Rezultat: tronsoane prezise, punctate, plafon `intersectie` × factor de lungime (portocaliu sau galben). Dacă `status: executat` (P1), traseul nou e aplicat, iar cel vechi trece pe „demontat probabil” (punctat gri), nu e șters.
5. **Jurnal și „De ce?”:** ce s-a extras, centrul, raza, ce s-a marcat, drumul ales și alternativele.

**Test:** textul de mai sus → zonă cu ≥ 1 tronson marcat, traseu nou pe străzi care nu trece prin centrul zonei, preferă Strada Crinului; fără `strada_noua` tot iese un traseu; intersecție negăsită → stradă; fără nicio stradă → P3.

### V5. Verificat de om (D10; `model.py` `_decizie_om` + eveniment `verificare_om`)
- `verificare_om` pe orice element → scor 1,0, `verificat_om: true`, `verificat_om_data`, `confirmat_de: om`, intrare în jurnal „Verificat de om în teren”.
- Pe o predicție (stâlp prezis, traseu): o și aplică (linie plină).
- Un raport ulterior care contrazice elementul: `verificat_om` devine false, scorul revine la calculul normal plus contradicția, iar jurnalul notează „verificarea din <data> a fost contrazisă”.
- `aplica_decizie` existent (Acceptă/Respinge pe predicții) rămâne; „Acceptă” se comportă de acum ca `verificare_om`.

**Test:** stâlp galben → 1,0 verde cu insignă; contradicție ulterioară → pierde insigna; scădere în timp ≥ 0,95.

### V6. „Nu se blochează” (P3; `match.py`, `sesiune2.py`, `model.py`)
Scara de localizare pentru orice tip de raport:
1. ID → 2. coordonate din text → 3. adresă cu număr → 4. intersecție → 5. stradă → 6. reper sau cartier (geocodare) → 7. analiză hartă pornind de la elementul sau vecinii numiți → 8. fără locație.

- La 2–7 iese mereu un rezultat: aplicat (P1), predicție sau, cel puțin, „de verificat” cu punct și scor mic.
- `neaplicat` rămâne doar pentru treapta 8 și în afara zonei (eronat în prototip).

**Test:** cele 8 evenimente `neaplicat` de azi se reclasifică; în golden, `g-07`/`g-08` (geocodare necunoscută) → „de verificat” cu stradă, nu `neaplicat`.

### V7. Curățenie în motor (D7 + scenariul extrem)
- `trace_generat.activ: false`: `_trace_generat` nu mai rulează. Codul și testele lui rămân, rulate explicit cu `activ: true`.
- Scos `model_scenariu`, `EXTREME`, `data/events/events.extreme.json` (mutat în `data/events/arhiva/`, nu șters), testele extreme.
- `timeline()` nu mai trimite `eronat_prototip` pe fiecare intrare dacă e false (aditiv: UI-ul îl tratează ca absent).

### V8. Documentație B
`docs/etapa-26-acuratete-realista.md`, `etapa-27-analiza-harta.md`, `etapa-28-mutare-fire-document.md`, `etapa-29-verificat-om.md`. Actualizate: `backend/engine/README.md`, `docs/calibrare.md` (distribuția nouă), `contracts/interfaces.md`.

---

## 6. Faza 1C (Claudiu): API, texte, bancă

### C1. Curățenie API (`backend/api/`)
- Scos `?scenariu=extrem`, `/trasee-demo`, `trace_params`, `trace`, `sources.py` pentru extrem. `smoke_api.py` actualizat.
- `GET /exemple?sursa=` acceptă doar `mentenanta`, `investitii`, `racordari` (D9).
- `NOTA` din `/health` rămâne (nu e afișată în UI).

### C2. Endpointuri noi
- `POST /element/{id}/verificare` → `engine.apply_event` cu `verificare_om` (V5); 404 dacă elementul nu există.
- `GET /demo/exemple` → 4 carduri, din `data/reports/demo-intro.json` (nou, C):
  `{id, titlu, descriere, sursa, text, data_moment, focus}`. Conținut: (1) sens giratoriu, fire mutate (V4); (2) racordare casă departe, traseu pe străzi (V3); (3) stâlp înlocuit raportat cu adresă, aplicat galben, apoi confirmat cu GPS și devenit verde (V1); (4) element verificat de om (V5).
- `POST /demo/reset` → `engine.reset()` + reîncărcarea scenariului.
- `GET /legenda` → benzi (prag, culoare, text), stiluri de linie (plină = în rețea, punctată = predicție, gri punctat = demontat probabil), insigne.

### C3. Câmpuri noi în răspunsuri
- `focus`: bbox-ul elementelor din `schimbari` (adăugat, mutat, marcat, predicție), lărgit cu 30 m; dacă nu există, punctul localizat; zoom 17 (16 pentru zone de mutare fire).
- `standardizare` (din `pasi`, pentru panoul „Ce a înțeles AI-ul”):
  ```json
  {"metoda": "ai_cache | ai_cli | regex",
   "campuri": [{"camp": "tip", "valoare": "nod_lipsa", "eticheta": "Tip eveniment", "din": "text"},
               {"camp": "adresa", "valoare": "Strada Viilor 12", "din": "text"},
               {"camp": "coordonate", "valoare": null, "din": "lipsa"}],
   "lipsa": ["coordonate", "vecini"],
   "localizare": {"sursa": "adresa_numar", "precizie_m": 200, "plafon": 0.70, "text": "Adresă cu număr, geocodată din străzile OSM locale"},
   "decizie": {"cod": "aplicat", "text": "Adăugat în rețea", "scor": 0.66, "banda": "galben"}}
  ```
  Etichetele și textele în română sunt făcute în API, nu în Lovable.
- `GET /retea`: `banda`, `verificat_om`, `sursa_locatie`, `eticheta_origine` („GIS” / „Din raport”) pe fiecare feature.
- `GET /evenimente`: `text_original`, `standardizare`, `banda_inainte`, `banda_dupa`, `focus`, `echipa` (eticheta română).

### C4. Texte pentru demo (`data/reports/`, Haiku pentru generare, revizuite de om)
- **Scenariul timeline** (faza 2): ~55 de rapoarte între 1 aug. și 14 nov., după rețeta din 7.1. Fiecare fișier `.txt` are datele în nume, ca acum.
- **Butoanele echipelor:** 5 texte pe echipă în `exemple-dummy.json`, cu nivel variat de standardizare (coordonate, adresă, doar stradă, intersecție, reper). Fiecare produce o schimbare vizibilă pe hartă.
- Toate cu străzi care există în cache-ul OSM local și în zona de 3 km (verificat cu `GET /geocodeaza`). Cache-ul are **doar 24 de străzi** (ex. Strada Viilor, Șoseaua Principală, Strada Liviu Rebreanu, Strada Bălții, Strada Crinului, Strada Regina Maria); lista completă: `osm.strazi()`. Un nume în afara listei iese „necunoscut” la geocodare.

### C5. Banca de test (`banc_logica`)
- Coloane noi: `banda`, `sursa_locatie`, `verificat_om`, `analiza_harta.lungime_m`.
- Golden nou (cu Victor, `data/golden/`): 3 cazuri de analiză hartă, 3 de mutare fire din document, 2 de verificat de om, 4 de „nu se blochează”.

### C6. Documentație C
`docs/etapa-30-api-sesiune4.md`, `frontend/README.md`, `docs/demo-checklist-C.md`.

---

## 7. Faza 2 (B + C): scenariul timeline realist

### 7.1 Rețeta (~55 de evenimente, 1 aug. → 14 nov.)

| Fel | Nr. | Efect vizibil |
|---|---|---|
| Mentenanță, verificare de rutină cu ID (confirmă) | 10 | elemente din rapoarte urcă (portocaliu → galben → verde cu GPS) |
| Mentenanță, stâlp înlocuit sau nod lipsă, cu adresă | 6 | element nou, linie plină, galben/portocaliu |
| Mentenanță, defect (avarie) | 5 | scor scade, unele trec în roșu |
| Investiții, linie nouă executată | 4 | tronsoane noi pe străzi, galben |
| Investiții, linie planificată | 3 | predicții punctate |
| Investiții, demontare | 4 | elemente scoase (gri punctat, apoi dispar) |
| Racordări, cereri (mix adresă/stradă/departe) | 8 | lanțuri prezise pe străzi, portocaliu/roșu |
| Racordări, executate | 4 | lanțuri prezise devin aplicate |
| Mutare fire (sens giratoriu + încă unul) | 2 | zonă roșie + traseu nou |
| Apeluri clienți (o rafală de 3 în aceeași zonă) | 5 | val de apeluri → zonă de verificat |
| Verificat de om | 4 | elemente → 1,0 verde cu insignă |

### 7.2 Ținta de distribuție la 15 nov.
Verde 70–82 %, galben 8–15 %, portocaliu 5–10 %, roșu 2–6 %. La 1 aug.: verde ~84 % (KMZ), restul SIM-* mixte.

`verifica_reglaje` primește verificarea de distribuție. Dacă ținta nu iese, se reglează **valori** (`reglaj:`), nu cod.

### 7.3 Pași
1. Claudiu scrie textele (C4) și le comite.
2. Victor rulează `fill_cache --lipsa` cu `ai_cli` (Haiku) și verifică extracțiile (tip, stradă, status).
3. Victor generează `data/events/events.json` din `data/reports/*.txt` + cache (script nou `scripts/genereaza_scenariu.py`, determinist).
4. Calibrarea și distribuția (7.2), referința de aur reîmprospătată (`--scrie-referinta`).
5. `scripts/verifica_tot.sh` verde.

---

## 8. Faza 3 (Claudiu): UI în Lovable

Trei prompturi, scrise în `frontend/lovable-prompt-sesiune4-P1.md`, `-P2.md`, `-P3.md`. Fiecare e **netrimis până decide Victor**, trimis doar după ce API-ul are câmpurile și e verificat prin tunel, cu checklist după fiecare. Buget estimat: 15–20 de credite. Regula de prompt rămâne: „NU SCHIMBA” + câmpuri exacte + „—” pentru orice lipsă.

### P1. Curățenie + hartă tip GIS + culori + panoul elementului
**Scos:**
- bannerul „DATE FICTIVE · rețea demonstrativă” de sus;
- comutatorul și orice mențiune a scenariului extrem;
- butoanele „Generează traseu ultima oră”, „Cerere racordare casă” (clic) și „Fire mutate” (clic), modul clic pe hartă, câmpurile de parametri trace;
- etichetele „in_model”, „Predicție AI”, „generat de model” și codurile brute (`predictie`, `de_verificat`).

**Aspect GIS:**
- Stânga: panoul „Straturi” cu bife:
  - Rețea GIS;
  - Din rapoarte;
  - Predicții;
  - Elemente de verificat;
  - Zona prototipului (cercul de 3 km);
  - Străzi (fundal OSM standard / gri deschis).

  Sub el, legenda din `GET /legenda`.
- Sus: bara de unelte cu căutare (ID element sau stradă), „Încadrează rețeaua”, cele 3 butoane de echipă (P2) și „Pagina de start”.
- Dreapta: panoul „Identificare” (ca în GIS): tabel cu atribute (ID, tip, sursă „GIS”/„Din raport”, acuratețe cu bara colorată și textul benzii, cum a fost localizat, ultima verificare, „Verificat de om” cu dată), „De ce?” (istoric) și butonul „Marchează verificat de om” (→ `POST /element/{id}/verificare`, apoi reîncărcare).
- Jos: scara grafică, coordonatele cursorului și timeline-ul (P3).

**Culori din `banda`** (UI-ul nu recalculează pragurile):
- benzile: verde, galben, portocaliu, roșu;
- linie plină = în rețea, punctată = predicție, gri punctat = demontat probabil;
- insignă ✓ pentru verificat de om.

**Accesibilitate** (WCAG 2.1 AA):
- culoarea nu e singurul semnal: textul benzii apare în tooltip și în Identificare, iar predicțiile au și stil de linie;
- contrast ≥ 4,5:1 pe text;
- navigare completă din tastatură (Tab, Enter, Esc închide panourile), focus vizibil;
- `aria-label` pe butoanele cu iconițe;
- text ≥ 14 px;
- `prefers-reduced-motion` oprește animațiile de zbor/pulsare;
- ținte de clic ≥ 32 px.

### P2. Pagina de intro + butoanele echipelor + „Ce a înțeles AI-ul”
**Pagina de intro (ruta `/`, D2):**
- titlu și o frază despre ce face prototipul;
- 3 carduri „Cum funcționează”:
  1. Standardizare cu AI (textul devine date);
  2. Modelul își actualizează rețeaua (scor, culori);
  3. Predicție pe hartă (pe străzi, cu acuratețe);
- 4 carduri „Exemple” din `GET /demo/exemple`, fiecare cu „Vezi pe hartă”: deschide harta la `data_moment`, zboară la `focus`, deschide pop-up-ul și panoul „Ce a înțeles AI-ul” pentru acel eveniment;
- butoane „Intră în hartă” și „Resetează demo” (`POST /demo/reset`, cu confirmare);
- o singură linie mică în subsol: „Date fictive, rețea demonstrativă.” Opțional, pentru că „scoate de tot” se referă la banner-ul de pe hartă.

**Butoanele echipelor (pe hartă, D9):** Mentenanță, Investiții, Racordări.
- **Clic:** se deschide un panou cu lista de texte (`GET /exemple?sursa=`), „Alt exemplu”, textul editabil și „Trimite raportul”.
- **După trimitere**, secvența animată:
  1. panoul „Ce a înțeles AI-ul” se completează pas cu pas din `standardizare`:
     - câmpurile cu valoare și sursă (din text / dedus / lipsă, cu culori diferite);
     - „Cum am localizat” cu plafonul;
     - decizia;
  2. harta zboară la `focus` (~1,2 s);
  3. elementele atinse pulsează de 3 ori;
  4. apar pop-up-uri ancorate pe hartă (maxim 3), câte unul pe schimbare. Ex.: „Stâlp nou adăugat, acuratețe 0,66 (galben), localizat din adresă”, „Traseu prezis pe Strada Viilor, 260 m, acuratețe 0,38”;
  5. timeline-ul sare la prezent, cu noul punct evidențiat.
- **În timpul cererii:** indicator de progres în 3 pași (Standardizare AI → Potrivire în rețea → Decizie). Textele demo sunt în cache, deci instant; un text nou poate dura 5–20 s cu `ai_cli`.

### P3. Timeline orizontal + vizualizarea analizei hărții
**Timeline jos, orizontal:**
- bara cu puncte pe axa timpului (1 aug. → azi), derulabilă orizontal (roată, trackpad, săgeți);
- puncte colorate după efect (adăugat, scos, mutat, scor ↑, scor ↓, verificat om), cu repere de lună;
- **implicit și după orice raport nou: poziția „acum”, cea mai din dreapta**;
- selectarea unui punct (clic sau săgeți): harta trece la acea dată, zboară la `focus` și se deschide o fișă deasupra barei cu:
  - data, echipa, textul raportului (scurtat, „mai mult”), ce a extras AI-ul (3–4 câmpuri);
  - decizia, scor și bandă înainte → după;
  - „De ce?”;
- butonul „Listă” deschide toate evenimentele ca listă verticală (înlocuiește panoul vertical actual).

**Vizualizarea analizei hărții** (când răspunsul sau evenimentul are pasul `analiza_harta`):
- drumul ales ca linie groasă punctată, colorată după bandă;
- alternativele ca linii subțiri gri, cu eticheta motivului;
- stâlpii noi ca puncte, cei refolosiți cu contur;
- branșamentul ca segment scurt;
- fișa „Analiza hărții” cu `explicatie` (3 rânduri) și lungimea.

Pentru mutare fire: cercul zonei, tronsoanele marcate roșu și traseul nou.

---

## 9. Faza 4: repetiție și închidere

1. `scripts/verifica_tot.sh` verde (smoke engine, sesiune2, sesiune4, match, API, `verifica_reglaje` cu distribuția, banca pe golden).
2. Parcursul de demo (scris în `docs/DEMO.md`, secțiunea „Sesiunea 4”), cronometrat sub 5 minute:
   1. intro;
   2. exemplul sens giratoriu;
   3. harta GIS, straturi, Identificare;
   4. butonul Mentenanță cu un text cu adresă (galben);
   5. butonul Racordări cu o casă departe (traseu pe străzi);
   6. „Marchează verificat de om” → verde 1,0;
   7. derulare în timeline înapoi la 1 aug. și înainte la prezent;
   8. „Resetează demo”.
3. Video de rezervă (P5).
4. Tag `logic-v2` (Victor), arhivarea schimbărilor OpenSpec ale sesiunilor 2–4 cu `/openspec-archive-change` (Victor decide).
5. Publicarea Lovable doar cu confirmarea lui Victor.

---

## 10. Lipsuri pe care le văd și cum le acoperă planul

| Lipsă | Risc | Acoperire |
|---|---|---|
| Tunelul HTTPS se schimbă la repornire | demo-ul nu încarcă datele | `demo_start.sh` + `?api=` în link; video de rezervă (P5); test cu 1 oră înainte |
| Extracție live lentă (5–20 s) | pauză stânjenitoare | texte demo în cache; indicator de progres; un singur text „live” la final, opțional |
| Doar 24 de străzi în cache-ul OSM local | texte cu străzi inexistente ies „necunoscut”, analiza hărții are puține drumuri | textele folosesc doar lista din `osm.strazi()`; extinderea cache-ului OSM e opțională, în afara planului |
| Graful de străzi OSM poate avea străzi nelegate | analiza hărții nu găsește drum | `fara_drum` explicit (roșu, „de verificat”), test dedicat |
| Pragurile de culoare calculate diferit în API și UI | culori inconsistente | `banda` vine din motor; UI-ul doar o afișează |
| Scenariul nou schimbă calibrarea | golden și referința pică | referința reîmprospătată în faza 2; golden actualizat cu Claudiu (C5) |
| Lovable nu e accesibil de pe contul lui Victor | nu putem citi sau repara codul UI | prompturile sunt foarte exacte; Claudiu verifică fiecare prin tunel cu checklist; capturi de ecran pe `board/` |
| Credite Lovable | iterații nelimitate costă | 3 prompturi grupate, ~15–20 credite; corecturi doar grupate |
| Ce e AI și ce e model | confuzie la juriu | AI apare doar la „Ce a înțeles AI-ul” (standardizare); restul e „modelul” (scor, predicție pe străzi) |
| Fișierele vechi (scenariul extrem, trasee) | cod mort care încurcă agenții | mutate în `arhiva/`, scoase din API și UI, notate în docs |

## 11. Ce NU facem acum
- Nu folosim imagini de hartă sau servicii externe (D4); nu există cheie API.
- Nu schimbăm valorile interne `origine` / `nivel` (doar afișarea).
- Nu facem plasare prin clic (cererea lui Claudiu).
- Nu păstrăm plan-B la zi (D1); rămâne în repo ca atare.

## 12. Verificare (comenzi)
```bash
scripts/verifica_tot.sh                                  # TOT VERDE
.venv/bin/python -m backend.engine.smoke_sesiune4        # sarcinile V1–V7
.venv/bin/python -m backend.engine.verifica_reglaje      # include distribuția culorilor (7.2)
.venv/bin/python -m backend.api.banc_logica --doar-diferente   # golden sesiunea 4
```
