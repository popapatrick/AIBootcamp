# Etapa 32: tracking echipe

Plan: `docs/plan-tracking-echipe.md`. OpenSpec: `openspec/changes/tracking-echipe/`. Date FICTIVE.

## Contract (Faza 0)
- `event.schema.json`: tip `tracking_tura`; `tip_sursa_pondere: tracking_gps`; `detalii.tura {tura_id, seed, echipa, puncte[{t, lat, lon}]}`; `detalii.tracking` (scris de motor).
- `state.schema.json`: `predictie.metoda: oprire_tracking`; `ultima_validare_tracking` (dată sau null).
- `weights.yaml`/`weights.limits.yaml`: `fiabilitate_sursa.tracking_gps` 0,60 și secțiunea `tracking` (valorile din plan 2.3). Relații verificate de `verifica_reglaje`: `durata_validare_min < durata_stalp_nou_min`, `raza_validare_m < raza_fara_stalp_m` (strict, lista `rel`) și `stalpi_min <= stalpi_max` (listă nouă `rel_le`, cu `<=`).
- `api.openapi.yaml`: `POST /tracking/genereaza`, `POST /tracking/aplica`, `GET /tracking/ture`. `interfaces.md`: secțiunea „Sesiunea 4b”.
- Verificare: `EXTRACT_CLI=0 .venv/bin/python -m backend.engine.verifica_reglaje --rapid` (fără erori, nicio „cheie nouă fără limite”) și `openspec validate --all`.

## Generator (B1)
**Ce face.** `backend.tracking.genereaza_tura(net, strazi, cfg, echipa, seed, data, scoruri=None, ora_start="08:00:00")` alege 3–5 stâlpi existenți (preferând cei care nu sunt verzi, dacă primește `scoruri`) și un loc fără stâlp pe o stradă, îi ordonează „cel mai apropiat următor” de la un capăt, îi leagă pe străzi OSM (`osm.traseu`), apoi emite puncte GPS la `tracking.pas_s` secunde (viteza `viteza_m_s`, zgomot gaussian `zgomot_m`). Opriri: stâlp 6–10 min la 3–8 m de stâlp; loc fără stâlp 15 min; 1–2 opriri scurte de 1–2 min pe drum.

**Verificare.** `.venv/bin/python -m backend.tracking.smoke_tracking` => `OK: 140 verificări` (cod 0). Acoperă: determinism, 3 echipe, seed diferit, preferința pentru stâlpi nu-verzi, toate punctele în zona de 3 km, fiecare oprire din `plan` regăsită de `gaseste_opriri` cu durată la ±1 min și nicio oprire în plus, opririle scurte sub `durata_validare_min` și nedetectate, locul fără stâlp la >= `raza_fara_stalp_m` de orice nod, puncte de mers fără zgomot la <= 20 m de stradă.

**Intrări.** `net` (rețeaua cu SIM-*), `strazi` (cache OSM), `cfg` (weights), `echipa` (mentenanta|investitii|racordari), `seed`, `data`, opțional `scoruri` {id: scor} și `ora_start`.
**Ieșire.** `{tura_id, echipa, data, seed, puncte[{t, lat, lon}], plan[{lat, lon, durata_min, tip_plan: stalp|fara_stalp|scurta, element_id?}], lungime_m, durata_min, linie_dreapta}`. `tura_id` = `TURA-<echipa>-<data>-<hash8>`. `plan` = doar depanare și teste.

**Decizii.**
- Determinism: `random.Random` seminat din sha256 al (echipă, dată, seed); zgomotul are un flux separat de alegeri.
- Stâlpii sunt aleși într-o zonă restrânsă în jurul unui stâlp-ancoră (rază 500 m, apoi 800/1300/3000), la >= 60 m unul de altul (altfel `gaseste_opriri` le-ar putea lipi), la >= 100 m în interiorul zonei de 3 km (zgomotul nu o depășește).
- Contractul cere stâlpi la <= 40 m de stradă; intern se preferă <= 25 m (mersul rămâne aproape de stradă), cu 40 m ca rezervă.
- În opriri zgomotul e plafonat la 0,4 × `trace.raza_oprire_m` (ca generatorul vechi), deci opririle rămân detectabile.
- Fără drum pe străzi, linie dreaptă, numărată în `linie_dreapta`; se reîncearcă alte alegeri (până la 8) înainte să se accepte o tură cu linie dreaptă.

