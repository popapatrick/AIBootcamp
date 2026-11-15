# Prompt Lovable sesiunea 4, P2: pagina de intro + 3 butoane de echipă + panoul „Ce a înțeles AI-ul”

> **STARE: NETRIMIS — se trimite doar după decizia lui Victor, DUPĂ P1 aplicat și verificat, și după ce API-ul e verificat prin tunel.**

- **Dependențe:** P1 aplicat (hartă GIS, Straturi, Identificare, culori din `banda`). API cu: `GET /demo/exemple` (4 carduri din `data/reports/demo-intro.json`, există), `POST /demo/reset`, `GET /exemple?sursa=mentenanta|investitii|racordari`, `POST /rapoarte` cu `standardizare` și `focus`, `GET /evenimente` cu `standardizare`, `focus`, `text_original`, `echipa`. Verificat prin tunel înainte de trimitere (checklist jos).
- **Cost estimat:** ~4-5 credite (un mesaj grupat). Dacă Lovable se încurcă: împarte în (A) pagina `/` + rută hartă (~1,5), (B) butoane echipă + progres (~1,5), (C) panoul „Ce a înțeles AI-ul” + zbor/pop-up-uri (~2).
- **Câmpuri presupuse (exact ca în API, etapa-30):**
  - `GET /demo/exemple` = listă de `{id, titlu, descriere, sursa, text, data_moment, focus}`; `focus` e adesea `null` în fișier (se completează din eveniment, vezi 2).
  - `GET /exemple?sursa=X` = listă de `{id, titlu, text, data, asteptat?}`; `asteptat` NU se afișează.
  - `POST /rapoarte` (corp: `{text, sursa, data?}` ca acum) întoarce, pe lângă ce există: `standardizare` = `{metoda, metoda_eticheta, campuri[{camp, valoare, eticheta, din: "text"|"dedus"|"lipsa"}], lipsa[], localizare: {sursa, precizie_m, plafon, metoda, indiciu, text} | null, decizie: {cod, text, scor, banda}}` și `focus` = `{lat, lon, zoom, bbox{lat_min, lon_min, lat_max, lon_max}} | null`; `schimbari[]` (elementele atinse, ca acum).
  - `GET /evenimente`: pe fiecare intrare `text_original`, `echipa`, `standardizare` (poate avea `metoda` null), `focus`, `banda_inainte`, `banda_dupa`, `elemente_atinse`.
  - `POST /demo/reset` -> `{status: "ok", evenimente: N}`.

---

## PROMPT (de lipit în Lovable)

Schimbări în frontend, română, date fictive. Textele afișate din `standardizare`, `metoda_eticheta`, `decizie.text`, `localizare.text` vin GATA din API: UI-ul doar le afișează, NU le traduce, NU le reformulează și NU calculează benzi sau praguri. Orice câmp `null`/lipsă se afișează „—”, fără erori în consolă. Fără pagini sau dependențe în plus față de ce cere promptul.

### 1. Rute și pagina de intro (`/`)
- Ruta `/` = pagina de intro nouă. Harta (tot ecranul de acum, cu Straturi, Identificare, timeline) se mută pe ruta `/harta`. Butonul „Pagina de start” din bara de unelte (P1) duce la `/`; orice link vechi spre harta veche duce la `/harta`. Parametrul `?api=` și `API_BASE` se păstrează pe ambele rute (la navigare, `?api=` se propagă).
- Pagina de intro, de sus în jos:
  1. **Titlu** „Un model de rețea care se ține singur la zi” și o frază: „Rapoartele echipelor devin date standardizate; modelul își actualizează rețeaua, scorul de acuratețe și predicțiile, iar tu vezi totul pe hartă.”
  2. **3 carduri „Cum funcționează”**, în ordine: (1) „Standardizare cu AI” (textul liber al raportului devine date structurate); (2) „Modelul își actualizează rețeaua” (fiecare schimbare primește scor și culoare); (3) „Predicție pe hartă” (tot ce lipsește e propus pe străzi, cu acuratețe, neaplicat până se confirmă). Fiecare card: icoană simplă, titlu, 1-2 rânduri.
  3. **4 carduri „Exemple”** din `GET /demo/exemple` (titlu, `descriere`, o etichetă mică cu echipa din `sursa`: mentenanta = „Mentenanță”, investitii = „Investiții”, racordari = „Racordări”, altfel „—”, și butonul **„Vezi pe hartă”**). Dacă lista e goală sau apelul eșuează: „Exemplele nu sunt disponibile” (fără eroare în consolă).
  4. Butoane: **„Intră în hartă”** (către `/harta`) și **„Resetează demo”**: dialog de confirmare „Modelul revine la starea de start și rapoartele trimise se șterg. Continui?” cu „Resetează” / „Anulează”; la confirmare `POST {API_BASE}/demo/reset`, în timpul cererii „Se resetează…”, la succes mesaj „Demo resetat (N evenimente)” cu N din `evenimente`, la eroare roșu „Nu s-a putut reseta”. După reset, harta și timeline-ul se reîncarcă din API la următoarea deschidere (golește cache-ul pe dată).
  5. Subsol, o singură linie mică (≥ 14 px, contrast bun): „Date fictive, rețea demonstrativă.” Pe hartă NU revine niciun banner de date fictive.
