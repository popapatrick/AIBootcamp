# Prompturi Lovable (C)

Ordinea de trimitere. **4 prompturi** (≈ 4 credite + eventuale corecturi). **Toate 4 trimise 2026-11-14 (total ≈ 7,0 credite).** Nu se publică fără confirmarea omului.
Backend: `API_BASE` = URL-ul tunelului HTTPS către FastAPI (ex. `https://xxxx.trycloudflare.com`). Contract: `contracts/api.openapi.yaml`. Referință vizuală funcțională: `frontend/plan-b/index.html` (servit la `/ui/`).

## Prompt 1: schelet + hartă
**Trimis 2026-11-14, 1,4 credite.** Adăugat la trimitere: fără DB/auth (doar frontend); mesaj „API indisponibil, setează API_BASE” dacă API-ul nu răspunde; `mod` din `/health` afișat într-un colț.

> Construiește o aplicație web în limba română: „Model rețea JT care se actualizează singur". Sus, permanent, un banner galben „DATE FICTIVE · rețea demonstrativă". O variabilă de configurare API_BASE (editabilă dintr-un câmp mic în setări, salvată în localStorage). Pagina principală e o hartă Leaflet (fundal OpenStreetMap) care încarcă `GET {API_BASE}/retea?data=YYYY-MM-DD` (GeoJSON). Fiecare feature are în properties: element_id, tip_element (nod/tronson/post_transformare), nivel (in_model/predictie/de_verificat), scor 0–1, motive [{text, efect, eveniment, data}], predictie. Culori: scor ≥ 0,75 verde, 0,4–0,75 galben, < 0,4 sau nivel de_verificat roșu; nivel predictie = violet cu linie PUNCTATĂ (dashArray), puncte cu contur punctat. Liniile = tronsoane, punctele = noduri (rază mică pentru in_model, mai mare pentru celelalte). Legendă vizibilă. Zoom automat pe rețea la prima încărcare.

## Prompt 2: timeline cu play
**Trimis 2026-11-14, 0,9 credite.** Adăugat la trimitere: lista evenimentelor include `decizie`; listă goală → un singur punct (azi); nu pornește cerere nouă cât timp cea anterioară e în curs; sliderul înlocuiește câmpul de dată.

> Adaugă jos o bară de timeline: încarcă `GET {API_BASE}/evenimente` (listă [{data, event_id, rezumat, elemente_atinse}], sortată). Slider zi cu zi între prima și ultima dată, eticheta datei curente, buton ▶ Play / ⏸ Pauză care parcurge toată perioada (~3 luni) în aproximativ 40 de secunde, reîncărcând harta cu `?data=` la fiecare pas. Lângă slider arată ultimul eveniment până la data curentă. În panoul din dreapta, lista evenimentelor, cu cele trecute evidențiate.

## Prompt 3: panoul „De ce?"
**Trimis 2026-11-14, 1,9 credite.** Adăugat la trimitere: panoul din dreapta are taburi „De ce?” și „Evenimente”; predicția arată și `propunere`, `scor_propunere`; grafic cu praguri 0,4 și 0,75; elementul selectat rămâne evidențiat.

> La click pe un element de pe hartă, încarcă `GET {API_BASE}/element/{id}` și arată în panoul din dreapta „De ce?": id, tip, insignă colorată cu nivelul, scorul mare, „valid de la", „ultima verificare", apoi lista de motive (efect cu semn, verde pozitiv / roșu negativ, text, eveniment sursă, dată), detaliile predicției dacă există (metoda, urmează strada) și istoricul [{data, nivel, scor}] ca mic grafic de scor în timp.

## Prompt 4: ecranul procesului + raport nou
**Trimis 2026-11-14, 2,8 credite.** Adăugat la trimitere: răspunsul include `decizie`; câmpuri cheie per pas (extracție: tip, status, referinta, campuri_lipsa; potrivire: status, element_id, metoda, calitate, motiv; scor: scor_propunere, factori, nivel, decizie); 3 exemple clicabile (A-T-002 investiții; stâlp nou 44.2849717, 26.0601908 mentenanță; apel client str. Florilor nr. 12, C-10234).

> Adaugă un al doilea ecran „Proces raport" (tab în header). Formular: sursă (mentenanță, investiții, racordări, apel client → valorile mentenanta, investitii, racordari, apel_client), dată opțională, text mare. Butonul „Procesează" trimite `POST {API_BASE}/rapoarte` cu {text, sursa, data}. Răspunsul are `pasi`: [{nume: extractie|potrivire|predictie|scor, rezultat, incredere, motive?}] și `modificari`: [ElementState]. Afișează pașii ca un flux vertical de carduri cu săgeți: „0. Text original → 1. Text → structură → 2. Potrivire pe rețea → 3. Predicție → 4. Scor și decizie", fiecare cu încrederea și rezultatul formatat lizibil (câmpuri cheie evidențiate, JSON-ul complet într-un detaliu pliabil). La final un card „Propunere" cu element_id, nivel și scor și un buton „Vezi pe hartă" care deschide harta, reîncarcă timeline-ul și centrează pe element.
