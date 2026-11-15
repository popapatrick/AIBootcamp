# Prompt Lovable sesiunea 4, P3: timeline orizontal + vizualizarea căutării pe stradă + a analizei hărții

> **STARE: NETRIMIS — câmpurile cautare_strada/analiza_harta vin după V3/V6 (Victor)**

- **Ordine:** se trimite DUPĂ P1 și P2 (nu le contrazice: Straturi, Identificare, bara de unelte, butoanele de echipă, panoul „Ce a înțeles AI-ul” rămân). Nu se trimite fără decizia lui Victor.
- **Dependențe API:** `GET /evenimente` cu `pasi[]` care conține pașii `cautare_strada` și `analiza_harta` (V6, V3), `focus`, `banda`; `POST /rapoarte` care întoarce aceiași pași; `predictie.traseu` / `predictie.alternative` pe features din `GET /retea`. Timeline-ul de ~55 de evenimente (secț. 7 din plan) trebuie să existe, altfel se vede gol.
- **Câmpuri presupuse (verifică pe răspuns real înainte de trimitere):**
  - Pe intrarea din `GET /evenimente` / răspunsul `POST /rapoarte`: `data`, `event_id`, `echipa` (dacă lipsește: „—”), `text` sau `rezumat`, `eticheta`, `decizie`, `eronat_prototip`, `schimbari[{element_id, ce, scor_inainte, scor_dupa, banda_inainte, banda_dupa, de_ce}]`, `elemente_atinse`, `focus {lat, lon, zoom, bbox{lat_min, lon_min, lat_max, lon_max}}`, `standardizare.campuri[{camp, valoare, eticheta, din}]`, `pasi[{nume, incredere, rezultat, motive?}]`.
  - Pasul `cautare_strada` (în `pasi[].rezultat`, sau direct pe pas dacă B nu folosește `rezultat`): `{strada, de_la_m, pana_la_m, punct{lat,lon}, precizie_m, metoda: ancore|conventie|indiciu, indiciu{tip, numar, numar_2, text}, ancore[{numar, lat, lon}], candidati[{element_id, distanta_m}], ales}` (`ales` = `element_id` al candidatului ales; poate fi `null`).
  - Pasul `analiza_harta`: `{tinta{lat,lon}, bransament_m, ales{de_la, lungime_m, strazi[], stalpi_noi, stalpi_reutilizati, traseu[[lat,lon],...]}, alternative[{de_la, lungime_m, motiv, traseu[[lat,lon],...]}], acuratete, explicatie[]}`; banda alesului vine din `decizie`/`banda` a intrării (nu se calculează din `acuratete`).
  - `GET /legenda` pentru culorile benzilor (neschimbat din P1).
  - Pozițiile elementelor candidate se iau din `GET /retea` (după `element_id`).
- **Cost estimat:** ~5-6 credite (un mesaj grupat, ca P1). Dacă Lovable se încurcă: (A) timeline orizontal + fișă, (B) căutare pe stradă, (C) analiza hărții (~2 credite fiecare).

---

## PROMPT (de lipit în Lovable)

Schimbări de afișare (frontend, română). Nu schimba logica de date. Orice câmp `null` sau lipsă se afișează „—”; **dacă un pas (`cautare_strada` sau `analiza_harta`) lipsește sau nu are câmpurile obligatorii (`punct` / `ales.traseu`), vizualizarea lui NU apare deloc** (fără erori în consolă, fără placeholder). Culoarea elementelor vine DOAR din `banda`; nu recalcula praguri din `scor`.

### 1. Timeline orizontal (înlocuiește panoul vertical „Evenimente” din P1/sesiunea 3)
- Bară jos, pe toată lățimea (peste scara grafică și coordonatele din P1, nu le acoperi), cu axa timpului de la 1 aug. 2026 până azi. Evenimentele din `GET /evenimente`, în ordine cronologică, ca puncte pe axă, poziționate proporțional cu data; repere de lună (aug., sep., oct., nov.) sub axă. Derulabilă orizontal: roată, trackpad și săgețile stânga/dreapta (când bara are focus).
- Puncte colorate după efect (derivat din `eticheta`, `decizie` și `schimbari[]`): adăugat, scos/demontat, mutat, scor ↑, scor ↓ (compară `scor_inainte` cu `scor_dupa`; `null` la `scor_inainte` = adăugat), verificat de om (`eticheta` de decizie om / `verificare_om`). Culorile din legenda existentă; fiecare efect are și o formă diferită (cerc, pătrat, romb, triunghi sus/jos, cerc cu ✓), ca să nu depindă doar de culoare. Tooltip cu data și `eticheta`.
- **Implicit și după orice raport nou (din butoanele de echipă sau formular): poziția „acum”, cel mai din dreapta punct, activ și vizibil** (bara derulează singură acolo). Cele mai multe pe aceeași zi: puncte alăturate, fără suprapunere.
- Selectarea unui punct (clic sau săgeți): devine activ; harta trece la acea dată (`GET /retea?data=<data>`, cu același cache pe dată și întârziere de 150 ms ca acum), zboară la `focus` (bbox, zoom din `focus.zoom`; dacă `focus` e null, harta rămâne unde e) și se deschide **fișa evenimentului**, deasupra barei:
  - data, echipa (`echipa`), textul raportului scurtat la ~3 rânduri cu „mai mult”;
  - ce a extras AI-ul: 3–4 câmpuri din `standardizare.campuri` (`eticheta`: `valoare`, cele cu `din` = `lipsa` marcate „lipsă”);
  - decizia (textul din `standardizare.decizie.text` sau `decizie`), scor și bandă înainte → după (din `schimbari[0]`: `scor_inainte` → `scor_dupa`, cu punct colorat pe `banda_inainte` / `banda_dupa`);
  - butonul „De ce?” (pașii din `pasi[]` ca în panoul actual) și, dacă există, fișele din secțiunile 2 și 3 de mai jos.
