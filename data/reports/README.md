# Rapoarte fictive

- Toate fișierele sunt **DATE FICTIVE**: prima linie a fiecărui .txt este `DATE FICTIVE`.
- Nume: `YYYY-MM-DD_<sursa>_<nn>.txt`, de ex. `2026-08-04_mentenanta_01.txt`. `sursa` ∈ `mentenanta`, `investitii`, `racordari`, `apel_client`.
- `index.json`: ground truth pentru fiecare raport.
  - `fisier`, `sursa`, `data`: din numele și conținutul fișierului.
  - `scenariu`: numărul scenariului de test (1–8), sau `null`.
  - `element_id_asteptat`: ID-ul elementului din text, sau `null` dacă nu se poate stabili.
  - `tip_asteptat`: tipul evenimentului așteptat (ex. `nod_lipsa`, `verificare`, `racord_nou`).
