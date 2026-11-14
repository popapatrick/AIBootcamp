Modifică aplicația existentă (frontend, fără DB/auth, în română). Date FICTIVE. Datele vin doar din API (`API_BASE`). Fă ambele părți într-o singură trecere, peste ce există deja (haloul, legenda și Show pipeline din promptul anterior rămân).

### Corecturi (contract nou, au prioritate peste restul textului)
1. Haloul verde se ia din `properties.verificat_recent` (bool dat de motor), NU din calculul de 45 de zile pe `ultima_verificare`. `confirmat_de` = `om` = simbol plin cu marcaj „✓ om".
2. `nivel` = `scos_din_uz`: gri deschis, element tăiat/transparent.
3. Intrările din `GET /evenimente` au acum `tip` și `eticheta` (`mutare_fire` | `demontat` | `val_apeluri` | `racordare` | `decizie_om` | tipul evenimentului). Evidențierile din timeline (ramură, demontat, val de apeluri, decizii) se fac după `eticheta`, NU după `event_id` EV-X01..EV-X10 (ID-urile rămân doar informative).
4. În Show pipeline poate apărea pasul `trace` înaintea `potrivire`, iar `potrivire` poate avea `status: "zona"` (mutare fir): afișează-le lizibil (nume pas, status, rezultat pe scurt), fără JSON brut.
5. Decizia: 409 deja decis, 404 necunoscut, 422 invalidă, 501 fără motor (mesajele din secțiunea C4).

### NU SCHIMBA
- Scala continuă/KMZ și comutatorul „Colorare", timeline-ul cu Play și selectarea datei, panoul „De ce?" (`GET /element/{id}`), lista „Evenimente".
- `?api=<URL>` și „Setări → API_BASE"; bannerul „DATE FICTIVE"; `mod` din `/health`.
- Cele 3 exemple demo, tab-ul „Proces raport", „Show pipeline", „Rețea actualizată la".
- Haloul de stare: verde = `verificat_recent` (vezi corecturile) SAU `confirmat_de` = `om`; galben = `in_model` neatins; punctat = `predictie`; roșu = `de_verificat`; gri deschis = `scos_din_uz`. Nu reface logica, doar o refolosești.

### PARTEA 1 (C4): decizia omului pe o predicție
În panoul „De ce?", când elementul selectat are `properties.nivel` = `predictie` (hartă sau listă), arată sub scor și metodă (`properties.predictie.metoda`, scor) un bloc „Verificare în teren":
1. Câmp text opțional „Motiv (opțional)".
2. Butoane „Acceptă (verificat în teren)" și „Respinge".
3. Apăsare: `POST {API_BASE}/predictii/{id}/decizie`, unde `{id}` = id-ul elementului predicție (`properties.id`, același cu cel din `GET /element/{id}`), cu corpul JSON exact:
   `{"decizie": "accepta"}` sau `{"decizie": "respinge"}`; adaugă `"motiv": "<text>"` doar dacă a fost completat; adaugă `"data": "YYYY-MM-DD"` (data selectată pe timeline) doar dacă timeline-ul are o dată selectată, altfel omite-o (serverul ia data de azi). Fără alte câmpuri.
4. Pe durata cererii, ambele butoane dezactivate. Nu apare bloc pentru elemente care nu sunt `predictie`.
5. La succes (200, răspuns StepTrace): mesaj „Decizie înregistrată: <acceptată | respinsă>", reîncarcă `GET /retea` (data curentă) și `GET /evenimente`, redeschide „De ce?" pe același id. Dacă `schimbari[]` există, arată-l în același tabel „Schimbări în rețea" ca la Show pipeline (`element_id`, `ce`, `scor_inainte` → `scor_dupa`, `de_ce`); dacă lipsește: „—".
6. Erori, afișate sub butoane în română (mesajul serverului vine în `detail`, ca text; arată-l ca detaliu mic sub mesajul de mai jos):
   - 409: „Această predicție are deja o decizie (acceptată sau respinsă)."
   - 404: „Predicția nu mai există (necunoscută)."
   - 400 sau 422 (tratate la fel): „Decizie invalidă: verifică valorile trimise."
   - 501: „Decizia nu e disponibilă încă în motor."
   - altă eroare / rețea căzută: „API indisponibil, setează API_BASE".
   După 409 reîncarcă oricum harta, ca să se vadă starea reală.
