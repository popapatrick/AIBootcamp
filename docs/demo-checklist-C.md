# Checklist demo, partea C (API + UI), sesiunea 4

Date FICTIVE. Parcursul complet al echipei: `docs/DEMO.md`; planul: `docs/plan-sesiune-4-prezentare.md` (secțiunile 8-9); API: `docs/etapa-30-api-sesiune4.md`. Prompturile Lovable: `frontend/lovable-prompt-sesiune4-P1.md`, `-P2.md`, `-P3.md` (fiecare are lista lui detaliată de verificare; mai jos e varianta scurtă).

## 1. Pornire
1. `backend/api/demo_start.sh --restart` (uvicorn :8000 + tunel cloudflared). Scriptul tipărește `API: {...}`, `Tunel: https://....trycloudflare.com`, `Link de deschis: <preview>/?api=<tunel>` și `Plan B: http://localhost:8000/ui/`.
2. Chiar înainte de demo: `backend/api/demo_start.sh --reset-model` (model curat, tunelul și URL-ul rămân).
3. Laptopul demo: `claude auth login` o dată (abonament). Nu există cheie API în `.env`.
4. URL-ul tunelului se schimbă la fiecare repornire a tunelului; e și în `/tmp/claude-1000/tunnel.url`. Nu se scrie în repo.

## 2. Verificări curl (`T=<URL tunel>` sau `http://127.0.0.1:8000`)
| Comandă | Rezultat așteptat |
|---|---|
| `curl -s $T/health` | `status: ok`, `extractie_cod: ai_cli` (nu `stub`/`regex`), `motor: real` |
| `curl -s $T/legenda` | `benzi` (4: verde, galben, portocaliu, roșu, cu `culoare`, `text`), `linii` (plină, punctată, gri punctat), `insigne` |
| `curl -s $T/retea` | GeoJSON ~530 elemente; pe feature `banda`, `verificat_om`, `eticheta_origine` („GIS”/„Din raport”), `sursa_locatie`, `t0`; `zona` la rădăcină (raza 3000 m) |
| `curl -s $T/evenimente` | ~55 intrări 1 aug.-14 nov.; fiecare cu `text_original`, `echipa`, `standardizare`, `focus`, `banda_inainte`, `banda_dupa` |
| `curl -s $T/demo/exemple` | 4 carduri `intro-1..intro-4` cu `id, titlu, descriere, sursa, text, data_moment, focus` |
| `curl -s "$T/exemple?sursa=mentenanta"` (și `investitii`, `racordari`) | lista de texte (5/echipă) cu `titlu`, `text`, fără `asteptat` |
| `curl -s -o /dev/null -w '%{http_code}' "$T/exemple?sursa=apel_client"` | `422` |
| `curl -s -o /dev/null -w '%{http_code}' $T/trasee-demo` | `404` (scos) |
| `curl -s -X POST $T/rapoarte -H 'content-type: application/json' -d '{"text":"Stâlp căzut lângă nr. 15 pe Strada Viilor, cablul atârnă pe trotuar. Nu am coordonate.","sursa":"mentenanta"}'` | `standardizare` (`metoda_eticheta` „AI (cache)”, `campuri`, `lipsa`, `localizare`, `decizie`) și `focus`; pas `cautare_strada` doar după V6 |
| `curl -s -X POST $T/element/<id>/verificare -H 'content-type: application/json' -d '{}'` | `200` cu StepTrace după V5; până atunci `501` „verificare_om nu e încă în motor”; `404` la ID inexistent |
| `curl -s -X POST $T/demo/reset` | `{"status":"ok","evenimente":N}` |

După orice test care scrie în model (POST `/rapoarte`, `/verificare`): `backend/api/demo_start.sh --reset-model` sau `POST /demo/reset`.

## 3. Bife UI după fiecare prompt
Starea promptului: P1 trimis 15 nov.; P2 și P3 netrimise (decide Victor; se trimit pe rând, după verificare prin tunel). Lista completă cu toate bifele e în fișierul fiecărui prompt.

