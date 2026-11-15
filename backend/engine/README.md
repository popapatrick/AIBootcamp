# backend/engine (rol B, Victor)

Motorul modelului: rețeaua în graf, potrivire, scor, decizie, traseu pe străzi (OSM). Date FICTIVE (PTAB 7812).

| Fișier | Ce face | Doc |
|---|---|---|
| `network.py` | citește KMZ-ul, noduri + tronsoane, `clasa` (casa/important/origine/post, aerian/ramura/subteran) | `docs/etapa-1-retea-graf.md`, `etapa-9-aspect-harta.md` |
| `defects.py`, `sample.py` | defectele introduse în model, eșantion pentru C | `docs/etapa-1-retea-graf.md` |
| `match.py` | potrivire pe ID, coordonate, adresă | `docs/etapa-4-potrivire.md` |
| `scoring.py`, `config.py` | scor, praguri, ponderi din `contracts/weights.yaml` | `docs/etapa-5-scor-decizie.md` |
| `model.py` | `GridModel`: apply_event, snapshot, timeline, statistici, decizia omului | `docs/etapa-5-scor-decizie.md`, `etapa-14-verificare-om.md` |
| `sesiune2.py` | mutare fire, demontat, val de apeluri, trace, cerere de racordare | `docs/etapa-15-motor-sesiune2.md` |
| `verificare_om.py` | verificat de om (D10): `verificare_om`, acceptare = verificare, contradicție | `docs/etapa-29-verificat-om.md` |
| `linie_planificata.py` | mixin `LiniePlanificata`: `_planificata` = scara 2 noduri / 2 GPS / ancoră + stradă / fereastră de stradă -> predicție punctată `PLAN-<event>` pe străzi (niciodată aplicat), `neaplicat` fără loc | `docs/etapa-27-analiza-harta.md` (secțiunea „Linie planificată”) |
| `analiza_harta.py` | analiza hărții (V3): `traseu_pe_strazi(tinta, net, cfg, evita, preferate, exclus)` = drum pe graful de străzi OSM de la stâlpii existenți, stâlpi noi la ~40 m, alternative, acuratețe | `docs/etapa-27-analiza-harta.md` |
| `osm.py` | traseu pe străzi, `strazi()` pentru modulele lui A (cache `data/model/osm/`) | `docs/etapa-6-traseu-osm.md` |
| `engine.py` | interfața publică pentru API: `apply_event`, `snapshot`, `timeline`, `statistici`, `aplica_decizie`, `reset` (scenariul extrem `model_scenariu` a fost scos în sesiunea 4) | `contracts/interfaces.md` |
| `calibrare.py`, `fallback_events.py` | rulare pe evenimente reale, rezervă fără date de la A | `docs/calibrare.md` |

## Rulare și verificare
```bash
python3 -m venv .venv && .venv/bin/pip install -r backend/engine/requirements.txt   # o singură dată
.venv/bin/python -m backend.engine.smoke_network    # rețea, clase KMZ
.venv/bin/python -m backend.engine.smoke_match      # 14 verificări
.venv/bin/python -m backend.engine.smoke_engine     # 39 verificări
.venv/bin/python -m backend.engine.smoke_sesiune2   # 66 verificări
.venv/bin/python -m backend.engine.smoke_osm        # 10 verificări
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune4   # 100 verificări (acuratețe V1/V2, analiza hărții V3, căutare pe stradă V6, verificat de om V5)
.venv/bin/python -m backend.engine.calibrare        # decizii pe evenimentele reale
```

## Reguli
Ponderile și pragurile vin doar din `contracts/weights.yaml`. Contractele se schimbă prin commit `contract:`. Ce lipsește se marchează, nu se inventează.

## Sesiunea 3
- `zona.py`: safeguard-ul zonei prototipului (`centru_retea`, `zona_ok`, `motiv_afara`); vezi `docs/etapa-20-safeguard-zona.md`.
- `verifica_reglaje.py`: verifică un reglaj în `contracts/weights.yaml` (limite din `weights.limits.yaml`, diferență de calibrare, smoke-uri, linie pentru board). `scripts/verifica_tot.sh` rulează toate verificările. Vezi `docs/etapa-23-reglaje.md` și `docs/cerere-logica.md`.
- `calibrare.py`: `evenimente()` și `ruleaza(weights)` sunt reutilizate de `verifica_reglaje`.

## Sesiunea 4 (acuratețe realistă; `docs/etapa-26-acuratete-realista.md`)
- `scoring.py`: `scor_la_data(..., regim)` (gis | verificat_om | normal), `regim_stare`, `banda`, `plafon`, `mai_buna`, `text_plafon`, `fmt`, `decizie(..., executat_teren)`.
- `model.py`: KMZ la `acuratete.initial_gis` (`origine: retea_start`, `t0`); SIM-* „din rapoarte mai vechi” cu scor determinist (`_scor_sim`); `banda`,
  `t0`, `sursa_locatie`, `verificat_om` în `snapshot`/`_publica`; `banda_inainte`/`banda_dupa` în `schimbari`; `procent_banda` în `statistici`.
