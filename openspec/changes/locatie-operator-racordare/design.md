# Design

## Context

`cerere-racordare-predictie` cere locația casei din text, coordonate sau clic. Cazul real de pe teren: adresă vagă, fără coordonate, operatorul e la fața locului. Nu avem GPS real; demo-ul simulează poziția.

## Goals / Non-Goals

**Goals:**
- Un buton explicit produce o poziție dummy, reproductibilă, marcată `simulata: true`, cu precizie.
- Poziția ajută lanțul de racordare (pornește spre ea), cu scor mai mic decât la coordonate exacte, prin același `weights.yaml`.
- Rezultatul rămâne predicție până confirmă omul.

**Non-Goals:**
- Nu geocodăm texte necunoscute și nu inventăm un punct pentru ele.
- Nu citim GPS real și nu cerem permisiuni de locație din browser.

## Decisions

- Generare deterministă: seed = hash al textului normalizat (fără diacritice, litere mici, prescurtări expandate: str., bd., sos., cart.). Același text dă același punct, deci demo-ul se repetă.
- Parsare cu reguli simple, fără AI. Indicii: `strada` (nume din `osm.strazi()`), `intersectie` („colț cu", „intersecția", sau două străzi pomenite; străzile trebuie să fie la <= 25 m una de alta), `cartier` (zonele OSM `is_in`, ex. „1 Decembrie"; nu există poligon, deci zona = dreptunghiul străzilor ei plus 30 m), `reper` („lângă ...": mereu `gasit: false`, datele OSM locale nu au repere). Constrângerile se combină prin intersecție; contradicție sau niciun indiciu găsit: eroare 422 „dă clic pe hartă". Indiciile negăsite se raportează cu `gasit: false`, nu se ignoră în tăcere.
- `precizie_m` reflectă cât de vagă e zona: intersecție mică (10 m), stradă după lungime (15-40 m), cartier mare (60 m). `zona` descrie constrângerea aplicată.
- Punctul: pe stradă, la cel mult `racordare.raza_nod_m` de cel mai apropiat nod (altfel lanțul n-ar porni) și cel puțin `racordare.operator_distanta_min_m` (ca să existe ce prezice); dintre candidate, cel mai depărtat de rețea. Dacă primește `lat`/`lon` ca indiciu, alege candidatul cel mai apropiat de indiciu; pe cartier alege determinist după seed. Apoi zgomot GPS de cel mult jumătate din `precizie_m`.
- Motorul: `detalii.locatie_operator` se folosește doar când `referinta.coordonate` și `detalii.locatie` lipsesc. Precedența: text, clic, operator simulat.
- Scor: același calcul de propunere, înmulțit cu `racordare.factor_locatie_operator` (< 1). Nivelul nu poate fi `in_model`: poziția simulată nu aplică niciodată singură lanțul.
- `sursa_locatie` apare în pașii `potrivire` și `predictie` ai StepTrace.

## Risks / Trade-offs

- Poziția simulată nu e o măsurătoare: UI-ul trebuie să o marcheze „simulată" și să arate precizia. Altfel ar da impresia unei date reale.
- Drumul racordării merge pe o singură stradă (limita lui `prezice_lant`); poziția pe stradă potrivește bine, dar nu garantează lanț, doar `linie_dreapta` ca rezervă.