**După P1 (curățenie + hartă GIS + Identificare)**
- [ ] Fără banner „DATE FICTIVE” pe hartă, fără comutator/mențiune de scenariu extrem.
- [ ] Fără butoanele „Generează traseu ultima oră”, „Cerere racordare casă”, „Fire mutate”; fără mod clic pe hartă și fără „Traseu simulat”.
- [ ] Nicăieri `in_model`, „Predicție AI”, „generat de model”, `predictie`, `de_verificat`.
- [ ] Panoul Straturi: 6 bife funcționale; legenda din `GET /legenda`.
- [ ] Căutare (ID sau stradă), „Încadrează rețeaua”, Identificare (ID, tip, sursă, bară de acuratețe cu textul benzii, localizare, „Verificat de om”, „De ce?”); `null` = „—”.
- [ ] „Marchează verificat de om” (cere V5; până atunci eroare 501 afișată curat) pune ✓ și banda verde.
- [ ] Culori din `banda`; linie plină / punctată / gri punctat; scară și coordonate jos.
- [ ] Tastatură, focus vizibil, `prefers-reduced-motion`, zero erori în consolă.

**După P2 (intro + echipe + „Ce a înțeles AI-ul”)**
- [ ] `/` are titlu, 3 carduri „Cum funcționează”, 4 carduri de exemplu, „Intră în hartă”, „Resetează demo” (cu confirmare), subsol „Date fictive, rețea demonstrativă.”.
- [ ] „Vezi pe hartă” pe fiecare din cele 4 carduri: harta la `data_moment`, zbor la `focus` (al evenimentului, dacă cel al cardului e null), puls, pop-up, panoul AI deschis.
- [ ] Exact 3 butoane de echipă (Mentenanță, Investiții, Racordări); panou cu lista din `GET /exemple`, „Alt exemplu”, text editabil.
- [ ] La trimitere: progres în 3 pași, panoul AI se completează pas cu pas, zbor ~1,2 s, puls de 3 ori, max 3 pop-up-uri, timeline la „acum”.
- [ ] Etichete: „AI (cache)” pentru texte din cache, „AI (live)” pentru text nou, „Regex (simplificat)” doar la rezervă.
- [ ] API oprit: „Nu s-a putut trimite raportul”, panoul rămâne utilizabil.

**După P3 (timeline orizontal + căutare pe stradă + analiza hărții)**
- [ ] Timeline orizontal jos, repere de lună, derulabil (roată, trackpad, săgeți); implicit „acum”; „Listă” deschide lista verticală.
- [ ] Puncte cu culoare ȘI formă; selectare = hartă la dată + zbor la `focus` + fișă (dată, echipă, text, câmpuri, decizie, bandă înainte → după, „De ce?”).
- [ ] Eveniment cu `cautare_strada`: bandă pe stradă, cerc de precizie, ancore, candidați cu contur, cel ales plin, fișa cu 3 rânduri.
- [ ] Eveniment cu `analiza_harta`: drum gros punctat pe străzi, alternative gri cu motiv, fișa cu explicație și lungime.
- [ ] Evenimente fără acești pași: nicio vizualizare, nicio eroare.

## 4. Parcurs demo sub 5 minute (cele 4 carduri din `data/reports/demo-intro.json`)
Ordinea din plan (secțiunea 9); pornești cu model curat (`--reset-model`).
1. **Intro `/` (~30 s):** titlul, cele 3 carduri „Cum funcționează”.
2. **Card 2, sens giratoriu (~45 s):** „Vezi pe hartă” (19 sept.): fire mutate, traseul nou apare, cel vechi se scoate. Depinde de V4.
3. **Harta GIS (~30 s):** Straturi, legendă, clic pe un element, Identificare (sursă, acuratețe, „De ce?”).
4. **Card 1 / Mentenanță, accentul (~60 s):** „Stâlp căzut lângă nr. 15 pe Strada Viilor, cablul atârnă pe trotuar. Nu am coordonate.” Se vede panoul AI (standardizare, localizare), căutarea pe stradă cu candidații și alegerea celui mai apropiat. Depinde de V6.
5. **Card 3 / Racordări, casă departe (~45 s):** „Cerere racord, casa din Strada Regina Maria nr. 40, la cca 180 m de ultimul stâlp.” Traseu pe străzi, acuratețe mai mică (galben/portocaliu). Depinde de V3.
6. **Card 4, stâlp înlocuit (~30 s):** aplicat galben pe adresă, apoi „Marchează verificat de om” pe el: ✓, verde 1,00. Depinde de V5.
7. **Timeline (~30 s):** derulare înapoi la 1 aug. și înainte la „acum”.
8. **„Resetează demo” (~10 s):** confirmare, „Demo resetat (N evenimente)”.

