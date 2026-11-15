# Prompt Lovable sesiunea 4, P1: curățenie + hartă tip GIS + culori din `banda` + panoul „Identificare”

> **STARE: NETRIMIS — se trimite doar după decizia lui Victor și după ce API-ul are câmpurile.**

- **Dependențe:** contract sesiunea 4 (`b9c59ea`) pe main; API care întoarce în `GET /retea`: `banda`, `verificat_om`, `verificat_om_data`, `sursa_locatie`, `t0`, `eticheta_origine`; `GET /legenda`; `POST /element/{id}/verificare`; `GET /element/{id}` (istoric). Verificat prin tunel înainte de trimitere (vezi checklist-ul de jos).
- **Cost estimat:** ~5-7 credite (un singur mesaj grupat; sesiunea 3 a costat 3,4, timeline-ul derulabil 4,7; P1 e mai mare). Dacă Lovable se încurcă: împarte în (A) curățenie, (B) Straturi + legendă + bară de unelte + bară de jos, (C) Identificare + verificare + accesibilitate (~2 credite fiecare).
- **Câmpuri presupuse (exact ca în contract):** pe feature `properties`: `element_id`, `tip_element`, `nivel` (nu se afișează), `scor`, `banda` (`verde|galben|portocaliu|rosu`), `origine`, `eticheta_origine` (`GIS` | `Din raport`), `sursa_locatie`, `t0`, `ultima_verificare`, `verificat_om`, `verificat_om_data`, `predictie` (`{metoda, slaba, treapta, ...}` sau null), `scos_din_uz`/`nivel = scos_din_uz`; `zona` = `{centru:{lat,lon}, raza_m}` la rădăcina `GET /retea`. `GET /legenda` = `{benzi:[{banda,de_la,culoare,text}], linii:[{stil,text}], insigne:[{cod,text}]}`. `GET /element/{id}` = ElementState + istoric (`motive[]` cu `text`, `efect`, `data`).

---

## PROMPT (de lipit în Lovable)

Schimbări de afișare, aspect și un buton nou (frontend, română, date fictive). Orice câmp `null` sau lipsă se afișează „—”, fără erori în consolă. Nu schimba logica de date: culoarea vine DOAR din `banda`, UI-ul NU recalculează praguri din `scor`.

### 1. Scoate din UI
1. Bannerul „DATE FICTIVE · rețea demonstrativă” de sus (și orice alt banner permanent de date fictive pe hartă).
2. Comutatorul de scenariu și orice mențiune a scenariului „extrem” (eticheta „Scenariu: extrem”, `?scenariu=extrem`, regulile care dezactivau raportul în extrem).
3. Butoanele „Generează traseu ultima oră”, „Cerere racordare casă” și „Fire mutate” care funcționează prin clic pe hartă; scoate și modul „clic pe hartă pentru locație” (cursorul special, marcajul de clic). Scoate secțiunea „Traseu simulat” și câmpurile `zgomot`, `durata`, `acoperire`, `decalaj`; nu mai trimite `trace_params` și `locatie` în `POST /rapoarte`.
4. Etichetele „in_model”, „Predicție AI”, „generat de model”, „Generat de model”, „Rețea de start” și orice cod brut (`predictie`, `de_verificat`, `in_model`, `scos_din_uz`, `retea_start`, `generat_model`, `ai_cli`, `traseu_pe_strazi` etc.) afișat utilizatorului. În locul lor: „GIS” / „Din raport” din `eticheta_origine`, textul benzii (vezi 4) și insigna ✓ (vezi 5).

### 2. Structura ecranului hărții (stil GIS)
- **Stânga: panou „Straturi”** (pliabil, ținte ≥ 32 px) cu casete de bifat, toate pornite implicit, în ordinea:
  1. Rețea GIS (elemente cu `eticheta_origine` = „GIS”);
  2. Din rapoarte (`eticheta_origine` = „Din raport”);
  3. Predicții (`predictie` != null);
  4. Elemente de verificat (elementele cu `banda` = `portocaliu` sau `rosu`);
  5. Zona prototipului (cercul din `zona`, subțire, punctat gri, cu etichetă „Zona prototipului”; ia locul vechiului comutator „Arată zona”);
  6. Străzi: comutator fundal între „OSM standard” și „Gri deschis”.

  Un strat debifat ascunde elementele respective; un element care aparține la două straturi se vede dacă cel puțin unul e bifat.
  **Sub Straturi: „Legendă”** din `GET /legenda`: câte o linie pe fiecare `benzi[]` (pătrat cu `culoare` + `text`; `de_la` în tooltip), `linii[]` (mostră de linie în stilul `stil` + `text`) și `insigne[]` (`cod` + `text`). Nu hardcoda texte sau culori ale legendei; dacă apelul eșuează, „Legenda indisponibilă”.
