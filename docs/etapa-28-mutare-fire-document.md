# Etapa 28: fire mutate din document (V4, D12; rol B, Sesiunea 4)

Date FICTIVE pentru rețea; străzile sunt reale (OSM local, ODbL). Fără AI în motor, fără imagini, fără serviciu extern.

## Ce face
Un raport de teren care spune doar în text că firele au fost mutate (fără clic, fără coordonate) dă acum o zonă marcată pe hartă și un traseu nou pe străzi care ocolește zona. Exemplul de pe cardul de intro:

> „Ca urmare a construirii sensului giratoriu de la intersecția Șoseaua Principală cu Strada Liviu Rebreanu, rețeaua aeriană JT a fost mutată pe Strada Crinului. Lucrare finalizată 10.10.2026.”

1. **Centrul zonei** (`sesiune2.py::_centru_mutare`), în ordinea: `detalii.centru` > coordonate din raport/clic > **intersecția** (`detalii.intersectie {strada_1, strada_2}`, sau indiciul `colt`, sau regex pe text; geocodată cu `backend.geo`, `acuratete.intersectie`, rază `mutare_fire_document.raza_intersectie_m` = 60 m) > **nodul** din `referinta.element_id` (sursa `id`, rază `mutare_fire.raza_m` = 40 m) > **strada** numită (mijlocul ei, rază dublă = 120 m, sursa `strada`). Fără nicio stradă, intersecție, nod sau coordonate: `neaplicat` cu motivul „Mutare de fire fără locație…” (P3). `detalii.raza_m`, dacă e dat, înlocuiește raza. Punct în afara zonei de 3 km: eronat în prototip (ca înainte).
2. **Regex de rezervă** (`mutare_fire_text.py`, doar dacă extracția nu a pus câmpurile): „intersecția X cu Y”, „colț cu Y” (strada 1 din adresă), adresa de forma „X cu Y”, „mutat(ă/e) pe Strada Z” (= `strada_noua`). `strada_noua` se potrivește (fără diacritice/majuscule) cu numele din cache-ul OSM; dacă nu e acolo, nu se preferă nimic.
3. **Zona afectată** (logica existentă): nodurile și tronsoanele la ≤ rază devin `de_verificat`, scor ≤ `mutare_fire.scor_marcat` (0,35), cele mai apropiate `mutare_fire.max_elemente` (25). Motiv „Mutare de fire în zonă (…)”.
4. **Traseul nou** (`_ancore_mutare`, `_legaturi_mutare`): ancorele = capetele aflate la > rază de centru ale tronsoanelor **aeriene** care intră în zonă (cel mult 6, cele mai apropiate de centru; tot ce e în rază, inclusiv ce depășește plafonul de 25, intră în `exclus`). Pentru fiecare pereche de ancore se calculează `traseu_pe_strazi(tinta=b, de_la=a, evita={centru, raza_m}, preferate=[strada_noua], exclus=zona, sursa=…)`. Se păstrează un **arbore de lungime minimă** (Kruskal) din drumurile ≤ `MAX_OCOLIRE_M` (1500 m, în cod; suprascris de `mutare_fire_document.max_ocolire_m` dacă cineva îl adaugă): ancorele rămân conectate fără legături în plus. Fiecare legătură = tronson `MUT-<event_id>-<n>` cu capetele `de_la`/`la` (stâlpi existenți) și geometria drumului ales (`ales.traseu`). Nu se creează stâlpi noi intermediari (traseul e un singur tronson; stâlpii pe care i-ar pune analiza apar doar în explicația pasului).
5. **Scor și decizie** (pe fiecare legătură): `scor = min(scor_propunere, acuratete)` unde `acuratete = plafon_locatie[sursa] × max(factor_min, exp(−L/lungime_referinta_m))` (sursa = `intersectie`, `strada`, `coordonate` sau `id`). `scor_propunere` e media ponderată obișnuită (fiabilitate sursă, încredere extracție, `mutare_fire.calitate_propunere`, urmează strada 1,0). Decizia: `S.decizie` cu pragul P1 (`acuratete.aplicat_raport_executat` 0,50) **doar** dacă `status: executat` și echipa e mentenanță/investiții; orice altceva (planificat, semnalat, alte echipe) nu aplică niciodată: predicție punctată. Sub `praguri.predictie` = „predicție slabă” (`predictie.slaba: true`); sub `racordare.prag_afisare` (0,15) legătura nu se creează (se spune în mesajul pasului `scor`).
6. **„Demontat probabil”**: dacă ≥ 1 legătură e aplicată, **tronsoanele aeriene marcate** din zonă trec la `nivel: scos_din_uz` (UI: gri punctat, „demontat probabil”), scorul rămâne cel marcat (≤ 0,35), motiv „Demontat probabil: fire mutate în zonă (…); traseul nou (MUT-…) e aplicat…”. **Nu se șterg** din model, rămân în istoric și pot fi redeschise de o verificare. Nodurile și tronsoanele subterane marcate rămân `de_verificat`. Dacă nimic nu e aplicat (predicții), tot ce e marcat rămâne `de_verificat`.
7. **Fără drum care ocolește zona** (niciun drum ≤ 1500 m): o singură legătură `fara_drum` între cele mai apropiate două ancore: linie dreaptă (trece prin zonă, flagată), `predictie.fara_drum: true`, `metoda: linie_dreapta`, scor ≤ `analiza_harta.fara_drum` (0,25), predicție slabă, niciodată aplicată.