- `sesiune2.py`: `_eff`, `_plafoneaza`, `_sursa_eveniment`, `_sursa_din_geocodare`, `_executat_teren`; plafon la racordare și mutare fire.
- `smoke_sesiune4.py`: verificările V1/V2.

## Căutare pe stradă (V6, partea 2; `docs/etapa-31-cautare-strada.md`)
Adresă fără ID/coordonate -> `fereastra_strada` (backend.geo) -> candidați din fereastră -> potrivit / predicție / de verificat / element nou / pin.
- `sesiune2.py`: `_foloseste_geocodare` (ancore + `_fereastra` internă), `_cautare_strada` (pasul `cautare_strada`), `_candidati_fereastra`,
  `_rezultat_cautare` (predicție „probabil acest element”, de verificat pe fereastră, pin `VER-<event_id>`), `_inregistreaza_ancora`,
  `_text_indiciu`, `_sursa_fereastra`, `_fara_marker`; constantele `TIPURI_CAUTARE` și `TIPURI_NOI`.
- `model.py`: `self.ancore`, `self.pinuri`, ramura din `apply_event` (înlocuiește regula „precizie > 15 m -> nepotrivit” pentru `TIPURI_CAUTARE`).
- **Tipuri noi (`nod_lipsa`, `racord_nou`; decizia lui Victor, 15 nov.):** mereu element nou la `fereastra.punct`, indiferent câți stâlpi sunt în fereastră (0, 1, 2–4, > 4); stâlpii existenți nu se potrivesc și nu dau `de_verificat`, ci apar informativ (`candidati` cu `ales` null în pas, `predictie.alternative` sau „De ce?” + `stalpi_existenti_in_fereastra` pe elementul nou). Regulile pentru tipurile despre elemente existente rămân (1 / 2–4 / > 4 / 0).
- `smoke_sesiune4.py`: `teste_cautare_strada()` (29 verificări: 1 candidat, 2–4, peste maxim, 0 candidați, pin, element numit, ancore, doar stradă, determinism).

## Analiza hărții (V3; `docs/etapa-27-analiza-harta.md`)
- `analiza_harta.py`: `traseu_pe_strazi(tinta, net, cfg, evita=None, preferate=None, exclus=None, *, sursa=None, de_la=None, strazi=None)`. Pură, deterministă; graful de străzi vine din `osm.strazi()` (cu nume). `evita` și `preferate` sunt pentru V4 (mutare fire).
- `sesiune2.py::_cerere_racordare`: treapta 3 = analiza hărții (pas nou `analiza_harta` în `pasi`, înainte de `predictie`); treapta 4 doar fără stâlp în `raza_cautare_m`. Elementele prezise: `predictie.metoda: traseu_pe_strazi`, `predictie.traseu`, `predictie.alternative`, stâlpii cu `sursa_locatie: analiza_harta`.
- `model.py::_propune_element_nou`: nod nou la > 80 m de orice tronson și legătură > 80 m care ar fi linie dreaptă -> legătura pe străzi, cu stâlpi intermediari (`NOU-<id>-<vecin>-S<k>`) și pas `analiza_harta` (cu `vecin`).

## Fire mutate din document (V4; `docs/etapa-28-mutare-fire-document.md`)
- `mutare_fire_text.py`: regex de rezervă pe text (`intersectie_din_eveniment`, `strada_noua_din_eveniment`, `strada_din_eveniment`, `nume_canonic`); pur, fără AI.
- `sesiune2.py`: `_centru_mutare` (centru: `detalii.centru` > coordonate > intersecție geocodată > nod din ID > stradă), `_ancore_mutare`, `_legaturi_mutare` (arbore de ocoliri pe străzi, `traseu_pe_strazi(..., evita=zona, preferate=[strada_noua])`), `_mutare_fire` (marcare, scor, aplicare P1 doar executat de mentenanță/investiții, tronsoanele aeriene vechi `scos_din_uz` = „demontat probabil”); constantele `MAX_ANCORE`, `MAX_OCOLIRE_M`. Elementele `MUT-<event>-<n>`: `predictie.metoda: traseu_pe_strazi | linie_dreapta`; un pas `analiza_harta` pe legătură. Racordare: treptele 1-2 înmulțesc scorul cu `factor` al analizei când lanțul merge pe străzi.
- `smoke_sesiune4.py`: `teste_mutare_fire_document()` (21 de verificări). `smoke_sesiune2.py`: aserțiunea pe `predictie.metoda` a traseului propus acceptă acum `traseu_pe_strazi`/`linie_dreapta` (era `zona_mutata`).

## Linie planificată și distribuția culorilor (sesiunea 4)
- `linie_planificata.py`: vezi tabelul de mai sus; teste în `smoke_sesiune4.py::teste_linie_planificata` (15 verificări). Constantele `LINIE_IMPLICITA_M`, `LINIE_MAX_M`, `LEGAT_MAX_M` sunt în cod.
- `verifica_reglaje.py::distributie_culori`: elementele `scos_din_uz` nu sunt rețea (nici în procent, nici în predicții); se întorc separat ca `scoase_din_uz` (`docs/calibrare.md`).
