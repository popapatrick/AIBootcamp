# Etapa 5: scor, decizie și model în timp (B)

Date FICTIVE.

## Ce face
- `backend/engine/scoring.py`: regulile de scor, funcții pure, parametri din `contracts/weights.yaml`.
- `backend/engine/model.py`: `GridModel`, modelul GIS versionat în timp. Primește evenimente, decide ce se aplică și ce rămâne predicție, ține jurnal și „de ce", redă starea la orice dată.
- `backend/engine/engine.py`: interfața pentru API (C): `apply_event`, `snapshot`, `timeline`, `statistici`, `reset`, `jurnal`.

## Cum se rulează și se verifică
```bash
.venv/bin/python -m backend.engine.smoke_engine   # așteptat: OK: 16 verificări
```
Din cod: `from backend.engine.engine import apply_event, snapshot, timeline`.

## Regula de decizie (aceeași pentru toate inputurile și predicțiile)
**Scor de propunere** = medie ponderată a: fiabilitatea sursei, încrederea extracției, calitatea potrivirii și, când există, cât de bine urmează traseul strada (etapa 6). Dacă un factor lipsește, ponderile rămase se renormalizează. Ponderile sunt în `weights.yaml`, secțiunea `propunere`.

| scor propunere | rezultat |
|---|---|
| ≥ 0,75 | aplicat (sau, pentru element lipsă, adăugat în model) |
| 0,40 – 0,75 | **predicție**: neaplicată, vizibilă, cu scor |
| < 0,40 | de verificat; un element nou nu se desenează, rămâne în jurnal |

- **Ce e doar planificat** (`status = planificat`, `linie_planificata`) nu se aplică niciodată, oricât de mare ar fi scorul.
- **Efect asupra unui element existent** = confirmare (+0,25) sau semnal negativ (−0,20), înmulțit cu fiabilitatea sursei și cu calitatea potrivirii. Un raport executat al unei echipe din teren e confirmare. **Un apel de client e semnal negativ slab** (fiabilitate 0,25): scade încrederea, nu șterge nimic, pentru că „nu am curent" poate însemna cădere, nu lipsa rețelei. Apelul trece prin același calcul ca oricare alt input.
- **Scădere în timp:** −0,07 la 30 de zile fără verificare, calculată la citire (`snapshot(data)`). După ~3 luni un element neverificat (0,60) coboară sub 0,40 și devine „de verificat". Un element confirmat recent rămâne verde.
- **Conflict:** două rapoarte diferite despre aceeași proprietate (secțiunea unui tronson) în 45 de zile: nu se aplică nimic nou, elementul devine „de verificat" și noul raport rămâne ca propunere.
- **Al doilea raport despre aceeași predicție** (de ex. nod lipsă) o întărește; dacă trece pragul, predicția e promovată în model.
- **Element nou (nod lipsă, racord):** geometria legăturilor e linie dreaptă între noduri vecine până apare traseul OSM (etapa 6); `GridModel.traseu_fn` e punctul de conectare.

## „De ce" și jurnal
Fiecare stare are `motive` (cel mai recent primul), cu textul, efectul asupra scorului, evenimentul sursă și data. La citire se adaugă automat „Neverificat de N zile". `jurnal` păstrează fiecare eveniment cu decizia lui. `StepTrace` are pașii: extracție, potrivire, predicție, scor (cu factorii).

## Decizii
- Scorul unei propuneri nu înmulțește totul cu fiabilitatea: așa nici un raport bun din text liber, nici unul de pe tabletă nu ar trece de 0,75 și „majoritatea n-ar intra" (cerința lui Victor). Cu valorile de acum, tableta și formularul cu ID trec; textul liber fără ID și cu extracție slabă rămâne predicție.
- `scadere_per_30_zile` a fost schimbat de la −0,05 la −0,07 ca scăderea să se vadă în 3 luni.
- Evenimentele se aplică în ordine cronologică; un eveniment mai vechi decât ultimul aplicat primește data ultimului (notă în `trace["nota"]`).

## Limite cunoscute
- Pragurile sunt puncte de plecare: se calibrează pe rapoartele reale ale lui A (testat până acum pe evenimente sintetice).
- Apelurile fără element potrivit (client unde modelul nu are linie) rămân doar în jurnal, nu generează încă propuneri.
- Un tronson adăugat nu are secțiune (necunoscută).
- Traseul pe stradă (etapa 6) nu e implementat: legăturile noi sunt linii drepte.
- Nu am verificat vizual pe hartă.

## Ce trebuie să știe ceilalți
- C: importă din `backend.engine.engine`. Proprietățile feature-urilor din `snapshot` urmează `state.schema.json` plus atribute (`sectiune`, `categorie`, `capete`).
- A: pentru ca extracția să ajungă bine în scor, completează `tip_sursa_pondere`, `forma_sursa`, `incredere_extractie` și, pentru înlocuiri, `detalii.sectiune_noua`; pentru nod lipsă `detalii.noduri_vecine` (altfel se deduc și scorul scade); pentru linii planificate `detalii.noduri` (două ID-uri).
