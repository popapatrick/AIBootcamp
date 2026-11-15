# Prompt Lovable sesiunea 4, P4: tab „Tracking echipe” + buton „Șterge”

> **STARE: scris 15 nov., NETRIMIS (așteaptă decizia lui Victor). Nu se trimite fără ea.**

- **Ordine:** DUPĂ P1, P2, P3 (nu le contrazice: Straturi, Identificare, intro, butoanele de echipă, timeline orizontal rămân).
- **Dependențe API (toate pe main, `docs/etapa-35-api-tracking-stergere.md`):** `POST /tracking/genereaza`, `GET /tracking/ture`, `POST /tracking/aplica`, `POST /element/{id}/stergere`, `stergibil` / `stergere_n` în `GET /retea`, `eticheta_text` în `GET /evenimente`.
- **Cost estimat:** ~5 credite (un mesaj grupat). Dacă Lovable se încurcă: (A) tab Tracking, (B) butonul „Șterge” (~1 credit).

---

## PROMPT (de lipit în Lovable)

Două funcții noi, în română. Nu schimba logica existentă. Textele afișate vin din API (câmpurile `eticheta`, `echipa_eticheta`, `motiv`); nu hardcoda praguri, culori de bandă (vin din `GET /legenda`) sau ID-uri. Orice câmp `null` sau lipsă = „—”.

### 1. Tab separat „Tracking echipe” (lângă „Hartă” / „Listă”, aceeași hartă și aceleași straturi)
Simulează tableta unei echipe în teren: o tură GPS pe străzi; opririle lungi lângă un stâlp îl confirmă, o oprire lungă unde nu e stâlp propune un stâlp nou.

**Controale (panou lateral):**
- Trei butoane de echipă: „Mentenanță”, „Investiții”, „Racordări” (valorile `mentenanta`, `investitii`, `racordari`), unul activ.
- „Generează tură”: `POST {API_BASE}/tracking/genereaza` cu `{"echipa": "<activă>", "seed": "<text opțional din câmpul Seed>", "data": "<data din timeline, YYYY-MM-DD>"}`. Câmpul „Seed” e opțional (gol = nu-l trimite); același seed dă aceeași tură.
- După generare: panoul arată `echipa_eticheta`, `durata_min` („71 min”), `lungime_m` („1,4 km”), numărul de puncte. Pe hartă, traseul din `puncte[]` (lat, lon) ca linie albastră subțire, cu un marcaj de start. Se ignoră `plan` (doar depanare).
- „Pornește”, „Pauză”, „Reia”, „Din nou”, plus comutator de viteză (x30, x60, x120; implicit x60). Un marcaj „tabletă” (cerc albastru cu contur alb) se mișcă pe traseu în funcție de `t` (secunde de la `puncte[0].t`), accelerat. Linia deja parcursă se îngroașe/colorează, restul rămâne subțire. Butonul „Aplică în model” e dezactivat până la final sau până la „Sari la sfârșit”.
- `GET {API_BASE}/tracking/ture` listează turele (generate acum și din scenariu) într-un selector „Ture”: `echipa_eticheta`, `data`, `durata_min`, `aplicata` ca insignă „Aplicată” / „Neaplicată”. Alegerea unei ture generate nu o aplică.

**Aplicare:** `POST {API_BASE}/tracking/aplica` cu `{"tura_id": "<tura_id>"}`. Răspunsul are `tracking[]` și `focus`. Apelul se face la apăsarea „Aplică în model” (sau automat când animația ajunge la final); animația poate rula și pe răspunsul deja primit, dar rezultatul fiecărei opriri apare doar când tableta ajunge la ea.

