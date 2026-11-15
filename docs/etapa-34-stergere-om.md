# Etapa 34: ștergere de către om (`stergere_om`)

Rol B (contract + motor). Date FICTIVE. Cod: `backend/engine/stergere.py` (mixin `Stergere` în `GridModel`), ramura din `model.py::apply_event`, contract în `contracts/` (aditiv).

## Ce face
Un om poate șterge din hartă ce a adăugat sistemul după start. Eveniment `tip: stergere_om` (`echipa_sursa: om_teren`, `detalii.tinta_id`, `detalii.motiv` opțional). Motorul îl procesează fără extracție/potrivire (ca `tracking_tura`): nu cere `status` sau `forma_sursa`.

- **Se șterge:** predicțiile punctate (`self.predictii`: `NOU-*`, `MUT-*`, `PLAN-*`, `TRK-*`, lanțuri de racordare), elementele aplicate din rapoarte/tracking (`origine: generat_model`, `t0: false`, ex. `NOU-EV4-023`) și pinurile `VER-*`.
- **NU se șterge:** rețeaua de start (`t0: true`: GIS/KMZ și `SIM-*`) și elementele deja retrase/șterse. Refuz: decizie `neaplicat` + `trace["eroare"] = {cod, mesaj}`: `nu_se_sterge_retea_start`, `deja_sters` (inclusiv element respins de „Respinge” sau înlocuit de un ID real), `necunoscut` (ID inexistent sau gol). Nimic nu se modifică la refuz.
- **Efect = retras cu jurnal:** de la data ștergerii elementul nu mai apare în `snapshot`; la datele anterioare apare ca înainte (cu geometria și forma lui). `motive[0].text` = „Șters de om: <motiv>. Retras de la <data> ...” (fără motiv: „Șters de om (fără motiv indicat)”). **Fără penalizare** de metodă (penalizarea rămâne doar la „Respinge”). Scorurile altor elemente nu se schimbă.
- **Grup:** stâlp nou = el + legăturile lui ștergibile; legătură = ea + stâlpii ei ștergibili rămași fără alte legături; `TRK-*` + `…-L`, pin: ca înainte. **Lanț de racordare (decizia lui Victor):** ștergerea ORICĂRUI element al lanțului (casa, un stâlp prezis `-S<n>` sau o legătură `-L<n>`) șterge TOT lanțul: casa, toți stâlpii prezisi și toate legăturile aceluiași eveniment de racordare (predicții sau aplicate în model), dacă sunt ștergibile. Elementele existente la care se leagă lanțul (nod/tronson de start, `t0`) nu se șterg. Niciodată un element de start.
- **Cum se identifică lanțul** (`Stergere._lant_racordare`): id de forma `NOU-<event>-(casa|S<n>|L<n>)` și există `NOU-<event>-casa` în `istoric` (doar `_cerere_racordare` creează casa; `NOU-<ev>-<vecin>-S<k>` de la „nod lipsă” nu se confundă). Grupul = toate elementele `istoric` cu același `<event>` care sunt ștergibile acum. Merge la fel pentru lanțurile aplicate (în `net`) și pentru predicții, fiindcă folosește numele, nu starea. Un câmp marker nu e fiabil: elementele aplicate (`_adauga_in_model`) nu păstrează metadate de lanț.

## Decizii
- **Decizia în StepTrace: `sters`** (nu `aplicat`: ar apărea „Aplicat în rețea”). **Eticheta în timeline: `stergere`.** Rezumat: „Șters de om: <n> elemente (<id-uri>)” (primele 8 id-uri + „și încă k”); la refuz „Ștergere neaplicată: <mesaj>”.
- **Cum e reprezentată retragerea:** nouă stare în `self.istoric[eid]` cu `retras: True`, `sters: True`, `sters_data`, `sters_motiv` (aceeași cale prin care `snapshot` omite elementele respinse). Predicția iese din `self.predictii` și pinul din `self.pinuri`; elementul aplicat iese din `self.net["noduri"|"tronsoane"]` (nu mai e potrivit de rapoarte viitoare). Toate trec în `self.retrase[eid]` (`geometrie` + `el`, forma originală din `net`) ca istoricul să-l poată reda: `_geometrie`, `_props_element` și `clasa` o citesc de acolo.
- **`stergibil`** (în `snapshot` și `_publica`) = element activ, `t0` fals, `origine != retea_start`, în `predictii`/`pinuri`/`net`. **`stergere_n`** în `snapshot` = mărimea grupului (pentru confirmare), 0 dacă nu e ștergibil.
- **Distribuția culorilor:** `distributie_culori` nu numără elementele șterse (snapshot-ul le omite, ca pe cele respinse); criteriul nu s-a schimbat. Logica a fost doar extrasă în `distributie_model(m, data)` ca să poată fi testată pe un model cu ștergeri. Scenariul nu are ștergeri: calibrarea și referința de aur neschimbate.

