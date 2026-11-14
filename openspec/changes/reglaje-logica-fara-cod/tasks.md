# Tasks

## 1. Unelte (B)

- [x] 1.1 (B6) `contracts/weights.limits.yaml` (min/max pentru fiecare valoare) și `backend/engine/verifica_reglaje.py` (chei, tipuri, limite, diferență calibrare, smoke-uri, linie pentru board)
- [x] 1.2 (B6) `scripts/verifica_tot.sh`: toate smoke-urile și testele; `docs/cerere-logica.md` (șablon)
- [ ] 1.3 (B7) Referința `data/golden/calibrare-referinta.json` și tag `logic-v1` după verde

## 2. Date de aur (A)

- [x] 2.1 (A6) `data/golden/`: texte cu adresă/stradă/reper, coordonate așteptate, tipuri așteptate, cazuri de trace și de racordare

## 3. Banc și API (C)

- [ ] 3.1 (C2) `backend/api/banc_logica.py`: rulează textele din `data/golden/` prin pipeline, tabel + sumar
- [x] 3.2 (C2) `GET /reguli` read-only în API, teste în `smoke_api.py`

## 4. Reguli de lucru

- [x] 4.1 (B6) CLAUDE.md și fișierele agenților: excepția `reglaj:` (doar `weights.yaml`, doar valori) și procedura de cerere

## 5. Documentație

- [ ] 5.1 `docs/etapa-23-reglaje.md` (ghid pentru Claudiu: ce poate schimba, cum verifică, ce face când nu poate), README-uri, board
