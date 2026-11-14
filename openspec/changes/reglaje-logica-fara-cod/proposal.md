# Proposal

## Why

Logica trebuie blocată treptat ca după să ne concentrăm pe UI. Claudiu (și oricare altul) trebuie să poată face mici schimbări de logică de pe laptopul lui, fără o implementare mare și fără să atingă codul motorului. Tot ce e reglabil trebuie să fie date, nu cod.

## What Changes

- „Zonă reglabilă": valorile numerice din `contracts/weights.yaml` pot fi schimbate de oricine, cu commit `reglaj:`, dacă `python -m backend.engine.verifica_reglaje` trece.
- `contracts/weights.limits.yaml`: minim și maxim pentru fiecare valoare. Scriptul refuză chei noi/șterse și valori în afara limitelor.
- `verifica_reglaje` rulează calibrarea pe evenimentele de bază și arată diferența față de referință (`data/golden/calibrare-referinta.json`), rulează smoke-urile, și tipărește o linie gata de lipit în `board/`.
- Orice altceva (alt comportament, regulă nouă, câmp nou) se cere prin „cerere de logică" în `board/` cu `@Victor`, în formatul fix din `docs/cerere-logica.md`; Victor o implementează sau o respinge.
- Banc de test al logicii fără UI: `backend/api/banc_logica.py` (C) rulează texte prin pipeline și tipărește tabel: metodă, coordonate, acuratețe, nivel, motiv.
- Înghețare: când `scripts/verifica_tot.sh` e verde și datele de aur sunt create, Victor pune tag-ul `logic-v1`; după el, logica se schimbă doar prin reglaj sau cerere aprobată.

## Capabilities

### New Capabilities
- `reglaje-logica`: schimbarea valorilor din configurație cu validare, banc de test și înghețarea logicii.

### Modified Capabilities

## Impact

- B: `backend/engine/verifica_reglaje.py`, `contracts/weights.limits.yaml`, `scripts/verifica_tot.sh`, `docs/cerere-logica.md`, tag `logic-v1`.
- A: `data/golden/` (texte de aur și rezultate așteptate pentru geocodare, trace, racordare).
- C: `backend/api/banc_logica.py`, `GET /reguli` (read-only) în API, ghid în `docs/etapa-23-reglaje.md`.
- CLAUDE.md: regula „reglaj" (excepție la „scrii doar în folderele tale": `contracts/weights.yaml`, doar valori).
- În afara scopului: editarea prompturilor AI de către alt rol decât A; endpoint de scriere a configurației.