7. **Marcaj „✓ om":** elementele cu `properties.confirmat_de` = `om` arată „✓ om" în tooltip, în panoul „De ce?" (lângă scor, ca insignă verde) și mic lângă nod pe hartă (de la zoom 15). Un element confirmat de om nu mai are butoanele de decizie. `confirmat_de` lipsă sau altă valoare: nu arăta nimic.
8. **Timeline:** intrările din `GET /evenimente` au câmpul `decizie`; adaugă două badge-uri noi: `aplicat` (verde, „acceptat de om" când intrarea e o decizie a omului, altfel „aplicat") și `respins` (gri-roșu, „predicție respinsă"). Restul valorilor (`adaugat`, `predictie`, `conflict`, `de_verificat`, `scor_actualizat`, `fara_efect`, `neaplicat`) rămân cum sunt; o valoare necunoscută se afișează ca text simplu.

### PARTEA 2 (C8): scenariul extrem
1. În bara de sus (lângă selectorul de dată/Play) adaugă un comutator cu două butoane: „Încarcă rețeaua cu evenimente (scenariu extrem)" și „Scenariu normal". Starea activă se vede clar, plus o etichetă „Scenariu: extrem" când e pornit. Implicit: normal.
2. În scenariul extrem toate cererile pentru hartă și timeline folosesc `?scenariu=extrem`: `GET {API_BASE}/retea?scenariu=extrem&data=<dată>` și `GET {API_BASE}/evenimente?scenariu=extrem`. Revenire la „Scenariu normal": aceleași cereri fără parametru. Starea scenariului se păstrează la schimbarea datei și la Play. `GET /element/{id}` și `POST /predictii/.../decizie` NU primesc `scenariu` (rămân neschimbate). Raportul nou și decizia în scenariul extrem: dezactivează „Trimite raport" și butoanele „Acceptă/Respinge" cu textul „Disponibil doar în scenariul normal" (scenariul extrem e doar de citit). La schimbare de scenariu: reîncarcă harta și timeline-ul, mută slider-ul la prima dată, oprește Play.
3. Eroare 404 la încărcare (fișierul scenariului lipsește): mesaj „Scenariul extrem nu e disponibil pe server", rămâi pe scenariul normal.
4. **Intervalul de date:** în scenariul extrem slider-ul acoperă de la prima la ultima dată din `/evenimente?scenariu=extrem` (evenimentele merg cam din septembrie până la 2026-11-12; ia limitele din date, nu le hardcoda).
5. **Play întreg sub 45 de secunde** în orice scenariu: viteza se calculează din numărul de pași (zile/evenimente) ca durata totală să fie ≤ 40 s; nu un pas fix. Afișează timpul rămas sau o bară de progres. Butonul Play/Pauză rămâne.
6. **Halou verde/galben pe data selectată** (aplicat pe fiecare cadru al timeline-ului): la jumătatea slider-ului elementele atinse de evenimentele de până atunci sunt verzi, restul galbene. Adaugă în legendă la „Stare" textul „verde = verificat/atins până la data aleasă, galben = neatins de niciun eveniment".
7. **Cazuri evidențiate pe timeline** (în scenariul extrem; marcaje mici pe axa timeline-ului și în lista de evenimente, cu clic = mută slider-ul la acea dată și zoom pe `elemente_atinse`; datele vin din `GET /evenimente`, câmpurile `data`, `eticheta`, `tip`, `decizie`, `rezumat`, `elemente_atinse`):
   - **Ramură pe etape:** intrările cu `eticheta` = `racordare` (și orice intrare al cărei `rezumat` menționează nodul nou `7900101`), unite printr-o bandă „Ramură pe etape", cu pașii în ordine. Pe hartă, ramura (nodul `7900101` și tronsoanele `NOU-7900101-*`) trece de la punctat (`nivel` = `predictie`) la plin (`in_model`) pe măsură ce slider-ul avansează; la trecere, o scurtă pulsație.
   - **Segment demontat:** intrările cu `eticheta` = `demontat`: bandă „Segment demontat". Când `properties.nivel` = `scos_din_uz` (la data selectată), tronsonul se desenează gri deschis, transparent, cu eticheta „scos din uz"; până atunci rămâne în model cu halou roșu/„de verificat" și „De ce?" arată semnalul negativ. Nu presupune în cod un ID fix: marcajul se bazează pe `nivel` = `scos_din_uz`.
   - **Val de apeluri:** intrările cu `eticheta` = `val_apeluri`: bandă „Val de apeluri (4 în 4 zile)" cu numărătoarea apelurilor până la data aleasă; pe hartă, zona din jurul lor (aprox. 44.2765, 26.0633, tronsoanele `A-T-004`/`A-T-005`) se evidențiază cu un cerc subțire; scorul elementului scade vizibil pe măsură ce apelurile se acumulează (din `scor` în `GET /retea` la fiecare dată).
   - Intrările cu `eticheta` = `mutare_fire` și `decizie_om` primesc un marcaj mic cu eticheta lor. Dacă `eticheta` lipsește (alt set de date), nu afișa benzile și nu da eroare; timeline-ul rămâne cel normal.

### Reguli generale
- Tot textul în română. Nu hardcoda URL-uri de API, tunel sau chei; doar `API_BASE`.
- Orice câmp absent din răspuns (`confirmat_de`, `schimbari`, `predictie`, `scor`, `verificat_recent`, `elemente_atinse`, `rezumat`, `eticheta`) => afișează „—", niciodată eroare în consolă sau ecran alb.
- Nu adăuga autentificare, bază de date sau alte pagini în afară de cele descrise.