- Contururile portocalii pe `elemente_atinse` și pulsația scurtă (oprită la `prefers-reduced-motion`) rămân.
- Butonul „Listă” (în bara timeline-ului) deschide toate evenimentele ca listă verticală într-un panou lateral, cu aceleași carduri de acum (dată, `eticheta`, decizie, scor înainte → după); **panoul vertical permanent dispare**. Clic pe un card din listă selectează punctul respectiv pe bară.
- Accesibilitate: puncte focusabile (Tab / săgeți, Enter selectează, Esc închide fișa), `aria-label` cu data și eticheta, focus vizibil, ținte ≥ 32 px, text ≥ 14 px.

### 2. Vizualizarea „Căutare pe stradă” (doar când intrarea activă sau răspunsul unui raport nou are pasul `cautare_strada` cu `punct`)
Pe hartă, peste elementele normale:
- **Fereastra pe stradă:** bandă semitransparentă (albastru, ~25% opacitate) centrată pe `punct`, cu raza `(pana_la_m − de_la_m) / 2` m (dacă `de_la_m`/`pana_la_m` lipsesc: raza `precizie_m`). Etichetă „Fereastră <strada>, <rotunjit> m”.
- **Punctul estimat:** marcaj mic cu cerc de precizie de rază `precizie_m` (linie subțire, fără umplere).
- **Ancorele:** puncte mici gri-închis cu numărul (`ancore[].numar`) lângă ele.
- **Candidații:** fiecare element din `candidati` apare cu contur albastru subțire (cerc mare în jurul poziției, ~10 px); **cel ales (`ales`) e plin** (umplere cu culoarea benzii lui, din `banda`) și are eticheta „ales”.
- **Fișa „Căutare pe stradă”** în fișa evenimentului, 3 rânduri (se omit rândurile ale căror date lipsesc):
  1. „Indiciu: <`indiciu.text`>” (dacă `indiciu.text` lipsește: compune din `tip` + `numar`, ex. „lângă nr. 15 pe Strada Viilor”);
  2. „Fereastră <rotunjit `pana_la_m − de_la_m`> m (<metoda>)”, cu `metoda`: `ancore` = „ancore din rapoarte anterioare”, `conventie` = „convenție de numerotare, fără ancore”, `indiciu` = „indiciu din text”; plus „±<`precizie_m`> m”;
  3. „<număr candidați> stâlpi găsiți; ales <`ales`>, alternative <ceilalți `element_id`>” (0 candidați: „Niciun element în fereastră”; fără `ales`: „fără alegere, de verificat”).
- Clic pe un candidat deschide „Identificare” (P1) pentru el.

### 3. Vizualizarea „Analiza hărții” (când pasul `analiza_harta` există, cu `ales.traseu` nenul; sau când un feature are `predictie.traseu`)
- **Drumul ales:** linie groasă punctată (≥ 4 px) pe `ales.traseu`, colorată după banda intrării (`banda` din `decizie`/schimbare). Urmărește străzile (nu o linie dreaptă).
- **Alternativele:** linii subțiri gri (`alternative[].traseu`), cu eticheta `motiv` la mijlocul fiecăreia (ex. „mai lung cu 180 m”); alternativele fără `traseu` apar doar în fișă.
- **Stâlpii:** cei noi (`stalpi_noi`) ca puncte pline pe drum, cei refolosiți (`stalpi_reutilizati`) cu contur; dacă pasul nu dă pozițiile lor, nu-i desena, ci afișează doar numerele în fișă. **Branșamentul:** segment scurt între capătul traseului și `tinta`, lungime `bransament_m`.
- **Fișa „Analiza hărții”** în fișa evenimentului: cele 3 rânduri din `explicatie[]` (dacă sunt mai multe, primele 3 + „mai mult”), plus „Lungime: <`ales.lungime_m`> m” și „Pe: <`ales.strazi` separate prin virgulă>”.
- **Mutare fire** (când `eticheta` = mutare fire și pasul are traseu): în plus, cercul zonei (din `focus` dacă pasul nu dă centru/rază; dacă nu există nicio sursă, nu-l desena), tronsoanele afectate (`schimbari[]` cu `ce` = marcat/de verificat) cu contur roșu și traseul nou ca mai sus.
- Un feature din `GET /retea` cu `predictie.traseu` se desenează punctat pe acel traseu (nu pe linia dreaptă) cu banda lui; `predictie.alternative` cu `traseu` apar gri subțire doar când elementul e selectat în Identificare.