## Cum se verifică
```bash
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune4   # așteptat: 121/121 OK (blocul „mutare fire …”, 21 de verificări)
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune2   # așteptat: OK: 66 verificări
bash scripts/verifica_tot.sh --strict-distributie                  # așteptat: TOT VERDE, distribuția în țintă
```
Exemplul de intro, direct: eveniment `mutare_fire`, `executat`, `mentenanta`, `detalii.intersectie` + `strada_noua` (sau doar `text_original` cu fraza), vezi `teste_mutare_fire_document()` în `smoke_sesiune4.py`.

## Rezultat pe hartă pentru exemplul de intro (verificat)
Centru 44,282179 / 26,065232 (intersecția Șoseaua Principală × Strada Liviu Rebreanu, ±15 m), rază 60 m, sursa `intersectie` (plafon 0,60). Zona are 27 de tronsoane și 23 de noduri la ≤ 60 m; se marchează cele mai apropiate 25 (12 noduri + 13 tronsoane). 6 ancore aeriene la 65–91 m de centru; 5 legături (arbore):

| Legătură | Drum | Lungime | Scor | Decizie |
|---|---|---|---|---|
| MUT-…-1 (6374339 – 6555187) | fără stradă numită (capete lângă același colț) | 10 m | 0,585 | aplicat |
| MUT-…-2 (7179803 – 6374339) | Șoseaua Principală | 58 m | 0,52 | aplicat |
| MUT-…-3 (6538120 – 6203522) | Strada Carpati, Viilor, Soarelui | 416 m | 0,21 | predicție slabă |
| MUT-…-4 (6203522 – 6589057) | Strada Soarelui, Viilor, Liviu Rebreanu | 646 m | 0,18 | predicție slabă |
| MUT-…-5 (6589057 – 6374339) | Strada Liviu Rebreanu, **Crinului**, Tineretului, Bălții, Șoseaua Principală | 1087 m | 0,18 | predicție slabă |

Niciun segment nou nu intră în cerc (cel mai apropiat e la 60,2 m). Cele 6 tronsoane aeriene marcate (de ~13) trec `scos_din_uz`. **Ce arată harta:** cercul de 60 m taie ambele drumuri care se întretaie, deci două ancore de pe brațe diferite nu se pot lega decât ocolind un cartier întreg: de aceea unele legături sunt lungi (400–1100 m) și slabe (roșu). Strada Crinului apare în singura legătură care unește partea de nord-vest cu cea de sud-est (1087 m); e și drumul cel mai scurt fără preferință, deci preferința din text (`cost_strada_noua` 0,5) nu schimbă aici alegerea. Crinului se află la ~250 m nord-vest de intersecție: „mutată pe Strada Crinului” înseamnă pe hartă un traseu lung, nu o deviere locală.

`EV4-026` (din `data/events/events.json`; „Șoseaua Principală”, nodul 5481763): iese acum `de_verificat` (nu `neaplicat`): centrul = nodul 5481763 (sursa `id`, rază 40 m), 4 elemente marcate, 1 singură ancoră în afara zonei, deci nicio legătură nouă. `EV4-041` (Strada Speranței colț cu Strada Tineretului): cele două străzi nu se intersectează în cache, deci centrul = mijlocul Străzii Speranței (sursa `strada`, rază 120 m), 4 elemente marcate, 1 ancoră, fără legătură.

## Intrări / ieșiri
- Intrare: `Event` `mutare_fire`; câmpuri folosite: `detalii.{centru, raza_m, intersectie{strada_1, strada_2}, strada_noua, motiv_mutare, observatii}`, `referinta.{coordonate, element_id, adresa, adresa_structurata}`, `text_original`, `status`, `echipa_sursa`.
- Pași în `pasi`: (`geocodare`, cu `intersectie`, dacă s-a încercat intersecția sau strada), `potrivire` (`status: zona`, `centru`, `raza_m`, `sursa_centru: coordonate|intersectie|id|strada`, `text_centru`, `intersectie{…, sursa: extractie|regex}`, `strada_noua`, `strada_noua_text`, `strada_noua_sursa`, `elemente`, `trunchiat`), câte un **`analiza_harta` pe legătură** (aceeași formă ca la racordare + `legatura` (`MUT-…`), `de_la`, `la`, `evita {centru, raza_m}`, `strada_preferata`), `predictie` (`metoda: zona_mutata`, `propuneri`, `aplicate`, `slabe`, `ancore`, `strada_noua`, `legaturi[{element_id, de_la, la, scor, lungime_m, strazi, fara_drum, nivel}]`), `scor` (`decizie: aplicat` dacă ≥ 1 legătură aplicată, altfel `de_verificat`; `neaplicat` fără locație).
- Elemente: `MUT-<event_id>-<n>`, `tip_element: tronson`, `sursa_locatie` = sursa centrului (nu mai `analiza_harta`); aplicat: în `net`, `predictie: null`; predicție: `predictie {metoda: traseu_pe_strazi | linie_dreapta, urmeaza_strada, propunere, scor_propunere, slaba, fara_drum, traseu, alternative, lungime_m, strazi}`.
- Marcate: `de_verificat` (noduri, tronsoane subterane, sau toate dacă nimic nu e aplicat) sau `scos_din_uz` (tronsoane aeriene, când traseul nou e aplicat). `schimbari[].ce`: `de_verificat`, `scos_din_uz`, `predictie`, `adaugat`.

