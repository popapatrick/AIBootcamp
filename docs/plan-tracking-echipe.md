# Plan: tracking echipe (simulare GPS din tabletă)

Stare: **aprobat de Victor (15 nov.)**, de implementat de Victor (B) și Claudiu (C). Date FICTIVE. Fără cheie API, fără serviciu extern.

## 0. Ce vrem, pe scurt

O funcție **independentă** de rapoarte, în care o echipă își face tura cu o tabletă care trimite poziția GPS:
- unde tableta **stă câteva minute lângă un stâlp existent**, stâlpul e **confirmat**: acuratețea lui crește;
- unde tableta **stă mult într-un loc fără stâlp**, sistemul **presupune un stâlp nou**, afișat ca predicție punctată;
- totul se vede **dinamic**: tableta se mișcă pe hartă, opririle cresc, apar pop-up-uri cu „înainte → după”, iar tura intră în timeline.

Traseele sunt **simulate** (nu avem tablete reale): generate pe străzile OSM locale, deterministe, ca demo-ul să fie repetabil.

Diferența față de „traseul de ultima oră”, scos în sesiunea 4: acela era un semnal ascuns, atașat fiecărui raport. Tracking-ul e o funcție separată, vizibilă, cu tab-ul ei.

## 1. Decizii (Victor, 15 nov.)

| # | Întrebare | Decizie |
|---|---|---|
| T1 | Unde în UI | **Tab separat „Tracking echipe”** pe aceeași hartă GIS, cu panoul lui. Nu se amestecă cu butoanele de rapoarte. |
| T2 | Ce face o oprire | **Validează și propune**: oprire lângă un stâlp existent = stâlp confirmat; oprire lungă fără stâlp = stâlp nou presupus (predicție). |
| T3 | Trasee | **Generate pe străzi, la cerere**, deterministe pe o „sămânță” (seed). |
| T4 | Istoric | **Da, eveniment în timeline**, tip `tracking_tura`, cu sursă proprie (fiabilitate mai mică decât un raport) și „De ce?” pe fiecare stâlp. |

Principiile rămân: același calcul de scor pentru orice input; nu inventăm date (un stâlp presupus e doar predicție); fiecare schimbare are jurnal și „de ce”; nimic în afara zonei de 3 km.

## 2. Cum funcționează (logica)

### 2.1 Generarea turei (simulare)
`genereaza_tura(echipa, seed, data)`:
1. Alege **3–5 stâlpi existenți** din zonă, preferând stâlpi care nu sunt verzi (galben/portocaliu), ca validarea să se vadă. Determinist pe `seed`.
2. Alege **un loc fără stâlp** pe o stradă OSM, la cel puțin `tracking.raza_fara_stalp_m` de orice stâlp.
3. Ordonează punctele (cel mai apropiat următor) și leagă-le **pe străzi** (`osm.traseu` / `analiza_harta`), nu în linie dreaptă.
4. Mers cu `tracking.viteza_m_s`, câte un punct GPS la `tracking.pas_s` secunde, cu zgomot `tracking.zgomot_m`.
5. Opriri: la fiecare stâlp ales, 6–10 min, la 3–8 m de el; la locul fără stâlp, 15 min. Plus 1–2 opriri scurte (1–2 min, semafor), care trebuie ignorate.
6. Ieșire: `{tura_id, echipa, data, seed, puncte: [{t, lat, lon}], plan: [{lat, lon, durata_min, tip_plan: stalp|fara_stalp|scurta, element_id?}], lungime_m, durata_min}`. `plan` e doar pentru depanare și teste; motorul NU îl folosește, el detectează singur opririle din puncte.

### 2.2 Aplicarea turei în model (eveniment `tracking_tura`)
1. Opririle se detectează din puncte cu `backend.trace.gaseste_opriri` (rază `trace.raza_oprire_m`, durată minimă `trace.durata_min_min`).
2. Pentru fiecare oprire:

