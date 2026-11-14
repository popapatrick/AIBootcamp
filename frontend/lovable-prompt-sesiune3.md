# Prompt Lovable sesiunea 3 (grupat): origine, predicție slabă, eronat în prototip, zonă, trace simulat, geocodare

> **TRIMIS 2026-11-15, la cererea omului** (după `logic-v1`). Textul trimis are 3 corecturi față de cel de mai jos, aflate în C3: (6) câmpurile sunt `trace_params: {zgomot_m, durata_oprire_min, acoperire, decalaj_m, dezactivat}`, iar sursa traseului e în `pasi[pas=trace].rezultat.sursa`, nu în `detalii.trace_sursa`; (7) geocodarea vine ca pas separat `pas = geocodare` în `pasi`, după `extractie`; (8) eticheta pentru `ai_cli` e „AI (live)".

- **Dependențe:** contract `3517dfa` (sesiunea 3) pe main; API care întoarce `origine`, `predictie.slaba/treapta`, `eronat_prototip`, `zona`, `detalii.geocodare`, `detalii.trace_params/trace_sursa`.
- **Cost estimat:** ~3-5 credite (un singur mesaj; dacă Lovable se încurcă, împarte pe punctele 1-3 / 4-7).
- **Verificare după:** elementele din rețeaua de start au „Rețea de start", cele prezise „Generat de model" cu contur punctat; un punct în afara zonei arată mesajul „eronat"; cercul zonei apare pe hartă; formularul de raport are 4 parametri trace marcați „simulat"; „Show pipeline" are pasul „Geocodare"; nicăieri nu mai scrie „Predicție AI".

---

## PROMPT (de lipit în Lovable)

Schimbări doar de afișare și formular (frontend, română, date FICTIVE). Orice câmp lipsă -> „—", fără erori în consolă. Nu schimba nimic altceva.

1. **Origine** (tooltip pe hartă și panoul „De ce?"): după `origine` al elementului: `retea_start` -> „Rețea de start"; `generat_model` -> „Generat de model". Separat de „Confirmat de om" (`confirmat_de` = `om`), care rămâne pe rând propriu și poate apărea alături.
2. **Contur punctat** pe hartă pentru elementele cu `origine` = `generat_model` (linii: `stroke-dasharray`; puncte: contur punctat); `retea_start` rămâne cu linie continuă.
3. **Predicție slabă**: dacă `predictie.slaba` = true, în panou și tooltip: insignă „predicție slabă" (portocaliu) și, dacă există `predictie.treapta` (1-4), „treapta N" lângă ea, cu tooltip „Treapta = cât de departe s-a căutat racordarea; peste 1 = rază extinsă, încredere mai mică". Predicția normală (`slaba` fals) nu are insignă.
4. **Eronat în prototip**: dacă răspunsul `POST /rapoarte` are `eronat_prototip` = true (decizie `neaplicat`, semnal `in_afara_zonei_prototip`), arată în rezultat un banner roșu: „Eronat în cadrul prototipului: punctul e în afara zonei rețelei demonstrative și nu a fost aplicat." Fără buton de aplicare. Nu schimba restul rezultatului.
5. **Cercul zonei**: `GET /retea` întoarce `zona` = `{centru:{lat,lon}, raza_m}`. Desenează pe hartă un cerc subțire punctat gri (centru, rază în metri), cu etichetă „Zona prototipului" și un comutator „Arată zona" (implicit pornit).
6. **Parametri trace în formularul de raport** (secțiune pliabilă „Traseu simulat"): câmpuri numerice `zgomot` (m), `durata` (min), `acoperire` (0-1), `decalaj` (m), trimise în `detalii.trace_params`; valori implicite goale (backend-ul folosește valorile din reglaje). Lângă secțiune, eticheta „simulat" (gri); când răspunsul are `detalii.trace_sursa` = `simulat`, arată „Traseu: simulat", iar `real` -> „Traseu: real".
7. **„Show pipeline"**: pas nou „Geocodare" între Extracție și Potrivire, doar dacă există `detalii.geocodare` (în pasul extracției sau în Event). Arată: `lat`, `lon`, `precizie_m`, `metoda` (`osm_cache` = „cache OSM", `ai_estimare` = „estimare AI din străzi cunoscute", `trace` = „din traseu", `necunoscut` = „necunoscut", `in_afara_zonei` = „în afara zonei"), `acuratete` ca procent, `motiv`. Dacă `metoda` = `necunoscut` sau `in_afara_zonei`, pasul e marcat „fără poziție".
8. **Scoate „Predicție AI"** din tot UI-ul (etichete, tooltip-uri, legendă, texte ajutătoare). Înlocuiește cu „Predicție" (+ metoda, ca acum). AI apare doar la standardizarea textului (etichetele din pasul Extracție: „AI (cache)" / „AI (API)" / „Regex (simplificat)"). Tooltip pe „Predicție": „Poziția prezisă vine din scor și străzile OSM; AI face doar standardizarea textului. Nu e aplicată în model până la confirmare."
