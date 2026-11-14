# Draft prompt Lovable: timeline derulabil (ciornă de la Victor/B pentru Claudiu)

Ciornă, NETRIMISĂ. Claudiu o verifică față de ce are acum în Lovable (C8: slider, Play, comutator scenariu, halou verde/galben, marcaje pe cazuri) și o mută în `frontend/` ca prompt. Decide omul când se trimite. Cost estimat 4-6 credite (un singur mesaj; dacă se încurcă, împarte: 1-3 / 4-7). Dependențe: contract `648f588` (`schimbari`, `pasi`, `eronat_prototip` pe intrările din `GET /evenimente`) și API-ul care le trece neatinse (sarcina 2.1 din `openspec/changes/timeline-derulabil/tasks.md`).

## Ce rămâne neschimbat din C8 (nu rescrie)
Comutatorul „Scenariu extrem / normal" și regulile lui (`?scenariu=extrem`, dezactivarea raportului și a Accept/Respinge în extrem), badge-urile de `decizie`, marcajele pe cazuri după `eticheta` (ramură, mutare_fire, decizie_om, demontat, val de apeluri), „De ce?" pe element (`GET /element/{id}`), halou verde/galben, legenda.

## PROMPT (de lipit)

Schimbare doar în timeline (frontend, română, date FICTIVE). Orice câmp lipsă -> „—", fără erori în consolă. Nu schimba nimic altceva.

1. **Scoate butonul Play, bara de progres și slider-ul de dată.** Rămân: comutatorul de scenariu și eticheta „Scenariu: extrem", plus un indicator mic „Data: YYYY-MM-DD" (data evenimentului activ) deasupra hărții.
2. **Panou vertical lateral „Evenimente"** (în dreapta hărții, înălțime = a hărții, scroll vertical propriu), cu toate intrările din `GET /evenimente` (cu `?scenariu=extrem` în scenariul extrem), în ordine cronologică. Fiecare intrare (card compact): data, insigna cu `eticheta` (mutare fire, racordare, decizie om, demontat, val de apeluri; altfel `tip`), insigna de `decizie` (culorile existente: adaugat/aplicat verde, predicție albastru punctat, de_verificat galben, neaplicat gri, respins gri-roșu; dacă `eronat_prototip` = true, insigna roșie „eronat în prototip"), `rezumat` pe un rând și, din `schimbari[]`, primele 3 elemente ca „<element_id>: <scor_inainte> → <scor_dupa>" cu „+N" pentru restul (valoare lipsă = „—").
3. **Derularea mută harta automat.** Intrarea care ocupă centrul panoului devine **activă** (fundal evidențiat, IntersectionObserver). După 150 ms fără schimbare a intrării active: `GET {API_BASE}/retea?data=<data intrării>` (plus `&scenariu=extrem` în extrem), harta se redesenează pe acea stare; ține un cache pe (scenariu, dată) ca să nu ceri aceeași dată de mai multe ori. Mai multe intrări în aceeași zi: aceeași hartă, dar evidențierea de la punctul 4 diferă. La schimbarea scenariului: reîncarcă lista, derulează la prima intrare. Pornește pe ultima intrare. Clic pe o intrare o face activă și derulează panoul la ea; săgețile sus/jos mută activa cu o intrare când panoul are focus.
4. **Evidențiază pe hartă elementele atinse** de intrarea activă (`elemente_atinse`): contur gros portocaliu (linii și puncte) peste stilul normal, cu o scurtă pulsație la schimbarea intrării; restul hărții neschimbat. Halo-ul verde/galben din C8 se calculează acum față de data intrării active, nu a slider-ului. Cazurile evidențiate (ramura pe etape, mutare_fire, decizie_om) rămân marcate pe intrări prin `eticheta`, fără axa veche.
5. **„De ce?" la clic pe intrare:** deschide, sub carduri sau într-un panou lateral, pașii din `pasi[]` ai intrării (fără apel nou): pentru fiecare pas `nume` (Extracție, Geocodare, Trace, Potrivire, Predicție, Scor), `incredere` ca procent, `motive[]` ca listă și `rezultat` pe scurt (cheile principale, nu JSON brut). Dedesubt tabelul „Schimbări în rețea" complet din `schimbari[]` (`element_id`, `ce`, `scor_inainte` → `scor_dupa`, `de_ce`). Un clic pe un `element_id` din tabel face zoom pe el și deschide „De ce?" pentru element (`GET /element/{id}`, ca acum).
6. **După un raport nou** (scenariul normal): reîncarcă `GET /evenimente`, derulează la intrarea nouă și fă-o activă.
7. Performanță: lista de ~70 de intrări se randează o dată (nu la fiecare derulare); doar clasa `activ` se mută.

## Verificare după (de făcut de Claudiu)
Fără Play și fără slider; scenariul extrem arată ~70 de intrări; derulând, data și harta se schimbă după ~150 ms; elementele atinse au contur portocaliu; clic pe o intrare arată pașii și schimbările de scor; un eveniment la 40 km are insigna „eronat în prototip"; `eticheta` lipsă nu dă eroare.

## Observații de compatibilitate (B -> C)
- `GET /evenimente` nu primește `data`; lista e întreagă, harta cere `GET /retea?data=` separat.
- Intrările din aceeași zi au aceeași hartă (snapshot la sfârșitul zilei); diferența se vede doar prin evidențiere.
- Pe scenariul normal (`GET /evenimente` fără parametru) `pasi` e prezent doar pentru evenimentele procesate de motorul real; pe stub/fallback poate lipsi, deci „—".
