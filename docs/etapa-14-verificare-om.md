# Etapa 14: decizia omului asupra predicțiilor (B)

Date FICTIVE. Schimbarea OpenSpec `verificare-om-predictii`.

## Ce face
Omul care a verificat în teren acceptă sau respinge o predicție AI. Decizia e un eveniment ca oricare altul: `tip: verificare`, `echipa_sursa: om_teren`, `tip_sursa_pondere: om_teren` (0,95 în `contracts/weights.yaml`), `detalii.decizie = {tinta_id, decizie: accepta | respinge, motiv?}`. Trece prin același calcul de scor (`scoring.scor_propunere`, extracție 1, potrivire 1).

- **Acceptă:** predicția (nod prezis plus legăturile lui, sau o legătură plus nodurile ei încă prezise) devine element real în model, scor mare (~0,98), `confirmat_de: om`, `ultima_verificare` = data deciziei. Pentru o propunere de secțiune pe un tronson existent, secțiunea se aplică.
- **Respinge:** predicția și legăturile ei sunt retrase (dispar din snapshot de la data deciziei, rămân în istoric), iar încrederea în metoda care le-a propus scade cu `decizie_om.penalizare_metoda_la_respingere` (0,05, plafon 0,20) la propunerile viitoare cu aceeași metodă.
- **O singură decizie** pe predicție; o a doua, o țintă necunoscută sau o decizie invalidă dau StepTrace cu `decizie: neaplicat` și `eroare: {cod, mesaj}` (`deja_decis` -> 409, `necunoscut` -> 404, `decizie_invalida` -> 400 în API).
- Decizii noi în jurnal/timeline: `aplicat` (acceptare) și `respins`. `schimbari[]` marchează `adaugat` / `actualizat` / `retras`.

## Cum se verifică
```bash
.venv/bin/python -m backend.engine.smoke_engine   # așteptat: OK: 36 verificări
```

## Intrări și ieșiri
Intrare: Event de mai sus, prin `apply_event`. Ieșire: StepTrace cu pașii `potrivire` (metoda `decizie_om`), `predictie` (gol) și `scor`, plus `modificari` și `schimbari`.

## Decizii și limite
- Omul nu ocolește scorul: e doar o sursă cu fiabilitate mare. Un raport ulterior contrar poate contrazice decizia prin regulile normale.
- Acceptarea unui nod prezis ia automat legăturile lui; respingerea le retrage tot pe ele. Acceptarea unei legături singure ia și nodurile prezise de la capete. Acceptarea stâlp cu stâlp a unui lanț (cerere de racordare) vine odată cu B8.
- Nu există conturi sau roluri: „omul" e un buton în demo.

## Ce trebuie să știe ceilalți
- C: `POST /predictii/{id}/decizie` construiește evenimentul de mai sus (echipa_sursa om_teren, incredere_extractie 1.0, status executat, data din cerere sau azi) și îl trimite la `apply_event`; la `eroare.cod` întoarce 409/404/400. Pe hartă: `properties.confirmat_de == "om"` = plin cu marcaj „om"; `nivel == "predictie"` = punctat.
- A: un exemplu de decizie în `exemple-dummy.json` (A7).