### 4. După un raport nou
Pașii noi din răspunsul `POST /rapoarte` (`pasi[]`) se desenează la fel (secț. 2 și 3) imediat după zborul la `focus`; timeline-ul sare la „acum” cu punctul nou activ. Vizualizările dispar la selectarea altui eveniment sau la Esc pe fișă.

### NU SCHIMBA
- Tot ce au făcut P1 și P2: panoul „Straturi” și legenda, bara de unelte cu căutare, „Încadrează rețeaua”, „Pagina de start”, panoul „Identificare” și „Marchează verificat de om”, pagina de intro, butoanele echipelor, secvența animată și panoul „Ce a înțeles AI-ul”, etichetele „AI (live)” / „AI (cache)” / „Regex (simplificat)”, bannerul „Eronat în cadrul prototipului”.
- Setarea `API_BASE`, parametrul `?api=`, logica `POST /rapoarte`, `POST /element/{id}/verificare`, `POST /predictii/{id}/decizie`, `GET /evenimente`, `GET /retea?data=`.
- Culorile benzilor (din `GET /legenda`), stilurile de linie plină / punctată / gri punctat, scara grafică și coordonatele cursorului.
- Nu adăuga pagini noi, nu adăuga dependențe, nu publica. Nu hardcoda texte de stradă, ID-uri sau coordonate.

---

## Verificare după (de făcut de Claudiu, prin tunel: `backend/api/demo_start.sh` + link cu `?api=<tunel>`)
Înainte de trimitere, pe API:
- [ ] `curl "$TUNEL/evenimente" | jq '.[].pasi[].nume' | sort | uniq -c` arată `cautare_strada` și `analiza_harta` (dacă lipsesc: V3/V6 nu sunt gata, NU trimite).
- [ ] Un eveniment cu `cautare_strada`: `rezultat` are `strada, de_la_m, pana_la_m, punct, precizie_m, metoda, candidati, ales`; un eveniment cu `analiza_harta`: `ales.traseu` (listă [lat, lon]) și `explicatie`. Dacă forma diferă de „Câmpuri presupuse”, ajustează promptul.
- [ ] `focus` și `banda` prezente pe evenimente; ~55 de evenimente între 1 aug. și 14 nov.
- [ ] `POST /rapoarte` cu „stâlp căzut pe Strada Viilor nr. 12” întoarce pasul `cautare_strada` (apoi `./demo_start.sh --reset-model`).

După aplicarea promptului, în preview:
- [ ] Jos e timeline orizontal cu puncte pe axă, repere de lună; derulabil cu roată, trackpad, săgeți; panoul vertical nu mai e permanent, „Listă” îl deschide.
- [ ] La încărcare, poziția activă e cea mai din dreapta („acum”); la fel după un raport nou.
- [ ] Puncte cu culori ȘI forme diferite după efect; selectarea unui punct mută harta la data lui, zboară la `focus`, deschide fișa (dată, echipă, text scurtat, 3–4 câmpuri extrase, decizie, scor/bandă înainte → după, „De ce?”).
- [ ] Eveniment cu `cautare_strada`: se văd banda pe stradă, punctul cu cercul de precizie, ancorele cu număr, candidații cu contur, cel ales plin; fișa „Căutare pe stradă” are cele 3 rânduri; clic pe candidat deschide Identificare.
- [ ] Eveniment cu `analiza_harta`: drum gros punctat pe străzi (nu linie dreaptă), alternative gri cu motiv, branșament scurt, fișa „Analiza hărții” cu explicația și lungimea.
- [ ] Eveniment fără aceste pași: nicio vizualizare, nicio eroare în consolă, „—” la câmpuri lipsă.
- [ ] Raport nou (buton de echipă): pașii se desenează, timeline-ul sare la „acum”.
- [ ] Tastatură (Tab/săgeți/Enter/Esc), `aria-label`, `prefers-reduced-motion`, ținte ≥ 32 px, text ≥ 14 px; P1 și P2 neschimbate (Straturi, Identificare, intro, echipe).
- [ ] Notat în `frontend/README.md`: mesajul trimis, creditele consumate, commit-ul Lovable.