**Limite.** O tură are ~190–350 de puncte și 47–88 min (mai mult decât cei ~200 de puncte din plan; scade cu `pas_s` mai mare sau cu mai puțini stâlpi). Opririle scurte (1–2 min) sunt sub `trace.durata_min_min` (3 min), deci `gaseste_opriri` nu le vede; motorul trebuie să le trateze doar dacă detectorul le raportează (altfel nu apar în `tracking[]`). Fără cache OSM generatorul ridică `ValueError`. Zgomotul mare (> `trace.raza_oprire_m`) poate pierde opriri, ca la generatorul vechi.

## Motor (B2)
Cod: `backend/engine/tracking.py` (mixin `Tracking` în `GridModel`), ramura `tip == "tracking_tura"` din `apply_event` (`model.py`), teste `backend/engine/smoke_tracking_motor.py` (în `SMOKES` din `verifica_reglaje.py`).

**Ce face.** Evenimentul vine deja structurat (`detalii.tura.puncte`), deci nu trece prin extracție/potrivire: primul pas din StepTrace e `opriri`. Motorul detectează opririle cu `backend.trace.gaseste_opriri` și le clasifică pe fiecare:

| tip | condiție | efect |
|---|---|---|
| `scurta` | durată < `tracking.durata_validare_min` | ignorată |
| `validare` | cel mai apropiat stâlp existent la <= `raza_validare_m`, durată >= `durata_validare_min` | confirmare `scor.confirmare_teren × tracking_gps × calitate` |
| `stalp_presupus` | niciun nod la <= `raza_fara_stalp_m`, durată >= `durata_stalp_nou_min` | predicție `TRK-<event>-<n>` + legătură `TRK-<event>-<n>-L` |
| `neclara` | orice altceva | doar în jurnal |

Stâlp existent = nod din rețea, fără `*-casa`, fără predicții/retrase/scoase din uz. Pentru „niciun nod” se numără toate nodurile (inclusiv casele): nu presupunem un stâlp lângă o casă.

**Validare.** Scorul pornește de la scorul **efectiv la data turei** (regimul de scădere corect: GIS / verificat de om / normal), deci „înainte” e ce arată harta, nu scorul stocat. `delta = 0,25 × 0,60 × calitate`; scor plafonat după sursa locației. Pentru ce nu e GIS, `sursa_locatie` devine cel puțin `coordonate` (poziție GPS, plafon 0,85, `scoring.mai_buna`); GIS rămâne `gis`. Se setează `ultima_verificare` și `ultima_validare_tracking` = data; un element `de_verificat` care trece de `praguri.predictie` devine `in_model`. Motiv: „Confirmat de tura <tura_id> a echipei <echipa>: oprire de <X> min la <Y> m.” plus calitatea și eventuala schimbare de plafon. Elementele `verificat_om`: scor și flag neschimbate, doar motiv în jurnal (decizia evenimentului rămâne `fara_efect` dacă nu s-a întâmplat altceva). Un stâlp se validează o singură dată pe tură (oprirea cea mai lungă); celelalte opriri la el devin `neclara` („numărat o singură dată”).

**Stâlp presupus.** Predicție nod (`predictie.metoda: oprire_tracking`, `sursa_locatie: coordonate`, scor = min(scor propunere, `plafon_stalp_presupus`); scorul propunerii: fiabilitate 0,6, extracție 1,0, potrivire `calitate_dupa_coordonate`, `urmeaza_strada`), plus tronson predicție spre stâlpul existent ales de `analiza_harta.traseu_pe_strazi` (pas `analiza_harta`, `predictie.metoda: traseu_pe_strazi`, scor <= `plafon_locatie.analiza_harta` și <= scorul stâlpului). Niciodată aplicat; omul îl poate accepta/respinge cu decizia obișnuită (grupul nod + legătură; respingerea scade încrederea în metoda `oprire_tracking`). În afara zonei de 3 km sau la < `raza_fara_stalp_m` de un TRK deja presupus: `neclara`.

**Aceeași tură de două ori** (același `tura_id`, pe același model): `fara_efect`, motiv „tura <id> a fost deja aplicată (eveniment <id>)”, fără modificări.

**Decizie și etichete.** `scor_actualizat` dacă a validat un element (nu doar verificat de om), altfel `predictie` dacă a presupus, altfel `fara_efect`. Eticheta în jurnal/timeline: `tracking`; `timeline()[].rezumat` = „Tura echipei mentenanta: 4 stâlpi confirmați, 1 stâlp presupus, 2 opriri scurte.”.

