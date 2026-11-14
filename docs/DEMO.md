# Demo (repetat de B pe UI-ul plan B, cu motorul real și `events.json` al lui A)

Date FICTIVE: rețea demonstrativă PTAB 7812. Spune asta la început.

## Pornire
```bash
.venv/bin/uvicorn backend.api.main:app --port 8000      # apoi deschide http://localhost:8000/ui/
```
`/health` trebuie să arate `retea=motor, evenimente=motor, motor=real`. `extractie=stub` pe laptopurile fără cheia OpenRouter (A are `claude`). Reporniți serverul înainte de demo: rapoartele live rămân în memorie până la repornire.

## Scenariul de 60 de secunde (Play durează ~29 s)
| Timp | Pe ecran | Ce spui |
|---|---|---|
| 0–5 s | Harta pe date 4 aug., rețeaua galben-verzuie | „530 de elemente, toate la încredere 0,6: nimeni nu le-a verificat recent. Culoarea e încrederea." |
| 5–10 s | Apasă Play. Apare un punct violet (4 și 18 aug.) | „Două rapoarte spun că lipsește un nod în curba străzii. Nu avem coordonate, deci îl propunem punctat, cu scor 0,74, apoi 0,81. Nu intră în model." |
| 10–16 s | 5–20 aug.: elemente devin mai verzi | „Verificările din teren cresc încrederea." |
| 16–20 s | 29 aug.: un element roșu | „Două echipe spun lucruri diferite despre aceeași secțiune: conflict. Nu aplicăm nimic, îl marcăm «de verificat»." |
| 20–23 s | 10 sept.: aplicat | „Investiții a înlocuit cablul. Formular cu scor 0,90: se aplică." |
| 23–29 s | Octombrie: rețeaua se închide la portocaliu; apeluri | „Apelurile clienților scad puțin încrederea, nu șterg nimic. Ce nu e verificat se estompează în timp." |
| 29–45 s | Pauză. **Proces raport**, lipește textul de mai jos | „Un raport nou, scris liber, trece prin pași vizibili." |
| 45–60 s | „Vezi pe hartă": punctul violet devine solid | „Raportul cu coordonate confirmă nodul: predicția intră în model, cu legăturile către vecini." |

Text de lipit (sursă: mentenanță, data 2026-10-28):
> Confirm în teren nodul 6925190 din curba străzii, la coordonatele 44.2830311, 26.063942, între nodurile 6513200 și 7824201.

Rezultat verificat: `adaugat`, scor 0,95, predicțiile rămase 0, nodul și 2 legături în model.

## Verificat la repetiție (14 nov.)
- Play de la 4 aug. la 27 oct. durează ~29 s; slider-ul și lista de evenimente se actualizează; consola fără erori.
- Culoarea e continuă (0,3 roșu → 0,8 verde), deci scăderea în timp și confirmările se văd.
- Un raport live apare pe hartă și în timeline cu data corectă.

## Riscuri la demo
- **Harta de bază cere internet** (plăci OpenStreetMap). La repetiție, într-un moment plăcile nu s-au încărcat și fundalul a fost gri; liniile rămân vizibile. Plan B: înregistrare video a unei rulări reușite.
- **Extracția live depinde de laptop:** cu `stub regex` unele texte primesc alt tip (aici raportul de mai sus iese «avarie»), dar motorul îl tratează tot ca nod lipsă pentru că ID-ul numeric nu există în model. Cu Claude iese `nod_lipsa`.
- **Scenariul 1 nu se închide singur** în datele lui A: rapoartele lui nu au coordonate pentru nod, de aceea partea „live" finalizează povestea. Dacă A adaugă un raport cu coordonate (44.2830311, 26.063942) într-o dată din toamnă, punctul devine solid chiar în timeline.
- **Apelurile:** 3 din 5 nu s-au putut potrivi (unul fără coordonate, două la peste 40 m de orice element); în timeline scad doar două elemente.
- **Proiectul Lovable** al lui C e netestat și nepublicat; demo-ul de mai sus rulează pe UI-ul plan B (Leaflet servit de FastAPI).
