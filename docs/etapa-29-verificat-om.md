# Etapa 29: verificat de om (D10, V5)

Rol B (motor). Date FICTIVE. Cod: `backend/engine/verificare_om.py` (mixin `VerificareOm` în `GridModel`), cârlige în `model.py` și `sesiune2.py`.

## Ce face
Un om poate marca în teren orice element ca „verificat”. Evenimentul `tip: verificare_om` (`echipa_sursa: om_teren`, `detalii.tinta_id`, opțional `detalii.motiv`) vine din `POST /element/{id}/verificare` sau dintr-un text de mentenanță extras de AI cu `tinta_id`.

- **Element existent (orice origine):** `scor = verificat_om.scor` (1,0), `verificat_om: true`, `verificat_om_data` = data evenimentului, `confirmat_de: "om"`, `ultima_verificare` = data, `nivel: in_model`, marcajul „probabil acest element” (`predictie.metoda = cautare_strada`) șters. Motiv: „Verificat de om în teren (<data>)[: <motiv>]. Scor 1,00.” Fără plafon de sursă (regim `verificat_om`, ca GIS).
- **Predicție** (`NOU-`, `MUT-`, `PLAN-`... din `self.predictii`): se aplică în model (grupul nod + legături, ca la acceptare) și toate elementele grupului sunt verificate. Se înregistrează în `self.decizii` (o a doua decizie dă `deja_decis`).
- **Pin `VER-...`** (`self.pinuri`): devine **nod real în model**, verificat (scor 1,0, geometria pinului). Pinul dispare din `self.pinuri`.
- **Fără `tinta_id`:** dacă raportul are `referinta.element_id` sau adresă, se folosește potrivirea normală (inclusiv căutarea pe stradă). Se verifică doar un element **sigur** (potrivit, fără predicție/fereastră cu mai mulți candidați). Altfel `neaplicat`, motiv: „nu e niciun element sigur de verificat ...”.
- **`tinta_id` inexistent / retras / scos din uz:** `neaplicat`, `eroare.cod = tinta_necunoscuta`.
- **„Acceptă” (`_decizie_om`)** pe o predicție (nod/legături sau propunere de secțiune) = verificare de om: `verificat_om: true`, scor 1,0 (înainte: scorul propunerii, ex. 0,75–0,99). „Respinge” neschimbat.
- **Contradicție ulterioară:** orice raport care scade scorul unui element verificat (apel de client / semnal negativ, conflict de secțiune, semnal sau aplicare de demontare, ID+coordonate contradictorii) pune `verificat_om: false`, `verificat_om_data: null`; scorul = scor efectiv (cu regimul `verificat_om`) + efectul contradicției; motivul spune „Verificarea de om din <data> a fost contrazisă de <event_id>.” Un raport care confirmă NU șterge flag-ul. `confirmat_de` rămâne `om` (istoric).
- **Scăderea în timp:** `scoring.regim_stare` dă regimul `verificat_om` (−0,01/30 zile, minim 0,95); verificat de test (la +365 zile scorul e 0,95).

## Decizii
- Decizia din StepTrace/jurnal e **`aplicat`** (există deja în `DECIZII` din `backend/api/prezentare.py`, „Aplicat în rețea”: nu lipsește niciun text, API-ul nu cere schimbări). Eticheta din jurnal/timeline e **`verificat_om`** (`jurnal[].eticheta`, `jurnal[].tip = "verificare_om"`), pentru ca UI-ul să poată afișa „Verificat de om”.
- `schimbari[].ce`: `actualizat` pe element existent, `adaugat` pe predicție/pin aplicat.
- Pinul devine nod (varianta cea mai simplă și sigură: nu se pierde locul estimat, iar omul a confirmat că acolo e un stâlp).

## Verificare
```bash
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune4   # 72/72 OK (20 verificări V5 noi)
bash scripts/verifica_tot.sh                                       # TOT VERDE
```
Testele V5 acoperă: galben -> 1,0 verde cu dată; +365 zile >= 0,95; apel contradictoriu; confirmare care nu șterge flag-ul; demontare; tronson GIS; fără `tinta_id` (cu/fără ID în referință); `tinta_id` inexistent; predicție `NOU-*`; „Acceptă”; pin `VER-*`; marker `cautare_strada`; determinism; `POST /element/{id}/verificare` = 200.

## Limite
- Propunere de secțiune încă deschisă pe un tronson (`propunere_proprietate`): verificarea pune scorul/flag-urile dar lasă nivelul și propunerea (decide omul prin „Acceptă”).
- Verificarea pe o predicție o aplică chiar dacă planificată (omul a văzut-o în teren).
- Contradicția nu acoperă schimbarea de secțiune aplicată (raport executat care schimbă secțiunea): doar conflictul.
- Un singur om, fără istoric de verificări multiple (se ține ultima).

## Pentru Claudiu (API/UI)
- `POST /element/{id}/verificare` merge fără schimbări în API (`_motorul_stie_verificare_om` găsește `verificare_om` în motor): 200 cu StepTrace, `decizie: aplicat`.
- În `GET /retea`: `verificat_om`, `verificat_om_data`, `banda` vin din `snapshot`; insigna „Verificat de om” = `verificat_om: true`. După o contradicție flag-ul devine `false`.
- Timeline: `eticheta: "verificat_om"` (nou), `decizie_om` rămâne doar pentru accept/respinge.
- Un pin `VER-...` verificat apare în `GET /retea` ca nod normal (același ID).