- **Sus: bară de unelte** cu: câmp de căutare (ID de element sau nume de stradă; Enter caută în elementele încărcate din `GET /retea`, potrivire pe `element_id` și, dacă proprietățile au nume de stradă, pe acesta; zboară la rezultat și deschide Identificare; niciun rezultat = „Niciun rezultat”), butonul „Încadrează rețeaua” (fitBounds pe toate elementele vizibile), grupul de butoane de echipă existent (Mentenanță, Investiții, Racordări, exact cum sunt acum; NU le schimba, se refac în P2) și butonul „Pagina de start” (link spre `/`; dacă ruta nu există încă, o deschide goală cu textul „În curând”).
- **Dreapta: panou „Identificare”** (apare la clic pe un element, se închide cu Esc sau cu X). Tabel cu rândurile:
  - ID (`element_id`);
  - Tip (`tip_element`: nod = „Nod”, tronson = „Tronson”, post_transformare = „Post de transformare”);
  - Sursă (`eticheta_origine`: „GIS” / „Din raport”);
  - Acuratețe: bară orizontală umplută proporțional cu `scor`, colorată cu culoarea benzii (din `GET /legenda`, cheia `banda`), plus textul benzii (`text` din legendă) și valoarea cu 2 zecimale;
  - Cum a fost localizat (`sursa_locatie`: `coordonate` = „Coordonate”, `clic` = „Clic pe hartă”, `geocodare` = „Din adresă”, `trace` = „Din traseu”, `operator` = „Operator”, `gis` = „GIS”, orice altă valoare afișată ca atare, `null` = „—”);
  - Ultima verificare (`ultima_verificare`, format zz.ll.aaaa, sau „—”);
  - Verificat de om: dacă `verificat_om` = true, „Da, la <`verificat_om_data`>” cu insigna ✓; altfel „Nu”.
  Sub tabel: secțiunea „De ce?” (apel `GET /element/{id}`, lista `motive[]` cu data, textul și efectul pe scor, cea mai recentă prima; lipsă = „—”) și butonul **„Marchează verificat de om”**: `POST {API_BASE}/element/{id}/verificare` cu corpul `{}` (opțional `{"motiv": "Verificat în teren"}`), apoi reîncarcă `GET /retea` (la data activă din timeline) și `GET /element/{id}`; în timpul cererii butonul e dezactivat cu „Se trimite…”; la eroare, mesaj roșu „Nu s-a putut marca”. Dacă `verificat_om` e deja true, butonul e dezactivat cu textul „Deja verificat de om”.
- **Jos: bara de stare a hărții** cu scara grafică (metri/kilometri), coordonatele cursorului (`lat, lon` cu 5 zecimale, „—” când cursorul e în afara hărții) și, în continuare, timeline-ul existent (NU îl schimba).

### 3. Culori și stiluri de linie (doar din `banda`)
- Culoarea elementului = culoarea benzii `properties.banda` (verde, galben, portocaliu, roșu), luată din `GET /legenda` (`benzi[].culoare`). Interzis: orice comparare a lui `scor` cu praguri în cod.
- Stil de linie pentru tronsoane: **plină** = element în rețea (`predictie` null și nu e demontat); **punctată** (`stroke-dasharray`) = predicție (`predictie` != null); **gri punctat** (gri fix, `#6b7280`, mai subțire) = demontat probabil (nivelul `scos_din_uz`). Noduri și posturi: punct plin; la predicție, punct cu contur punctat; demontat = gri.
- **Insigna ✓** (cerc mic verde închis cu ✓ alb, colț dreapta-sus pe marcaj și lângă ID în Identificare și în tooltip) pe elementele cu `verificat_om` = true.
- Tooltip la hover: ID, tip, sursă („GIS”/„Din raport”), textul benzii (de ex. „Galben: acuratețe medie”, din legendă), scor cu 2 zecimale, „✓ Verificat de om” dacă e cazul.
- Halo-ul verde/galben vechi, contururile portocalii ale timeline-ului și evidențierea elementelor atinse rămân.

### 4. Accesibilitate (WCAG 2.1 AA)
- Culoarea nu e singurul semnal: textul benzii apare în tooltip și în Identificare; predicțiile se disting prin stilul de linie (punctat), demontatul prin gri punctat.
- Contrast ≥ 4,5:1 pe tot textul (inclusiv pe panouri și pe bara de jos); text ≥ 14 px peste tot.
- Navigare completă din tastatură: Tab trece prin bara de unelte, Straturi, hartă (elementele focusabile cu Enter = Identificare), Identificare și „Marchează verificat de om”; Esc închide Identificare și panourile pliabile; focus vizibil (contur ≥ 2 px, contrast bun).
- `aria-label` în română pe toate butoanele cu iconițe (Încadrează rețeaua, Închide, Pagina de start etc.); casetele din Straturi au etichete asociate; Identificare are `role="complementary"` și `aria-label="Identificare element"`.
- `prefers-reduced-motion: reduce` oprește zborul animat (trecere instant), pulsațiile și tranzițiile.
- Ținte de clic ≥ 32 × 32 px (butoane, casete, elementele din legendă interactive).