**Verificare.**
```bash
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_tracking_motor   # 40/40 OK
bash scripts/verifica_tot.sh                                              # TOT VERDE (calibrarea neschimbată)
```
Acoperă: validare SIM portocaliu 0,50 -> ~0,63 galben cu sursa `coordonate`; stâlp presupus <= 0,45 cu legătură și `analiza_harta`; oprire scurtă; 20 m (neclară); verificat de om; două opriri la același stâlp; aceeași tură de două ori; scăderea în timp la data turei; GIS; în afara zonei; tură `genereaza_tura` (validări pentru stâlpii din plan, un stâlp presupus la `fara_stalp`, scurte ca `scurta`); determinism; fără regresii.

**Intrări.** Eveniment `{event_id, echipa_sursa, tip: "tracking_tura", data, detalii: {tura: {tura_id, echipa, puncte[{t, lat, lon}]}}}`; `tip_sursa_pondere` e forțat intern la `tracking_gps`, `incredere_extractie` la 1,0.
**Ieșiri.**
- StepTrace `pasi`: `opriri` (`rezultat: {tura_id, echipa, n_puncte, durata_tura_min, opriri[], pe_tip{}}`), `validari_tracking` (`validari[]` = opririle de tip validare, `verificat_om_neschimbat[]`), apoi `analiza_harta` (câte unul pe stâlp presupus, cu `capat: <TRK>`), `predictie` (doar dacă a presupus) și `scor` (rezumatul în `motive[0]`). `schimbari`: `actualizat` cu `scor_inainte` (efectiv) / `scor_dupa` / benzi pe stâlpii validați, `predictie` pe nodul și legătura TRK.
- **Pentru Claudiu (`tracking[]`):** fiecare oprire (în `pasi[nume=opriri].rezultat.opriri` și în `detalii.tracking.opriri`) are `{lat, lon, inceput, sfarsit, durata_min, tip: validare|stalp_presupus|scurta|neclara, t_ajungere (= inceput, ISO), motiv}` și, după caz, `element_id` (stâlpul validat sau `TRK-…`), `distanta_m`, `scor_inainte`, `scor_dupa`, `banda_inainte`, `banda_dupa`; plus `calitate` (validări), `scor_propunere` și `legatura_id` (stâlp presupus), `om: true` (verificat de om, neschimbat). `detalii.tracking` = `{opriri, validari[ids, fără cei verificați de om], presupuneri[ids TRK], ignorate (= nr. opriri scurte), de_ce (rezumatul)}`; se scrie pe obiectul `detalii` al evenimentului primit (mutare pe loc). Pentru un stâlp presupus, `scor_inainte` lipsește (nu exista), `scor_dupa` = scorul predicției.
- `snapshot()`: `properties.ultima_validare_tracking` (doar dacă există). `timeline()`: `eticheta: tracking`, `rezumat` lizibil.

**Decizii.**
- Calitatea după distanță: liniar, 1 la 0 m, 0,5 la `raza_validare_m`: `calitate = max(0,5; 1 − 0,5 × d / raza_validare_m)`. Exemplu: 4 m, 0,87; delta +0,13 (0,50 -> 0,63).
- Opririle scurte: `trace.durata_min_min` se coboară la 1 min (sau la `durata_validare_min` dacă e mai mic) într-o copie a configurației; `weights.yaml` nu se schimbă, iar localizarea din rapoarte (`trace`) rămâne pe 3 min. Sub 1 min nu se raportează nimic (nici ca `scurta`).
- „Înainte” = scorul efectiv la data turei (și în `schimbari`), ca poziția „înainte → după” din UI să coincidă cu ce arăta harta.
- Stâlpul validat e cel mai apropiat stâlp eligibil, nu neapărat cel din `plan` al generatorului (dacă doi stâlpi sunt la câțiva metri, câștigă cel mai apropiat de oprire).
- Legătura stâlpului presupus: un singur tronson, fără stâlpi intermediari noi (ca la `PLAN-*`); capătul existent e cel ales de `traseu_pe_strazi` dintre cei mai apropiați candidați.

**Limite.** Un stâlp presupus în același loc într-o tură ulterioară nu întărește predicția veche (a doua oprire devine `neclara`). Deduplicarea turii e pe model (`ture_aplicate`), nu persistă între rulări. Opririle fără timp (`t` lipsă) dau eroare. Elementele `scos_din_uz` nu se validează. Scenariul (B3) nu conține încă ture; calibrarea nu se schimbă.