- Aspect: curat, contrast ≥ 4,5:1, text ≥ 14 px, focus vizibil, Tab/Enter pe toate cardurile și butoanele, `aria-label` în română pe butoanele cu iconițe, `prefers-reduced-motion` oprește animațiile.

### 2. „Vezi pe hartă” (cardurile de exemplu)
La clic pe „Vezi pe hartă” la un card `c`:
1. Navighează la `/harta` cu timeline-ul/instantaneul setat la `c.data_moment` (aceeași logică ca derularea existentă a timeline-ului: `GET /retea?la=<data_moment>`).
2. Caută în `GET /evenimente` (cache-ul deja încărcat sau reîncărcat) intrarea al cărei `text_original` e egal cu `c.text` (comparat după trim și spații normalizate); dacă nu găsește, prima intrare cu `data` = `c.data_moment`; dacă nici asta, nu deschide panoul și arată doar harta la dată.
3. Zbor (~1,2 s; instant la `prefers-reduced-motion`) la `c.focus` dacă nu e null, altfel la `focus` al evenimentului găsit: `fitBounds` pe `bbox` dacă există, altfel `flyTo(lat, lon, zoom)`; dacă ambele sunt null, harta rămâne unde e.
4. Elementele din `elemente_atinse` ale evenimentului pulsează de 3 ori (stilul existent al contururilor portocalii) și se deschide un pop-up ancorat pe primul element atins cu o frază scurtă din `standardizare.decizie.text` + scorul („Scor 0,66”) + textul benzii din legendă.
5. Se deschide panoul „Ce a înțeles AI-ul” (vezi 4) pentru acel eveniment, fără animație pas cu pas (afișat direct), cu textul raportului (`text_original`) deasupra.

### 3. Butoanele de echipă (doar 3)
- În bara de unelte rămân DOAR **Mentenanță, Investiții, Racordări**; scoate „Apel client”, „Om din teren” și orice alt buton de echipă. Un buton de echipă activ e marcat vizibil (nu doar prin culoare).
- Clic pe buton: se deschide un panou (lateral, pliabil, Esc îl închide) cu:
  - lista de texte din `GET /exemple?sursa=mentenanta|investitii|racordari` (titlu + text scurtat; clic pe un element îl pune în câmpul de text); NU afișa `asteptat`;
  - butonul „Alt exemplu” (alege următorul text din listă, ciclic; lista goală = „Nu sunt exemple”);
  - câmp de text editabil (textarea, etichetă „Textul raportului”);
  - butonul **„Trimite raportul”** (dezactivat dacă textul e gol): `POST {API_BASE}/rapoarte` cu `{text, sursa: <echipa>}` (aceeași formă ca formularul existent; fără `trace_params`, fără `locatie`).
- Formularul „adaugă raport nou” existent rămâne ca alternativă pentru text liber (NU îl scoate).
- **În timpul cererii:** indicator de progres în 3 pași, în panou: „1. Standardizare AI” → „2. Potrivire în rețea” → „3. Decizie”. Pasul activ e evidențiat (text + icoană, nu doar culoare); pașii avansează la ~1 s (cache) și rămân pe „1.” până la răspuns dacă durează (un text nou poate lua 5-20 s); la răspuns toți devin bifați. La eroare HTTP: mesaj roșu „Nu s-a putut trimite raportul” și panoul rămâne editabil.
- **După răspuns (secvența, la fiecare pas ~0,6-1,2 s; sub `prefers-reduced-motion` totul se afișează instant):**
  1. panoul „Ce a înțeles AI-ul” se completează pas cu pas (4);
  2. harta zboară la `focus` din răspuns (~1,2 s; `bbox` -> fitBounds, altfel flyTo; `focus` null = nu zbura);
  3. elementele din `schimbari[]` pulsează de 3 ori;
  4. maximum 3 pop-up-uri ancorate pe hartă, câte unul pe schimbare (primele 3 din `schimbari`), cu textul „<tip element>, <decizie.text>, acuratețe <scor cu 2 zecimale> (<text bandă din legendă>)”; dispar la Esc, la clic pe hartă sau după 12 s;
  5. timeline-ul sare la poziția „acum” (cea mai recentă) și noul eveniment e evidențiat; reîncarcă `GET /retea` și `GET /evenimente`.