| Situație | Rezultat |
|---|---|
| durată < `tracking.durata_validare_min` | ignorată („oprire scurtă”) |
| stâlp existent la ≤ `tracking.raza_validare_m` și durată ≥ `durata_validare_min` | **validare**: confirmare cu `scor.confirmare_teren × fiabilitate_sursa.tracking_gps × calitate` (calitatea scade cu distanța); poziția devine GPS (`sursa_locatie` → `coordonate`, plafon 0,85) pentru elementele care nu sunt GIS |
| niciun stâlp la ≤ `raza_fara_stalp_m` și durată ≥ `tracking.durata_stalp_nou_min` | **stâlp presupus** `TRK-<event>-<n>`: predicție punctată, scor ≤ `tracking.plafon_stalp_presupus`, legat de cel mai apropiat stâlp pe străzi (`traseu_pe_strazi`) ca predicție |
| altfel (între praguri) | „oprire neclară”, doar în jurnal |

3. Un stâlp confirmat de mai multe opriri din aceeași tură se numără o dată (oprirea cea mai lungă).
4. Elementele „verificat de om” nu scad și nu se schimbă (doar jurnal).
5. Decizie eveniment: `scor_actualizat` dacă a validat ceva, `predictie` dacă doar a presupus, `fara_efect` dacă n-a găsit nimic. Eticheta în timeline: `tracking`.

### 2.3 Valori de pornire (`contracts/weights.yaml`, reglabile cu `reglaj:`)
```yaml
fiabilitate_sursa:
  tracking_gps: 0.60          # mai mic decât un raport de teren
tracking:
  durata_validare_min: 5      # sub asta oprirea nu validează
  raza_validare_m: 15         # stâlp „atins” de oprire
  durata_stalp_nou_min: 12    # cât trebuie să stea ca să presupunem un stâlp
  raza_fara_stalp_m: 25       # niciun stâlp mai aproape => loc fără stâlp
  plafon_stalp_presupus: 0.45
  viteza_m_s: 1.4             # mers pe jos
  pas_s: 15                   # un punct GPS la 15 s
  zgomot_m: 5
  stalpi_min: 3
  stalpi_max: 5
```
Exemplu: un stâlp SIM portocaliu (0,50), oprire 8 min la 4 m → +0,25 × 0,60 × ~0,9 ≈ +0,14 → 0,64, galben.

## 3. Cine ce face

Victor (B): contract, generator, motor, scenariu, teste. Claudiu (C): API, Lovable, demo. Laptopurile lucrează ca până acum: `git pull --rebase` la fiecare bloc; codul îl scriu agenți Sonnet, omul verifică.

### Faza 0 (B, ~45 min): contract
Un commit `contract:` cu `contracts/interfaces.md` actualizat:
- `event.schema.json`: tip nou `tracking_tura`; `echipa_sursa` una din cele 3 echipe; `tip_sursa_pondere: tracking_gps`; `detalii.tura {tura_id, seed, puncte[{t, lat, lon}]}`; `detalii.tracking` (scris de motor: opriri, validări, presupuneri).
- `state.schema.json`: `predictie.metoda` + `oprire_tracking`; `ultima_validare_tracking` (dată) pe element.
- `weights.yaml` + `weights.limits.yaml`: cheile din 2.3; relații: `durata_validare_min < durata_stalp_nou_min`, `raza_validare_m < raza_fara_stalp_m`.
- `api.openapi.yaml`: `POST /tracking/genereaza`, `POST /tracking/aplica`, `GET /tracking/ture` (vezi Faza 2).
- OpenSpec `openspec/changes/tracking-echipe/` (creat odată cu acest plan).

### Faza 1 (B, ~3 h): generator + motor
- **B1. `backend/tracking/` (modul nou, al lui B):** `genereaza_tura(net, strazi, cfg, echipa, seed, data)` ca în 2.1. Teste `backend/tracking/smoke_tracking.py`: determinism, toate punctele în zona de 3 km, la ≤ 20 m de o stradă (fără zgomot), opririle din `plan` regăsite de `gaseste_opriri`, opririle scurte prezente.
- **B2. Motor:** `backend/engine/tracking.py` (mixin în `GridModel`, ca `verificare_om.py`): ramura `tracking_tura` din `apply_event`, tabelul din 2.2, pași în StepTrace `opriri`, `validari_tracking` și, pentru stâlpii presupuși, `analiza_harta`. Teste în `smoke_sesiune4.py` (sau `smoke_tracking_motor.py`): validare stâlp portocaliu → crește și devine galben; oprire 15 min fără stâlp → `TRK-*` predicție ≤ 0,45 cu legătură pe străzi; opriri scurte ignorate; stâlp verificat de om neatins; aceeași tură aplicată de două ori = fără dublare; determinism.
- **B3. Scenariu:** 2 ture în timeline (ex. 2026-09-25 și 2026-10-30), generate determinist, adăugate în `events.json` de `scripts/genereaza_scenariu.py` (dintr-un fișier nou `data/events/ture-tracking.json`, scris de B). Distribuția culorilor rămâne în țintă (`--strict-distributie`).
- **Doc:** `docs/etapa-32-tracking-echipe.md`, README-uri.

