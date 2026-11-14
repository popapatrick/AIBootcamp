# Prompt Lovable: locația operatorului la cererea de racordare + text tabletă (sesiunea 2)

- **Dependențe:** API cu `GET /locatie-operator-demo?text=` și `locatie_operator` în `POST /rapoarte` (contract 1af15c6, cod a307c33, doc `docs/etapa-17-locatie-operator-racordare.md`).
- **Cost estimat:** ~2-3 credite.
- **Verificare după:** în „Cerere racordare casă", fără clic, scrii „casă pe Strada Liviu Rebreanu" și apeși „Folosește locația operatorului (simulată)": apare un punct „operator (simulat) ±40 m" cu cercul de precizie; „Trimite" dă lanț punctat cu „sursa locației: operator simulat". Un text fără stradă cunoscută arată mesajul de eroare și cere clic. Traseul `trace-1` trimis dă pas `trace` și stâlp prezis.

---

## PROMPT (de lipit în Lovable)

Două schimbări mici (frontend, română, date FICTIVE). Nu schimba nimic altceva.

### 1. Cerere racordare casă: „Folosește locația operatorului (simulată)"
În panoul „Cerere racordare casă":
1. Câmpul „Adresă (opțional)" devine „Unde e casa (descrierea operatorului)", text liber (ex. „casă pe Strada Liviu Rebreanu", „Strada X colț cu Strada Y", „cartierul 1 Decembrie").
2. Când NU există clic pe hartă, sub câmp apare butonul **„Folosește locația operatorului (simulată)"** (dezactivat dacă textul e gol). Când există clic, butonul e ascuns (clicul are prioritate).
3. Apăsare: `GET {API_BASE}/locatie-operator-demo?text=<descrierea, URL-encoded>`.
   - **200** -> răspuns `{lat, lon, precizie_m, simulata, strada, motiv, indicii: [{tip, valoare, gasit}], zona}`. Pe hartă: marcaj distinct (siluetă/omuleț sau pin violet) cu eticheta „operator (simulat) ±<precizie_m> m" și un cerc cu raza `precizie_m`; zoom pe el. În panou: „Locație simulată din descriere: <zona>" și lista `indicii` cu ✓ (gasit true) sau ✗ „negăsit" (gasit false). Un nou clic pe hartă înlocuiește locația operatorului (și o șterge).
   - **422** -> `detail` e obiect `{mesaj, indicii}`: arată `mesaj` și lista `indicii` cu ✗, plus „Dă clic pe hartă pentru locație". Nu desena niciun punct.
   - altă eroare / rețea: „API indisponibil, setează API_BASE".
4. Textul cererii precompletat (editabil) folosește descrierea: `Cerere racordare: client nou, casă pe <descriere>` (fără coordonate când locația vine de la operator; cu `la coord <lat>, <lon>` doar când vine din clic, ca acum).
5. „Trimite cererea" cu locația operatorului -> corp `{"text": ..., "sursa": "racordari", "locatie_operator": {"lat": <lat>, "lon": <lon>, "precizie_m": <precizie_m>, "simulata": true, "zona": "<zona>"}}` (+ `data` ca acum). NU trimite `locatie` în acest caz. Cu clic rămâne exact ca acum (`locatie`).
6. În „Show pipeline", la pașii `potrivire` și `predictie`, afișează `sursa_locatie` lizibil: `text` = „din text", `clic` = „din clic pe hartă", `operator_simulat` = „poziția SIMULATĂ a operatorului" (cu insignă violet „simulat"). Lipsă -> „—".
7. În scenariul extrem butonul e dezactivat, ca restul acțiunilor de scriere.

### 2. Traseu ultima oră: textul precompletat al raportului
Textul precompletat al raportului tabletei devine: `Raport tabletă: stâlp nou necartat pe <adresa>, lucrare executată. Am verificat și stâlpii din jur.` (în loc de „control pe <adresa>, lucrare finalizată"). Rămâne editabil. Restul fluxului (corp cu `trace`, fără `locatie`) neschimbat.

### Reguli
- Tot textul în română. Doar `API_BASE`, fără URL-uri sau chei hardcodate.
- Câmp lipsă -> „—", fără erori în consolă. Rulează testele și build-ul.