## StepTrace (exemplu real, ștergerea lanțului EV4-017)
```
{"event_id": "DEL-1", "data": "2026-11-20", "decizie": "sters",
 "pasi": [{"nume": "potrivire", "rezultat": {"status": "potrivit", "element_id": "NOU-EV4-017-L1", "metoda": "tinta_id", ...}},
          {"nume": "predictie", "rezultat": null},
          {"nume": "scor", "rezultat": {"nivel": null, "tinta": "NOU-EV4-017-L1", "grup": ["NOU-EV4-017-casa", "NOU-EV4-017-L1"], "sters": 2, "decizie": "sters"},
           "motive": ["Șters de om: nu există în teren. Retras de la 2026-11-20 (DEL-1); rămâne în istoric, vizibil la datele anterioare. Fără penalizare pentru metoda care l-a propus."]}],
 "modificari": [{"element_id": "NOU-EV4-017-casa", "nivel": "predictie", "scor": 0.362, "banda": "rosu", "sters": true, "sters_data": "2026-11-20", "sters_motiv": "nu există în teren", "stergibil": false, "motive": [...]}, {"element_id": "NOU-EV4-017-L1", ...}],
 "schimbari": [{"element_id": "NOU-EV4-017-casa", "ce": "sters", "scor_inainte": 0.362, "scor_dupa": 0.362, "banda_inainte": "rosu", "banda_dupa": "rosu", "de_ce": "Șters de om: ..."}, {"element_id": "NOU-EV4-017-L1", "ce": "sters", ...}],
 "stergere": {"tinta_id": "NOU-EV4-017-L1", "elemente": ["NOU-EV4-017-casa", "NOU-EV4-017-L1"], "n": 2, "motiv": "nu există în teren"}}
```
La refuz: `decizie: neaplicat`, `eroare: {cod, mesaj}`, `modificari: []`.

## Cum se verifică
```bash
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_stergere   # 47/47 OK
EXTRACT_CLI=0 bash scripts/verifica_tot.sh --strict-distributie   # TOT VERDE (smoke_stergere e în SMOKES)
```
Acoperă: lanț de racordare (EV4-017: 2 elemente; EV4-012: 10 elemente, din casă, stâlp din mijloc sau legătură; `stergere_n` pe fiecare element; nodul de start rămâne), element aplicat `NOU-EV4-023` (scos din `net`; un raport pe aceeași poziție se potrivea înainte, nu mai după), `TRK-*` + `…-L` (și legătura ca țintă), pin `VER-*`, refuzuri (GIS nod/tronson, `SIM-*`, ID inexistent/gol, a doua ștergere, element respins), „Respinge” neschimbat, `stergibil`/`stergere_n`, fără penalizare, scoruri neschimbate, determinism, eticheta `stergere`, distribuția.

## Limite
- Ancorele de căutare pe stradă (`self.ancore`, adrese din rapoarte) nu se șterg odată cu elementul.
- Ștergerea unui `MUT-*` nu readuce tronsoanele vechi `scos_din_uz` (sunt rețea de start, neatinse).
- Ștergerea e ireversibilă (nu există „restaurează”); nu poate fi respinsă o predicție ștearsă, nici șters un element respins.
- `stergibil`/`stergere_n` la o dată trecută reflectă starea de acum.
- Nu există test prin API: endpointul `POST /element/{id}/stergere` nu e încă făcut (testat doar la nivel de motor).

## Pentru Claudiu (API/UI)
- **Endpoint** `POST /element/{id}/stergere {motiv?, data?}`: construiește `{"event_id": ..., "tip": "stergere_om", "echipa_sursa": "om_teren", "data": ..., "detalii": {"tinta_id": id, "motiv": motiv}}` și cheamă `engine.apply_event(...)`; întoarce StepTrace (200). Dacă `trace["eroare"]["cod"]` e `nu_se_sterge_retea_start` sau `deja_sters` -> 409, `necunoscut` -> 404 (ca la `deja_decis`/`necunoscut` din `/predictii/{id}/decizie`). Adaugă în `DECIZII` din `backend/api/prezentare.py`: `"sters": "Șters de om"` (altfel UI-ul ar arăta codul brut „sters”). Etichetele de timeline: `stergere` (text „Ștergere”).
- **UI:** buton „Șterge” în panoul Identificare, doar când feature-ul din `GET /retea` are `stergibil: true`; confirmare „Se șterg `stergere_n` elemente (elementul și legăturile lui). Rămân vizibile la datele anterioare.”; după succes refresh la hartă și timeline. Pe GIS/SIM butonul nu apare.