### NU SCHIMBA
- **Timeline-ul derulabil** (panoul vertical „Evenimente”, derularea care mută harta după 150 ms, cache-ul pe dată, „De ce?” pe intrare, contururile portocalii pe `elemente_atinse`): rămâne exact cum este; se mută orizontal abia în P3.
- Butoanele de echipă (Mentenanță, Investiții, Racordări) și panourile lor, formularul „adaugă raport nou”, „Show pipeline” cu pașii lui (Extracție, Geocodare, Potrivire etc.), etichetele „AI (live)” / „AI (cache)” / „Regex (simplificat)”, bannerul roșu „Eronat în cadrul prototipului”, insigna „predicție slabă / treapta N”: toate rămân până la P2.
- Setarea `API_BASE` și parametrul `?api=`, logica `POST /rapoarte`, `POST /predictii/{id}/decizie`, `GET /evenimente`.
- Nu adăuga pagini noi, nu adăuga dependențe, nu publica.

---

## Verificare după (de făcut de Claudiu, prin tunel: `backend/api/demo_start.sh` + link cu `?api=<tunel>`)
Înainte de trimitere, pe API:
- [ ] `curl $TUNEL/legenda` întoarce `benzi` (4), `linii`, `insigne`.
- [ ] `curl "$TUNEL/retea"` — pe fiecare feature: `banda`, `verificat_om`, `eticheta_origine`, `sursa_locatie`, `t0` prezente; `zona` la rădăcină.
- [ ] `curl -X POST $TUNEL/element/<id>/verificare -d '{}' -H 'content-type: application/json'` dă 200 (apoi `./demo_start.sh --reset-model`).

După aplicarea promptului, în preview:
- [ ] Sus nu mai e bannerul „DATE FICTIVE”; nu există comutator de scenariu, nici „extrem”.
- [ ] Nu mai există butoanele „Generează traseu ultima oră”, „Cerere racordare casă”, „Fire mutate”; clic pe hartă doar selectează un element; formularul de raport nu mai are „Traseu simulat”.
- [ ] Nicăieri nu apar „in_model”, „Predicție AI”, „generat de model”, `predictie`, `de_verificat` (căutare vizuală în tooltip, Identificare, legendă, timeline).
- [ ] Panoul Straturi are 6 bife; debifând „Predicții” dispar liniile punctate, debifând „Rețea GIS” dispar elementele „GIS”; „Zona prototipului” ascunde cercul; comutatorul de fundal schimbă între OSM și gri.
- [ ] Legenda de sub Straturi are 4 benzi, stilurile de linie și insigna ✓, cu textele din `GET /legenda`.
- [ ] Căutare „SIM-021” (sau alt ID real) zboară la element și deschide Identificare; un text fără rezultat dă „Niciun rezultat”; „Încadrează rețeaua” revine pe toată rețeaua.
- [ ] Clic pe un element: Identificare arată ID, tip, sursă „GIS”/„Din raport”, bară colorată cu textul benzii, cum a fost localizat, ultima verificare, „Verificat de om: Nu”; câmpurile `null` arată „—”; Esc îl închide.
- [ ] „Marchează verificat de om” pe un element: apare ✓ pe hartă, bara urcă (scor 1,00, banda verde), „Da, la <data>”; butonul devine „Deja verificat de om”. Pe o predicție: devine linie plină (aplicată).
- [ ] Culoarea unui element schimbat de un eveniment din timeline se schimbă odată cu `banda` din API (nu rămâne culoarea veche); în codul sursă nu există praguri numerice pe `scor`.
- [ ] Linie plină / punctată / gri punctat vizibile pe hartă (rețea, predicție, demontat).
- [ ] Jos: scara grafică și coordonatele cursorului se actualizează la mișcarea mouse-ului; timeline-ul derulabil funcționează ca înainte (derulare mută harta, contur portocaliu pe atinse).
- [ ] Butoanele de echipă și „Show pipeline” sunt neschimbate.
- [ ] Tastatură: Tab parcurge toate; focus vizibil; Esc închide Identificare; `prefers-reduced-motion` (DevTools) oprește animațiile; ținte ≥ 32 px; text ≥ 14 px; zero erori în consolă la câmpuri lipsă.
- [ ] Notat în `frontend/README.md`: mesajul trimis, creditele consumate, commit-ul Lovable.