## Decizii
- **„Demontat probabil” = `nivel: scos_din_uz`** pe tronsoanele aeriene marcate, doar când traseul nou e aplicat. E reprezentarea pe care UI-ul o desenează deja (gri punctat, legenda „demontat probabil”), fără câmp nou. Atenție: `contracts/state.schema.json` descrie `scos_din_uz` ca „doar peste pragul de aplicare” (regula de la `activ_demontat`); aici scorul rămâne ≤ 0,35. Descrierea din contract ar trebui lărgită (decide Victor; nu am atins `contracts/`).
- Arbore minim în loc de inel: un inel între ancorele ordonate unghiular dădea ocoliri de 1,1–1,6 km pentru brațe vecine. Arborele păstrează doar legăturile necesare.
- `evita` = cercul de marcare (aceeași rază), ca „traseu care nu intră în zonă” să fie exact ce spune planul; consecința e în tabelul de mai sus.
- Scorul nu depășește nici scorul propunerii (fiabilitate × încredere extracție), deci un text vag (încredere mică) coboară legătura sub plafon.
- Doar raportul executat de mentenanță/investiții aplică (P1); fără excepții pentru semnalat/planificat.
- Calibrare: `EV4-026` și `EV4-041` ies acum `de_verificat` (înainte `neaplicat`). Valorile din `weights.yaml` nu s-au schimbat.

## Limite
- Plafonul `mutare_fire.max_elemente` (25) taie zonele dense: în exemplul de intro 50 de elemente sunt în rază, se marchează 25; restul (mai îndepărtate) rămân nemarcate, deși tronsoanele lor intră în zonă.
- Intersecția trebuie să existe în cache-ul OSM (24 de străzi) și să fie găsită de `backend.geo` (capete la ≤ ~50 m); altfel centrul e mijlocul străzii, iar pe străzi lungi (ex. Șoseaua Principală) mijlocul poate să nu aibă niciun element: atunci `neaplicat` („Niciun element al rețelei în raza de …”).
- Pentru un nod (sursa `id`) zona e mică și de obicei are o singură ancoră: nicio legătură nouă.
- Un singur tronson `MUT-…` per legătură, fără stâlpi noi pe traseu; `latura` din prompt nu se folosește încă; scorul legăturilor lungi e mic (0,18–0,21, roșu) prin construcție.
- `MAX_ANCORE` (6) și `MAX_OCOLIRE_M` (1500) sunt constante în cod (nu în `weights.yaml`); `max_ocolire_m` se poate adăuga în `mutare_fire_document` fără cod.
- Extracția (promptul din `extract.py`): vezi raportul; promptul extrage deja `detalii.intersectie`, `strada_noua`, dar nu un câmp `latura` pentru mutare fire; textele din cache fără aceste câmpuri trec prin regex.

## Pentru Claudiu (UI)
- **Cercul zonei:** `potrivire.rezultat.centru` + `raza_m` (cerc punctat), `text_centru` ca etichetă („intersecția … geocodată, ±15 m”), `sursa_centru` pentru „cum a fost localizat”; zoom 16 (deja în `focus`).
- **Tronsoanele marcate:** `schimbari` cu `ce: de_verificat` (roșu/portocaliu) sau `ce: scos_din_uz` (gri punctat, subțire, „demontat probabil”).
- **Traseul nou:** elementele `MUT-…`: aplicat = linie plină (culoare după `banda`), predicție = punctat; `predictie.traseu` = drumul complet, `predictie.slaba` = punctat subțire, `predictie.fara_drum` = linie dreaptă punctată roșie cu mesajul din `explicatie`.
- **Pasul `analiza_harta`:** unul pe legătură, aceeași formă ca la racordare (`ales.traseu`, `alternative`, `explicatie`), plus `legatura`, `de_la`, `la`, `evita`, `strada_preferata`; poți lega pasul de element prin `legatura` = `element_id`. Nu există `ales.stalpi_noi` desenați ca noduri (nu se creează stâlpi).
