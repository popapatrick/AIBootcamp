# Cadre pentru video-ul de rezervă (~3 min)

Bazat pe `docs/demo-parcurs-sesiune4-ciorna.md`. Date FICTIVE. Înregistrare cu modelul resetat (`POST /demo/reset`) și textele din cache.

| # | Durată | Pe ecran | Ce se spune |
|---|---|---|---|
| 1 | 0:00-0:15 | Intro `/`: titlul, cele 3 carduri „Cum funcționează” | „Rețeaua electrică se schimbă zilnic, harta rămâne în urmă. Noi o ținem la zi din rapoarte scrise liber. Date fictive.” |
| 2 | 0:15-0:35 | „Intră în hartă”, legenda cu 4 benzi, clic pe un element (Identificare) | „Verde = sigur, galben = probabil, portocaliu = nesigur, roșu = foarte nesigur. Linia plină e în rețea, cea punctată e predicția modelului.” |
| 3 | 0:35-1:15 | Cardul 1 „Stâlp căzut lângă nr. 3” → „Vezi pe hartă”: panoul „Ce a înțeles AI-ul”, fereastra pe stradă, candidații, cel ales, „De ce?” | „Doar «Strada Orhideelor, lângă nr. 3», fără coordonate. AI-ul extrage locul; modelul caută pe stradă și alege cel mai probabil stâlp, cu scor.” |
| 4 | 1:15-1:50 | Cardul 4: elementul galben → verde → verde cu ✓ (14.09, 17.09, 10.11) | „Aceeași informație, trei pași: adresă (galben), GPS (verde), verificare de om (1,0). Fiecare pas are jurnal și «de ce».” |
| 5 | 1:50-2:15 | Cardul 3: casă departe de rețea, legătură pe străzi, culoare galben/portocaliu | „Modelul propune stâlpul casei și legătura pe străzi, dar scorul e mic: e doar o predicție.” |
| 6 | 2:15-2:40 | Buton „Mentenanță” → `mnt-02` → Trimite: pașii Standardizare, Potrivire, Decizie; zbor spre loc | „Raport nou, în română obișnuită: AI-ul îl standardizează, modelul îl potrivește, harta se actualizează pe loc.” |
| 7 | 2:40-2:55 | Timeline: derulare înapoi la 1 august, apoi la „acum” | „În trei luni, ~55 de rapoarte au schimbat rețeaua, fără ca cineva să redeseneze harta.” |
| 8 | 2:55-3:05 | „Resetează demo” (confirmare), apoi intro | „Același calcul de scor pentru orice informație: GIS, raport sau apelul unui client.” |
| 9 (opțional, dacă P4 e aplicat) | +0:20 | Tab-ul „Tracking echipe”: pozițiile echipelor pe hartă; apoi un element adăugat de sistem (ex. `NOU-*`) → butonul „Șterge” → confirmare „Se vor șterge N elemente” → elementul dispare, rămâne în istoric „Șters de om” | „Echipele din teren apar pe hartă. Omul poate șterge ce a adăugat sistemul; ștergerea e retrasă cu jurnal, rețeaua de start nu se șterge.” |

Note: cadrul 9 nu intră în cele ~3 min dacă P4 nu e aplicat. Cardul 2 (sens giratoriu) se omite dacă nu e gata.