**Opririle (din `tracking[]`), în ordinea `t_ajungere`** (secunde de la începutul turei; când timpul animat >= `t_ajungere`, oprirea se dezvăluie; la oprire tableta stă `durata_min` simulat, accelerat):
- `tip: "validare"` (eticheta „Stâlp confirmat”): cerc verde mare la `lat, lon`, etichetă `eticheta`; pop-up: „<element_id>”, „Oprire <durata_min> min la <distanta_m> m”, „Scor <scor_inainte> → <scor_dupa>” cu un punct colorat pe `banda_inainte` și altul pe `banda_dupa` (culorile din `GET /legenda`); când banda se schimbă, o scurtă tranziție (săgeată colorată) înainte → după.
- `tip: "stalp_presupus"` („Stâlp presupus”): cerc portocaliu punctat (contur punctat, umplere transparentă), la fel și legătura spre rețea (`legatura_id`, desenată din `GET /retea` după `element_id`, linie punctată); pop-up: „Stâlp presupus” + „Scor <scor_dupa>” cu punct pe `banda_dupa`; fără „înainte” (`scor_inainte` lipsește).
- `tip: "scurta"` („Oprire scurtă”): punct gri mic, FĂRĂ pop-up (doar `title`/aria-label cu eticheta).
- `tip: "neclara"` („Oprire neclară”): punct gri-deschis mic cu `motiv` în tooltip.
- Forme diferite pe lângă culoare (cerc plin / cerc punctat / punct mic), ca să nu depindă doar de culoare.

**Rezultat (card sub hartă, apare după aplicare):** titlul „Tura echipei <echipa_eticheta>”; contoare: N „Stâlpi confirmați”, N „Stâlpi presupuși”, N „Opriri scurte” (numărate din `tracking[].tip`); lista stâlpilor confirmați, fiecare rând „<element_id>: <scor_inainte> → <scor_dupa>” cu două puncte de bandă; clic pe un rând zboară harta la oprire. Dacă răspunsul are `decizie: "fara_efect"` (tura era deja aplicată): banner „Tura a fost deja aplicată, fără modificări.” și fără contoare noi.
- După aplicare: reîncarcă `GET /retea` (stâlpii confirmați își schimbă banda pe hartă; cei presupuși apar punctat) și `GET /evenimente` (în timeline apare „Tracking echipă”, câmpul `eticheta_text`), și mută timeline-ul la „prezent”. Harta zboară la `focus` (bbox, `zoom`).
- Erori: 404/422/501 → mesaj roșu scurt cu `detail`, fără blocarea UI-ului.

**Exemplu real de răspuns** (`POST /tracking/genereaza`, `seed=demo`, `data=2026-11-15`; `puncte` trunchiat):
```json
{"tura_id": "TURA-mentenanta-20261115-7d53932e", "echipa": "mentenanta", "echipa_eticheta": "Mentenanță",
 "data": "2026-11-15", "seed": "demo", "lungime_m": 1408.0, "durata_min": 70.9, "linie_dreapta": 0,
 "puncte": [{"t": "2026-11-15T08:00:00", "lat": 44.2804775, "lon": 26.0670306},
            {"t": "2026-11-15T08:00:15", "lat": 44.2804933, "lon": 26.0670208}]}
```
**Exemplu real `tracking[]`** din `POST /tracking/aplica` (câmpul `motiv` omis aici):
```json
[{"tip": "validare", "eticheta": "Stâlp confirmat", "t_ajungere": 0, "lat": 44.280467, "lon": 26.066973,
  "durata_min": 7.5, "element_id": "NOU-EV4-021", "distanta_m": 7.2,
  "scor_inainte": 0.582, "banda_inainte": "portocaliu", "scor_dupa": 0.696, "banda_dupa": "galben"},
 {"tip": "stalp_presupus", "eticheta": "Stâlp presupus", "t_ajungere": 870, "lat": 44.283194, "lon": 26.068684,
  "durata_min": 15.0, "element_id": "TRK-EV-TRK-001-1", "legatura_id": "TRK-EV-TRK-001-1-L",
  "scor_dupa": 0.45, "banda_dupa": "portocaliu"},
 {"tip": "scurta", "eticheta": "Oprire scurtă", "t_ajungere": 1815, "lat": 44.283163, "lon": 26.067941, "durata_min": 1.75},
 {"tip": "validare", "eticheta": "Stâlp confirmat", "t_ajungere": 2595, "lat": 44.284323, "lon": 26.066164,
  "durata_min": 7.25, "element_id": "SIM-007", "distanta_m": 5.6,
  "scor_inainte": 0.269, "banda_inainte": "rosu", "scor_dupa": 0.391, "banda_dupa": "rosu"}]
```
Observă: un stâlp poate rămâne în aceeași bandă (SIM-007 rămâne roșu, scorul crește totuși); afișează scorul chiar dacă banda nu se schimbă. `focus`: `{"lat": 44.282827, "lon": 26.065719, "zoom": 16, "bbox": {"lat_min": 44.280158, "lat_max": 44.285496, "lon_min": 26.062294, "lon_max": 26.069144}}`.