- Bannerul roșu „Eronat în cadrul prototipului” și insigna „predicție slabă / treapta N” rămân ca acum.

### 4. Panoul „Ce a înțeles AI-ul”
Panou (dreapta jos sau în stânga, fără să acopere Identificare; pliabil, închidere cu X/Esc, `role="complementary"`, `aria-label="Ce a înțeles AI-ul"`), alimentat din obiectul `standardizare` (din răspunsul `POST /rapoarte` sau din intrarea `GET /evenimente`). Secțiuni, în ordine:
1. **Antet:** `metoda_eticheta` ca etichetă mică (de ex. „AI (live)”, „AI (cache)”, „Regex (simplificat)”; `null` = „—”). Dacă `metoda_eticheta` e „Regex (simplificat)”, adaugă sub ea notița „Rezervă simplificată, fără AI”.
2. **Câmpuri extrase:** tabel/listă cu câte un rând pe fiecare element din `campuri[]`: `eticheta` (nume), valoarea (`valoare`; obiect `{lat, lon}` = „lat, lon” cu 5 zecimale; `null` = „—”) și o insignă după `din`: `text` = „Din text” (verde închis), `dedus` = „Dedus” (albastru), `lipsa` = „Lipsă” (gri, valoare „—”). Insigna are text, nu doar culoare; contrast ≥ 4,5:1.
3. **Ce lipsește:** dacă `lipsa[]` nu e gol: „Lipsesc: <elementele separate prin virgulă>”; dacă e gol: „Nu lipsește nimic”.
4. **Cum am localizat:** dacă `localizare` e null: „—”. Altfel `localizare.text` (afișat ca atare), plus rânduri mici: „Precizie: ±<precizie_m> m” (dacă nu e null), „Plafon acuratețe: <plafon>” (dacă nu e null), „Indiciu: <indiciu>” (dacă nu e null). Codurile `sursa`/`metoda` NU se afișează brute.
5. **Decizia:** `decizie.text` (ca atare), scorul `decizie.scor` cu 2 zecimale și o bară colorată cu culoarea benzii `decizie.banda` din `GET /legenda` plus textul benzii; `null` = „—”. Fără praguri în cod.
- Când panoul e deschis după trimitere, secțiunile 2-5 apar pe rând (animat, ~0,6 s între ele), iar „Decizia” e ultima. Pentru intrările vechi din timeline (`standardizare.metoda` poate fi null): se afișează la fel, cu „—” la metodă.
- Panoul din „De ce?” de pe Identificare și cel din timeline rămân; „Ce a înțeles AI-ul” e separat și nu le înlocuiește.

### NU SCHIMBA (tot ce a făcut P1 și ce era înainte)
- **Tot ce a adus P1:** panoul „Straturi” (6 bife) și legenda din `GET /legenda`, bara de unelte (căutare, „Încadrează rețeaua”, „Pagina de start”), panoul „Identificare” (tabel, „De ce?”, „Marchează verificat de om”), bara de jos (scara, coordonatele cursorului), culorile DOAR din `banda`, stilurile de linie (plină / punctată / gri punctat), insigna ✓, tooltip-urile, regulile de accesibilitate (contrast, tastatură, aria-label, reduced-motion, ținte ≥ 32 px). Absența elementelor scoase în P1 rămâne (fără banner „DATE FICTIVE” pe hartă, fără scenariu extrem, fără trasee/clic-pe-hartă/„Fire mutate”, fără câmpuri trace, fără coduri brute afișate).
- **Timeline-ul derulabil vertical** („Evenimente”, derularea care mută harta după 150 ms, cache pe dată, „De ce?” pe intrare, contururile portocalii pe `elemente_atinse`): rămâne exact; se mută orizontal abia în P3.
- „Show pipeline” cu pașii lui, formularul „adaugă raport nou”, bannerul „Eronat în cadrul prototipului”, insigna „predicție slabă / treapta N”.
- `API_BASE` și `?api=`, logica `POST /rapoarte`, `POST /predictii/{id}/decizie`, `GET /evenimente`, `POST /element/{id}/verificare`.
- Nu adăuga alte pagini decât `/` și `/harta`, nu adăuga dependențe, nu publica.