## 5. Dacă ceva pică
| Problemă | Ce faci |
|---|---|
| Tunelul sau Lovable nu răspunde | Plan B: `http://localhost:8000/ui/` (Leaflet, fără scenariul extrem). Sau `backend/api/demo_start.sh --restart` pentru un link nou și deschizi din nou |
| Modelul e „murdar” după repetiții | `backend/api/demo_start.sh --reset-model` (tunelul rămâne) sau butonul „Resetează demo” |
| `/health` arată `extractie_cod` ≠ `ai_cli` | `claude auth login` pe laptop, apoi `--restart`. Textele din cache merg oricum (instant) |
| Text nou lent (5-20 s) | Normal cu `ai_cli`; folosește textele din cache (cele 4 carduri și butoanele de echipă) |
| Fundal gri pe hartă | Plăcile OSM cer internet; liniile rămân; comutator „Gri deschis” |
| Ultima soluție | Înregistrarea video de rezervă |

## 6. Dependențe de motor (API le trece neatinse, `null`/„—” până atunci)
- `banda`, `verificat_om`, `sursa_locatie`, `t0` din `/retea` și `banda_inainte`/`banda_dupa` din timeline: `null` până produce B (V1/V2); UI arată „—”, nu inventează culori din scor.
- `POST /element/{id}/verificare`: **501 până la V5**; butonul „Marchează verificat de om” nu merge până atunci.
- Pasul `cautare_strada` (P3, accentul): lipsește până la V6; fără el nu apare vizualizarea pe stradă (doar punctul).
- `analiza_harta` cu `ales.traseu`: V3; fără el, linie fără traseu pe străzi.
- Cele 4 texte „verificat de om” din scenariu nu au `tip: verificare_om` până promptul de extracție știe tipul (V5), iar `events.json` trebuie regenerat din textele noi (B, `genereaza_scenariu.py`).
- Nu trimite P3 dacă `curl $T/evenimente | jq '.[].pasi[].nume' | sort | uniq -c` nu arată `cautare_strada` și `analiza_harta`.

## Ce NU promitem
- Extracția fără `claude auth login` cade pe „Regex (simplificat)”, vizibil în panou.
- Proiectul Lovable e nepublicat; se folosește preview-ul. Publicare doar cu confirmarea lui Victor.

## 8. Ziua demo: stabilitate
- **Laptop:** fără suspendare (setări energie: nu adormi, ecran stins permis) și cu încărcătorul conectat.
- **Tunel:** pornit o singură dată, `backend/api/demo_start.sh --restart`. Nu-l reporni inutil: fiecare tunel nou are alt URL. Dacă linkul moare: `demo_start.sh --tunel-nou`, apoi deschizi din nou cu noul `?api=`.
- **AI:** `claude auth login` o dată; `curl -s $T/health` trebuie să arate `extractie_cod: ai_cli`.
- **Reset:** `POST /demo/reset` (sau butonul „Resetează demo”) înainte de fiecare repetiție și înainte de prezentare.
- **Versiune:** laptopul demo e pe tag-ul `logic-v2`: `git checkout logic-v2`. Fără `git pull` în ziua demo.
- **Lovable:** niciun prompt nou după repetiția finală.
- **Plan B:** `http://localhost:8000/ui/` deschis într-o filă separată.
- **Video de rezervă:** deschis într-o altă filă (cadre: `docs/demo-video-cadre.md`).
