# Etapa 15: regulile noi ale motorului, sesiunea 2 (B)

Date FICTIVE. Acoperă schimbările OpenSpec `mutare-fire-sens-giratoriu` (B5), `timeline-cazuri-extreme` (B6, partea de motor), `locatie-din-trace-tableta` (B7) și `cerere-racordare-predictie` (B8). Cod: `backend/engine/sesiune2.py` (mixin al `GridModel`), apelat din `model.py`. Praguri: `contracts/weights.yaml`.

## Verificare
```bash
.venv/bin/python -m backend.engine.smoke_sesiune2   # așteptat: OK: 22 verificări
```

## Mutare fire (`tip: mutare_fire`)
Intrare: centrul în `detalii.centru` (sau `referinta.coordonate`), raza în `detalii.raza_m` (altfel `mutare_fire.raza_m` = 40 m), `detalii.motiv_mutare`. Elementele (noduri, tronsoane) din rază, cel mult `max_elemente` (25) cele mai apropiate, trec `de_verificat` cu scorul plafonat la `scor_marcat` (0,35); nimic nu se șterge. Nodurile din afara zonei legate de tronsoanele marcate sunt „ancore": între ancore vecine (cel mult 4, în ordine unghiulară) se propun traseuri noi pe străzi OSM (`MUT-<event>-<n>`, metoda `zona_mutata`), ca predicții punctate, neaplicate (scor = media ponderată, calitate 0,6; ×0,8 dacă nu există stradă). Un raport de confirmare ulterior readuce elementul în model prin regula normală; traseul propus se poate accepta de om (B4).

## Demontat (`tip: activ_demontat`)
Fiecare raport are un scor de propunere (calitatea potrivirii, sursa, extracția). Rapoartele pe același element din fereastra de 45 de zile se combină `1 − Π(1 − scor)`. Elementul trece `scos_din_uz` (nu se șterge) doar dacă au raportat cel puțin `demontat.rapoarte_min` (2) echipe diferite și scorul combinat e peste pragul de aplicare. Altfel rămâne în model cu semnal negativ și motiv („1 din 2 echipe necesare").

## Val de apeluri
Apelurile pe același element în `val_apeluri.fereastra_zile` (7): de la al 3-lea apel (`numar_min`) semnalul crește cu 50% pentru fiecare apel în plus, iar suma efectelor din fereastră nu depășește `plafon_semnal` (0,40). Tot sursa `apel_client` (0,25), același calcul.

## Locația din trace-ul tabletei
Dacă raportul are `detalii.trace` și nici ID, nici coordonate, motorul apelează `backend.trace.localizeaza` (A) cu adresa; oprirea aleasă devine `referinta.coordonate`, iar `detalii.trace_rezumat` păstrează rezultatul (pas nou `trace` în StepTrace). Calitatea din trace înmulțește calitatea potrivirii și a propunerii. Un stâlp existent la ≤ 15 m se confirmă; altfel apare nod prezis (punctat). Opririle lângă alți stâlpi existenți (`vizitate`), doar la rapoarte executate, dau verificări în plus (`confirmare_teren × fiabilitate × 0,7`). Dacă raportul are deja ID sau coordonate, trace-ul nu schimbă nimic.

## Cerere de racordare (`tip: cerere_racordare`)
Locația casei vine din `referinta.coordonate` (sau clic pe hartă). `backend.racordare.prezice_lant` (A) dă nodul de start, stâlpii și cablurile. Fiecare stâlp, casa (`NOU-<ev>-casa`, clasa `casa`) și cablu e un element separat (`NOU-<ev>-S<n>`, `-casa`, `-L<n>`). Scor: media ponderată (sursă, extracție, potrivire 0,7, urmărirea străzii), ×`racordare.factor_fara_strada` fără stradă. Peste 0,75 (sursă bună, ex. formular): se adaugă în model, în timp real. Între 0,40 și 0,75 (ex. apel de client): lanț punctat; omul poate accepta stâlp cu stâlp (o legătură intră doar dacă ambele capete există) sau respinge restul. Sub 0,40: neaplicat, cu motiv.

## Scenariul extrem
`engine.model_scenariu("extrem")` construiește un model separat din evenimentele de bază plus `data/events/events.extreme.json` (A6); ridică `FileNotFoundError` dacă fișierul lipsește. C poate înlocui scurtătura din `sources.model_extrem()`.

## Limite
- Valorile din `weights.yaml` sunt de pornire, necalibrate pe date reale.
- Drumul racordării și al propunerilor de zonă merge pe o singură stradă (limită a modulului lui A); altfel linie dreaptă.
- Raza de mutare e circulară; nu detectăm sensuri giratorii din OSM.
- La acceptarea unei propuneri de zonă omul nu poate ajusta geometria.

## Ce trebuie să știe ceilalți
- C: nivel nou `scos_din_uz` (desenează gri, tăiat); proprietate nouă `verificat_recent` (bool) în snapshot pentru haloul verde; pas nou `trace` în StepTrace (rezultatul `localizeaza`) și `zona` în `potrivire` pentru mutare_fire; `engine.aplica_decizie` și `engine.model_scenariu` există.
- A: modulele voastre sunt apelate din `sesiune2.py`; ieșirea de la `localizeaza` și `prezice_lant` e folosită exact cum e în contract.
