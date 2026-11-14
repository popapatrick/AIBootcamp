# Design

## Context

`cerere-racordare-predictie` cere locația casei din text, coordonate sau clic. Cazul real de pe teren: adresă vagă, fără coordonate, operatorul e la fața locului. Nu avem GPS real; demo-ul simulează poziția.

## Goals / Non-Goals

**Goals:**
- Un buton explicit produce o poziție dummy, reproductibilă, marcată `simulata: true`, cu precizie.
- Poziția ajută lanțul de racordare (pornește spre ea), cu scor mai mic decât la coordonate exacte, prin același `weights.yaml`.
- Rezultatul rămâne predicție până confirmă omul.

**Non-Goals:**
- Nu geocodăm adrese necunoscute și nu inventăm un punct pentru ele.
- Nu citim GPS real și nu cerem permisiuni de locație din browser.

## Decisions

- Generare deterministă: seed = hash al adresei normalizate (fără diacritice, litere mici). Aceeași adresă dă același punct, deci demo-ul se repetă.
- Strada se caută în `osm.strazi()` după nume (potrivire pe numele normalizat, cea mai lungă câștigă). Fără potrivire: eroare 422 „adresa nu se poate localiza, dă clic pe hartă".
- Punctul: pe stradă, la cel mult `racordare.raza_nod_m` de cel mai apropiat nod (altfel lanțul n-ar porni) și cel puțin `racordare.operator_distanta_min_m` (ca să existe ce prezice); dintre candidate, cel mai depărtat de rețea. Dacă primește `lat`/`lon` ca indiciu, alege candidatul cel mai apropiat de indiciu. Apoi zgomot GPS de cel mult `racordare.operator_precizie_m` (15 m).
- Motorul: `detalii.locatie_operator` se folosește doar când `referinta.coordonate` și `detalii.locatie` lipsesc. Precedența: text, clic, operator simulat.
- Scor: același calcul de propunere, înmulțit cu `racordare.factor_locatie_operator` (< 1). Nivelul nu poate fi `in_model`: poziția simulată nu aplică niciodată singură lanțul.
- `sursa_locatie` apare în pașii `potrivire` și `predictie` ai StepTrace.

## Risks / Trade-offs

- Poziția simulată nu e o măsurătoare: UI-ul trebuie să o marcheze „simulată" și să arate precizia. Altfel ar da impresia unei date reale.
- Drumul racordării merge pe o singură stradă (limita lui `prezice_lant`); poziția pe stradă potrivește bine, dar nu garantează lanț, doar `linie_dreapta` ca rezervă.
