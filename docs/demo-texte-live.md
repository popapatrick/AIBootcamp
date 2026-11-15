# Texte pentru raportul scris live la demo (în cache)

Date FICTIVE. Textele de mai jos sunt deja în `data/cache/` (cheia = text + echipă + dată; fără dată în text se folosește data zilei, deci valabile **doar fără dată scrisă în text** și cu aceeași echipă). Verificate pe API (15.11.2026, model resetat înainte de fiecare): `standardizare.metoda` = `ai_cache`, răspuns instant, fără AI live. Textul trebuie scris **exact** (inclusiv punctuația); variantele fără diacritice sunt cache-uri separate.

Data de rezervă (raport fără `data` și fără dată în text) e fixă: `DEMO_DATA` din env, implicit `2026-11-15` (`backend/api/pipeline.py:data_demo`). Cache-ul se potrivește deci în orice zi a demo-ului, fără refacere dimineața; refacerea rămâne doar rezervă (dacă se setează alt `DEMO_DATA` sau textul conține o dată). Vezi `docs/etapa-35-api-tracking-stergere.md`, „DEMO_DATA”.

| Echipă | Text | Decizie | Scor / bandă |
|---|---|---|---|
| Mentenanță | Stâlp căzut pe Strada Orhideelor lângă nr. 3 | predicție | 0,609 galben |
| Mentenanță | stalp cazut pe Strada Orhideelor langa nr 3 | predicție | 0,609 galben |
| Mentenanță | Montat stâlp nou pe Strada Viilor nr. 9 | adăugat | 0,586 portocaliu |
| Investiții | Linie nouă executată pe Strada Tineretului, stâlp nou montat între nr. 10 și nr. 20 | adăugat | 0,608 galben |
| Investiții | Stâlp nou montat la capătul Străzii Crinului | adăugat | 0,511 portocaliu |
| Investiții | montat stalp nou pe Strada Teiului nr. 5 | adăugat | 0,533 portocaliu |
| Racordări | Cerere racord Strada Bălții nr. 14 | predicție | 0,400 portocaliu |
| Racordări | cerere racordare casa noua Strada Regina Maria nr. 40 | predicție | 0,302 roșu (predicție slabă, departe de rețea) |
| Racordări | Cerere de racord pentru casă pe Strada Speranței nr. 7 | predicție | 0,302 roșu (predicție slabă) |
| Racordări | Racord nou executat pe Strada Soarelui nr. 8 | adăugat | 0,503 portocaliu |

Cele mai bune pentru efect vizual: Orhideelor (căutare pe stradă), Tineretului (fereastră + candidați), Viilor.

Eliminate (dau `de_verificat`, fără efect): „avarie izolator pe Strada Ulmului, lângă nr. 6" și „Înlocuit stâlp vechi pe Strada Carpati nr. 12".

După probe: `POST /demo/reset`.
