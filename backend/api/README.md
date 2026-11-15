# backend/api/ (proprietar: C)

API FastAPI pentru prototip (etapa 7). Implementează `contracts/api.openapi.yaml`. Date FICTIVE.

- `main.py`: aplicația și endpoint-urile; servește și UI-ul plan B (`frontend/plan-b/`) la `/ui/`.
- `sources.py`: de unde vin datele (motorul lui B → fișierele lui B → eșantionul `data/model/sample/`), ales automat.
- `pipeline.py`: `POST /rapoarte` (extracție → potrivire → predicție → scor); folosește `extract_event` (A) și `apply_event` (B) când există, altfel stub + `match_event` real.
- `POST /predictii/{id}/decizie`: Event `om_teren` dat lui `apply_event`; 404 necunoscută, 409 deja decisă, 400 invalidă. `API_EXTRACTIE=stub` forțează extracția regex. Detalii: `docs/etapa-7b-api-sesiunea-2.md`.
- `GET /locatie-operator-demo?text=` (alias `adresa`): poziție GPS dummy a operatorului din textul lui (`simulata: true`, `indicii`, `zona`, `precizie_m`; 422 cu `detail.mesaj` dacă nu se găsește niciun indiciu); `POST /rapoarte` acceptă `locatie_operator`. Detalii: `docs/etapa-17-locatie-operator-racordare.md`.
- Sesiunea 3 (C1): `POST /rapoarte` acceptă `trace_params` (-> `detalii.trace_params`, validat numeric; are și `dezactivat: bool`); câmpurile motorului (`detalii.geocodare`, `trace_sursa`, `origine`, `predictie.slaba/treapta`, `eronat_prototip`, `adresa_structurata`) trec neatinse; pas „geocodare" în `pasi` doar dacă Event-ul are `detalii.geocodare`. `GET /retea` adaugă `zona {centru, raza_m}` (din `engine.zona.zona_ok` dacă există, altfel centroid + `weights.zona`). `GET /geocodeaza?adresa=` (501 „geocodarea nu e încă în motor (B2/A1)" până există `geocodeaza`). `GET /reguli` = `weights.yaml` ca JSON, read-only.
- Sesiunea 4 (C1-C3, C5; `docs/etapa-30-api-sesiune4.md`): scoase `?scenariu=extrem`, `/trasee-demo`, `trace_params`, `trace`; `/exemple` doar 3 echipe. Noi: `POST /element/{id}/verificare` (501 până motorul știe `verificare_om`), `GET /demo/exemple`, `POST /demo/reset`, `GET /legenda`; `standardizare` și `focus` în `POST /rapoarte` și `GET /evenimente`; `banda`, `verificat_om`, `sursa_locatie`, `t0`, `eticheta_origine` în `GET /retea`. Logica de prezentare: `prezentare.py`.
- Etapa 35 (`docs/etapa-35-api-tracking-stergere.md`): `POST /tracking/genereaza`, `POST /tracking/aplica` (`tracking[]` cu `t_ajungere` în secunde + `focus`), `GET /tracking/ture` (turele în memorie, golite de `/demo/reset`); `POST /element/{id}/stergere` (409 `nu_se_sterge_retea_start`/`deja_sters`, 404 `necunoscut`); `eticheta_text` pe `GET /evenimente`; `DECIZII["sters"]`. Cod: `pipeline.tracking_*`, `pipeline.stergere`.
- `smoke_api.py`: test pe toate endpoint-urile.

```bash
python3 -m venv .venv && .venv/bin/pip install -r backend/api/requirements.txt
.venv/bin/python -m backend.api.smoke_api                    # așteptat: OK: API
.venv/bin/uvicorn backend.api.main:app --reload --port 8000  # UI: http://localhost:8000/ui/
```

## metoda_cod și regex (sesiunea 3)
`pasi[extractie].metoda_cod` = `ai_cache` | `ai_api` | `regex`; `/health.extractie_cod` la fel. Cache miss -> `CacheMiss` -> regex, cu `motiv`. Regex înțelege textele butoanelor Cerere racordare / Fire mutate / Raport tabletă. Detalii: `docs/etapa-7b-api-sesiunea-2.md`.

## Banc de logică (C2/C3)
`python3 -m backend.api.banc_logica [--fisier F] [--json] [--doar-diferente]`: rulează `data/golden/*.json` (sau exemple-dummy) prin `pipeline.proceseaza`; compară cheile din `asteptat` (tip, decizie, nivel, origine, slaba, treapta, banda, sursa_locatie, verificat_om, lungime_m, eronat_prototip, element_id; `eronat_prototip` lipsă = false). Stare: golden 20 cazuri, 14 ok, 6 diferite (vezi `docs/etapa-24-api-sesiune3.md`, C3 runda 3).