### 2. Butonul „Șterge” în panoul „Identificare”
- În panoul „Identificare” al unui element, lângă „Marchează verificat de om”, buton „Șterge” (roșu discret). **Vizibil DOAR când `properties.stergibil === true`** (din `GET /retea`); pe elementele GIS și simulate din rețeaua de start nu apare.
- Clic: dialog de confirmare: „Se vor șterge **<stergere_n>** elemente.” (dacă `stergere_n` = 1: „Se va șterge 1 element.”), câmp „Motiv (opțional)” și butoanele „Șterge” (roșu) și „Anulează”. Esc și clic pe fundal = Anulează; focusul pornește pe „Anulează”.
- „Șterge”: `POST {API_BASE}/element/{element_id}/stergere` cu `{"motiv": "<text sau omis>"}`. Pe succes (200): închide dialogul, reîncarcă `GET /retea` și `GET /evenimente`, mută timeline-ul la „prezent”, un toast „Șters: <stergere.n> elemente” (din `stergere.n`) și panoul Identificare se golește (elementul nu mai e pe hartă). În timeline apare intrarea „Ștergere” (`eticheta_text`). Elementele șterse se văd încă la date anterioare.
- Erori: 409 → mesajul din `detail` (ex. „deja_sters: ... e deja șters de om” sau „nu_se_sterge_retea_start: ...”); 404 → „Elementul nu mai există”; fără blocarea UI-ului.
- Exemplu real de feature (`GET /retea`): `{"element_id": "TRK-EV-TRK-001-1", "stergibil": true, "stergere_n": 2, "banda": "portocaliu", "eticheta_origine": "Din raport"}`; pe `SIM-011`: `stergibil: false`, `stergere_n: 0`.
- Exemplu real de răspuns la ștergere: `{"decizie": "sters", "stergere": {"tinta_id": "TRK-EV-TRK-001-1", "elemente": ["TRK-EV-TRK-001-1", "TRK-EV-TRK-001-1-L"], "n": 2, "motiv": "nu există în teren"}, ...}`. Decizia „sters” se afișează „Șters de om”.

### Accesibilitate
Butoane și puncte focusabile (Tab, Enter/Space), `aria-label` pe opriri („Stâlp confirmat SIM-007, scor 0,27 spre 0,39”), focus vizibil, ținte >= 32 px, text >= 14 px; animația respectă `prefers-reduced-motion` (fără mișcare: tableta sare direct la fiecare oprire).

### NU SCHIMBA
- Tot ce au făcut P1–P3: Straturi și legendă, bara de unelte, Identificare și „Marchează verificat de om”, intro, butoanele de echipă pentru rapoarte, panoul „Ce a înțeles AI-ul”, timeline orizontal, Căutare pe stradă, Analiza hărții.
- `API_BASE`, `?api=`, `POST /rapoarte`, `POST /element/{id}/verificare`, `POST /predictii/{id}/decizie`, `GET /evenimente`, `GET /retea?data=`.
- Nu adăuga dependențe, nu publica. Nu afișa `tracking_gps` sau `oprire_tracking` ca atare, doar textele din API.

---

## Verificare după (Claudiu, prin tunel: `backend/api/demo_start.sh` + link cu `?api=<tunel>`)
Înainte: `curl $TUNEL/tracking/ture | jq length` >= 2 și un `POST /tracking/genereaza` întoarce `puncte`.
- [ ] Tab „Tracking echipe”: 3 butoane de echipă, „Generează tură” desenează traseul (albastru) și arată durata/lungimea.
- [ ] „Pornește” mișcă tableta; fiecare oprire apare doar când tableta ajunge la ea; confirmările arată „înainte → după” cu benzi; stâlpul presupus e punctat; opririle scurte nu au pop-up.
- [ ] „Aplică în model”: contoare corecte, harta zboară la `focus`, `/retea` reîncărcat, timeline are „Tracking echipă”; a doua aplicare = banner „deja aplicată”.
- [ ] „Resetează demo” golește turele din listă (cele din scenariu rămân).
- [ ] „Șterge” apare doar pe elemente cu `stergibil` (nu pe SIM-*/GIS); confirmarea spune câte elemente; după ștergere elementul dispare, apare „Ștergere” în timeline, la o dată anterioară elementul se vede.
- [ ] Tastatură, `aria-label`, `prefers-reduced-motion`; P1–P3 neschimbate.