---

## Verificare (de făcut de Claudiu, prin tunel: `backend/api/demo_start.sh` + link cu `?api=<tunel>`)
Înainte de trimitere, pe API:
- [ ] `curl $TUNEL/demo/exemple` întoarce 4 carduri cu `id, titlu, descriere, sursa, text, data_moment, focus`.
- [ ] `curl "$TUNEL/exemple?sursa=mentenanta"` (și investitii, racordari) întoarce liste cu `titlu`, `text`; `?sursa=apel_client` dă 422.
- [ ] `curl -X POST $TUNEL/rapoarte -H 'content-type: application/json' -d '{"text":"<un text demo>","sursa":"mentenanta"}'` conține `standardizare` (campuri, lipsa, localizare, decizie) și `focus`.
- [ ] `curl $TUNEL/evenimente` are `text_original`, `standardizare`, `focus` pe intrări (verifică că un `text_original` din card se potrivește cu un `text` din `demo-intro.json`).
- [ ] `curl -X POST $TUNEL/demo/reset` dă `{status: ok, ...}` (apoi `./demo_start.sh --reset-model` dacă e nevoie).

După aplicarea promptului, în preview:
- [ ] `/` arată titlul, 3 carduri „Cum funcționează”, 4 carduri de exemplu, „Intră în hartă”, „Resetează demo”, subsolul „Date fictive, rețea demonstrativă.”; pe `/harta` nu e niciun banner de date fictive.
- [ ] „Pagina de start” de pe hartă duce la `/`; „Intră în hartă” duce la `/harta`; `?api=` se păstrează.
- [ ] „Vezi pe hartă” pe fiecare din cele 4 carduri: harta trece la `data_moment`, zboară la zonă (cu `focus` null din card: folosește `focus` al evenimentului), elementele pulsează, apare pop-up, se deschide „Ce a înțeles AI-ul”; la un card fără eveniment găsit: doar harta la dată, fără erori.
- [ ] „Resetează demo”: apare confirmarea; „Anulează” nu face nimic; „Resetează” arată „Demo resetat (N evenimente)”; timeline-ul se reîncarcă corect după.
- [ ] În bara de unelte sunt exact 3 butoane de echipă (Mentenanță, Investiții, Racordări); fără „Apel client”/„Om din teren”.
- [ ] Clic pe fiecare echipă: panou cu lista din `GET /exemple`, „Alt exemplu” ciclează, textul e editabil, nu se vede `asteptat`; „Trimite raportul” dezactivat la text gol.
- [ ] La trimitere (text din cache): progres în 3 pași, apoi panoul „Ce a înțeles AI-ul” se completează pas cu pas (câmpuri cu „Din text”/„Dedus”/„Lipsă”, „Ce lipsește”, „Cum am localizat”, „Decizia” cu scor și bandă), harta zboară la `focus`, elementele pulsează de 3 ori, maximum 3 pop-up-uri, timeline-ul sare la „acum” cu noul eveniment evidențiat.
- [ ] Etichetă de metodă corectă: „AI (cache)” pentru texte din cache, „AI (live)” pentru text nou cu `ai_cli`, „Regex (simplificat)” cu notița doar la rezervă.
- [ ] Un text cu `localizare` null: secțiunea arată „—”; câmpuri `null`: „—”; zero erori în consolă.
- [ ] Eroare simulată (API oprit): „Nu s-a putut trimite raportul”, panoul rămâne utilizabil.
- [ ] Neschimbat din P1: Straturi + legendă, căutare, Identificare + „Marchează verificat de om”, culori din `banda`, linii plină/punctată/gri, ✓, scara și coordonatele; timeline-ul vertical funcționează; „Show pipeline” și formularul „adaugă raport nou” intacte.
- [ ] Tastatură: Tab parcurge pagina de intro, panoul de echipă și panoul AI; Esc închide panourile și pop-up-urile; focus vizibil; `prefers-reduced-motion` face zborul și pulsul instant; text ≥ 14 px; ținte ≥ 32 px.
- [ ] Notat în `frontend/README.md`: mesajul trimis, creditele consumate, commit-ul Lovable.
