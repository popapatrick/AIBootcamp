# Etapa 26: acuratețe realistă (Sesiunea 4, V1 + V2, rol B)

Date FICTIVE. Implementare în `backend/engine/{scoring,model,sesiune2}.py`. Valorile vin din `contracts/weights.yaml`
(`acuratete`, `retea_start`, `plafon_locatie`, `culori`, `verificat_om`); nu s-a schimbat niciun fișier din `contracts/`.

## Ce face
**V1, modelul de acuratețe**
1. *Scădere pe regim* (`scoring.scor_la_data(..., regim)`): `gis` = `acuratete.scadere_gis_per_30_zile` (−0,01), nu sub
   `minim_gis` (0,85); `verificat_om` = `verificat_om.scadere_per_30_zile`, minim `verificat_om.minim`; altfel
   `scor.scadere_per_30_zile` (−0,05), fără minim. Un scor deja sub minim nu e ridicat:
   `eff = max(min(scor, minim), scor + rata*zile/30)`. Regimul se deduce din stare (`scoring.regim_stare`): `verificat_om`
   dacă `verificat_om` e true, `gis` dacă `origine == retea_start` și `sursa_locatie == gis`, altfel normal.
2. *KMZ*: pornește la `acuratete.initial_gis` 0,95, `origine: retea_start`, `t0: true`, `sursa_locatie: gis`, `verificat_om: false`.
3. *Plafon după sursa locației* (`scoring.plafon`, `plafon_locatie`): orice element creat dintr-un raport primește `sursa_locatie`
   și scorul propunerii e `min(scor, plafon)`; motivul spune „Acuratețe plafonată la 0,70: locația vine dintr-o adresă cu număr.”
   Mapare: ID în raport -> `id`; coordonate/clic/trace -> `coordonate`; geocodare -> `intersectie` | `adresa_numar` | `strada` | `reper`
   (din `geocodare.tip` dacă există, altfel din `motiv`); poziție dedusă din vecini -> `analiza_harta`; stâlpii și cablurile
   prezise ale unei racordări și traseul propus la mutare fire -> `analiza_harta`; casa din racordare -> sursa ei
   (coordonate/clic -> `coordonate`, adresă -> ca mai sus, operator simulat -> `strada`); linie planificată -> `id` (nodurile date prin ID).
4. *Confirmare cu sursă mai bună* (`_efect_pe_element`): un raport cu ID sau coordonate (potrivire `id`/`coordonate`) ridică
   `sursa_locatie` a unui element care nu e GIS (ordine: coordonate = id > adresa_numar > intersectie > strada > analiza_harta > reper)
   și deci plafonul; scorul unei confirmări e plafonat la plafonul curent. GIS și „verificat de om” nu au plafon.
5. *P1*: `scoring.decizie(..., executat_teren=True)` folosește pragul `acuratete.aplicat_raport_executat` (0,50). Se activează
   (`_executat_teren`) pentru `status == executat` și echipa `mentenanta`/`investitii`, sau `racordari` doar la `racord_nou`.
   Rămân predicții: planificat, poziția dedusă din vecini, cererile de racordare, raportul „semnalat”.
6. *Bandă*: `scoring.banda(scor, w)` (`verde` ≥ 0,80, `galben` ≥ 0,60, `portocaliu` ≥ 0,40, altfel `rosu`). În `snapshot()` (properties),
   `_publica` (StepTrace) și `schimbari[]` (`banda_inainte`, `banda_dupa`; `null` pentru element nou). `snapshot()` mai pune
   `t0`, `sursa_locatie`, `verificat_om`, `verificat_om_data`. `statistici()` are `procent_banda`.
7. *Mesajul de scădere* din `stare_efectiva` spune rata regimului („scade cu 0.01 la 30 de zile (rețea GIS)”).

**V2, rețeaua de start mixtă** (`retea_start.sim_din_rapoarte == 1`): elementele `SIM-*` (noduri și tronsoane) sunt
`origine: generat_model`, `t0: true`, regim normal; scorul se alege determinist pe ID:
`u = int(md5(id), 16) % 10000 / 10000`; `u < fractie_galben` -> `scor_galben`, `adresa_numar`; `u < fractie_galben + fractie_portocaliu`
-> `scor_portocaliu`, `strada`; altfel `scor_rosu`, `strada`. Motiv: „Element din rapoarte mai vechi (nu din GIS), acuratețe 0,68.”
Cu `sim_din_rapoarte: 0` sunt tratate ca GIS. Centrul zonei de 3 km se calculează ca înainte, din toate nodurile de start.

## Cum se verifică
```bash
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune4   # așteptat: 23/23 OK
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_engine     # 39 OK
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune2   # 66 OK
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_match      # 14 OK
EXTRACT_CLI=0 bash scripts/verifica_tot.sh
```
Distribuție pe benzi (630 elemente, rețeaua neatinsă): la 2026-08-01 GIS 100 % verde, SIM 46,6 % galben / 38,8 % portocaliu / 14,6 % roșu;
la 2026-11-15 GIS 100 % verde (0,915), SIM 46,6 % portocaliu / 53,4 % roșu; total 2026-11-15: 83,7 / 0 / 7,6 / 8,7 %.
Notă: la 2026-11-15 un KMZ neatins are 0,915 (0,95 − 0,01·106/30), nu ≥ 0,92 cum scria enunțul; testul cere ≥ 0,91.

## Intrări / ieșiri
Intrări: evenimentele existente (nicio schimbare de schemă), `detalii.geocodare` (acum cu `tip` opțional păstrat). Ieșiri noi pentru API (Claudiu):
`banda`, `t0`, `sursa_locatie`, `verificat_om`, `verificat_om_data` în properties din `snapshot()` și (parțial) în `modificari[]`; `banda_inainte`/`banda_dupa`
în `schimbari[]` și în timeline; `procent_banda` în `statistici()`. Toate sunt aditive; `origine` rămâne: KMZ `retea_start`, SIM-* și tot ce adaugă sistemul `generat_model`.

## Decizii și limite
- `banda_inainte` folosește scorul brut dinaintea evenimentului (ca `scor_inainte`), nu cel efectiv la data evenimentului.
- Decizia omului (`accepta`) nu e plafonată (e verificare în teren); păstrează `sursa_locatie`.
- Cererea de racordare: decizia (in_model/predicție) se ia pe scorul plafonat după sursa casei; fiecare element are propriul scor
  (stâlpi/cabluri ≤ 0,40). Cererile rămân în practică predicții (status planificat sau scor sub prag).
- `verificat_om` e doar prevăzut (cheie și regim); evenimentul `verificare_om` vine la V5.
- Elementele fără `sursa_locatie` (stări vechi) nu sunt plafonate.
- Traseul real al tabletei (`trace_rezumat`) e tratat ca `coordonate`.

## Aserțiuni vechi schimbate (efect intenționat)
- `smoke_engine`: „nod lipsă, text liber -> predicție”, „înlocuire din text liber -> predicție”, pregătirile pentru decizia omului (ev. 70, 74, 76) foloseau
  `executat` cu scor ~0,6–0,7, acum aplicat de P1; trecute pe `semnalat`; adăugat testul P1 pe `executat`. „scade în timp” (GIS 0,95 -> de_verificat) înlocuit cu
  GIS nu coboară sub 0,85 + SIM-* devine `de_verificat`.
- `smoke_sesiune2`: testele de origine (KMZ = `retea_start` 0,95; SIM-* = `generat_model`, `t0`).
- `verifica_reglaje`: diferențele de calibrare față de referință sunt așteptate (GIS 0,95, plafon, prag 0,50); referința NU a fost rescrisă.
