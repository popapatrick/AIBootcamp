Corectează 4 defecte găsite la testare. NU schimba altceva: nu atinge URL-ul API (vine doar din `?api=`), toate textele rămân în română, nu șterge testele existente, nu modifica culorile, harta principală sau celelalte tab-uri.

1. Suprapunere (fișa evenimentului vs panoul Identificare). După selecția unui element, fișa evenimentului (dreapta-jos, z-index ~1065) acoperă partea de jos a panoului Identificare, inclusiv butoanele „Marchează verificat de om" și „Șterge" (`src/components/Identificare.tsx`). Fix: când Identificare e deschis cu un element selectat, fișa evenimentului se închide/minimizează sau nu se mai afișează peste el (alege varianta cea mai simplă), iar butoanele din Identificare rămân vizibile și clicabile la 1600x1000 și la 1366x768 (fără să iasă din ecran; panoul poate avea scroll intern).

2. Fișa pentru evenimente `tip` = `tracking_tura` și `stergere_om`. Acum arată cod brut „Tip eveniment: tracking_tura" și câmpurile „Stare lucrare / Element (ID) / Adresă: — lipsă". Fix, doar pentru aceste două tipuri:
   - titlul = `eticheta_text` din `GET /evenimente` („Tracking echipă", „Ștergere"); nu afișa `tip` brut;
   - nu afișa câmpurile de raport din `standardizare.campuri` (Stare lucrare, Element (ID), Adresă, Coordonate, „lipsă");
   - arată echipa din câmpul `echipa` al evenimentului (deja „Mentenanță", „Investiții", „Racordări"; niciodată „mentenanta"), `rezumat`, data, `banda_inainte` → `banda_dupa` și lista `schimbari` (cu `de_ce`) ca la celelalte evenimente;
   - durata și numărul de opriri doar dacă există în eveniment (altfel nu afișa nimic, nu „—").
   Celelalte tipuri de evenimente rămân neschimbate.

3. Tura nou generată (`src/components/TrackingPanel.tsx`, `src/hooks/use-tracking.ts`) arată „—" în loc de „Neaplicată", fiindcă răspunsul `POST /tracking/genereaza` nu are câmpul `aplicata`. Tratează lipsa (undefined/null) ca `false` peste tot unde se afișează starea („Aplicată"/„Neaplicată", în listă și în detaliu). După aplicare (`aplicata: true`), butonul „Aplică în model" devine dezactivat (tura e deja aplicată).

4. La intrarea în tab-ul Tracking harta pornește la zoom ~8 și pierde încadrarea. Fix: harta trebuie să rămână încadrată pe rețea (aceeași vedere inițială ca harta principală) sau, dacă există o tură selectată, pe `focus` (lat, lon, zoom / bbox) al turei. Fără zoom hardcodat nou; reutilizează vederea/`fitBounds` din harta principală (`src/components/ReteaMap.tsx`).

Verificare: la 1600x1000 și 1366x768 butoanele „Marchează verificat de om" și „Șterge" se pot apăsa cu fișa deschisă; fișa unei ture arată „Tracking echipă" fără câmpuri lipsă; tură nou generată = „Neaplicată", apoi „Aplicată" cu butonul dezactivat; tab-ul Tracking se deschide încadrat pe rețea.