### Faza 2 (C, ~1,5 h): API
- `POST /tracking/genereaza {echipa, seed?, data?}` → tura (2.1), fără să schimbe modelul. `seed` implicit: `<echipa>-<data>`.
- `POST /tracking/aplica {tura_id | tura, data?}` → StepTrace + `tracking`: listă pe opriri `{lat, lon, inceput, durata_min, tip: validare|stalp_presupus|scurta|neclara, element_id?, scor_inainte?, scor_dupa?, banda_inainte?, banda_dupa?, t_ajungere}` (ca UI-ul să arate rezultatul fiecărei opriri când tableta ajunge acolo), plus `focus` (bbox-ul turei).
- `GET /tracking/ture` → turele generate în sesiunea curentă (și cele 2 din scenariu).
- Teste în `smoke_api.py`; doc `docs/etapa-33-api-tracking.md`.

### Faza 3 (C, ~1,5 h + credite): Lovable P4 „Tracking echipe”
Un singur prompt, **netrimis până decide Victor**:
- Tab nou „Tracking echipe” lângă harta principală (aceeași hartă GIS, alt panou). Rapoartele și timeline-ul rămân neschimbate.
- Panou: alegi echipa (Mentenanță / Investiții / Racordări), „Generează tură” (afișează traseul gri punctat și durata), „Pornește”.
- **Animație:** marcajul tabletei merge pe traseu, accelerat (implicit ×60, comutator ×30/×60/×120, pauză). La fiecare oprire apare un cerc care crește cu un contor de minute.
- **Rezultate dinamice:** la „Pornește” se trimite `POST /tracking/aplica`; rezultatul fiecărei opriri se dezvăluie când tableta ajunge la ea (`t_ajungere`):
  - validare: stâlpul pulsează, pop-up „Stâlp SIM-012 confirmat de echipă: 0,50 → 0,64 (portocaliu → galben)”;
  - stâlp presupus: apare punctat, pop-up „Oprire de 15 min fără stâlp: stâlp presupus, acuratețe 0,42”;
  - oprire scurtă: un punct gri mic, fără pop-up.
- La final: rezumat („3 stâlpi confirmați, 1 stâlp presupus, 2 opriri scurte ignorate”) și timeline-ul sare la prezent, cu evenimentul „Tracking echipă”.
- Legendă pentru tipurile de oprire. Accesibilitate: `prefers-reduced-motion` = fără animație, rezultatul final direct; butoanele din tastatură; textul benzii lângă culoare.

### Faza 4 (B + C, ~30 min): demo și verificare
- `scripts/verifica_tot.sh` TOT VERDE (include `smoke_tracking` și noile teste).
- Pas nou în `docs/DEMO.md` (~30 s): „Tracking echipe → Mentenanță → Generează → Pornește”.
- Test cap-coadă prin tunel (Claudiu), capturi pe board.

## 4. Ordine și dependențe
```
Faza 0 (B, contract) ──> Faza 1 (B)  ──> Faza 4
                    └──> Faza 2 (C, API cu valori din motor sau „—”) ──> Faza 3 (C, Lovable, după decizia lui Victor) ──> Faza 4
```
Faza 2 poate începe imediat după contract; câmpurile care vin din motor apar null până la B2.

## 5. Riscuri
| Risc | Acoperire |
|---|---|
| Animația cere multe puncte (sute) | `pas_s` 15 s și accelerare; tura ~40–60 min → ~200 de puncte |
| Validările schimbă distribuția culorilor | doar 2 ture în scenariu; verificarea strictă o prinde; reglaj `tracking_gps` |
| Stâlp presupus lângă unul existent (zgomot GPS) | `raza_fara_stalp_m` 25 m > zgomot 5 m; test dedicat |
| Confuzie cu „traseul de ultima oră” scos | doc + UI: alt tab, alt nume, eveniment propriu |
| Credite Lovable | un singur prompt, grupat |
