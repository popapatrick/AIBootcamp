# Rapoarte fictive

- Toate fișierele sunt **DATE FICTIVE**: prima linie a fiecărui .txt este `DATE FICTIVE`.
- Nume: `YYYY-MM-DD_<sursa>_<nn>.txt`, de ex. `2026-08-04_mentenanta_01.txt`. `sursa` ∈ `mentenanta`, `investitii`, `racordari`, `apel_client`.
- `index.json`: ground truth pentru fiecare raport.
  - `fisier`, `sursa`, `data`: din numele și conținutul fișierului.
  - `scenariu`: numărul scenariului de test (1–8), sau `null`.
  - `element_id_asteptat`: ID-ul elementului din text, sau `null` dacă nu se poate stabili.
  - `tip_asteptat`: tipul evenimentului așteptat (ex. `nod_lipsa`, `verificare`, `racord_nou`).

## exemple-dummy.json (etapa 10)
Texte messy (typo-uri, prescurtări, câmpuri lipsă; DATE FICTIVE) pentru butonul „Generează exemplu". Obiect cu cheile `mentenanta`, `investitii`, `racordari`, `apel_client` (`GET /exemple?sursa=` întoarce lista) și `om_teren` (decizii ale omului).
- Item: `{id, titlu, text, data, asteptat: {tip, element_id|null, nota}}`. `asteptat` e doar orientativ (nu e ground truth ca `index.json`).
- Include stâlpi existenți (ID-uri din `data/model/network.geojson`) și inexistenți (`9999001`..`9999003`, `8800123`), 3 texte de sens giratoriu (`mut-*`, tip `mutare_fire`, în `mentenanta`), 3 cereri de racordare (`cer-*`, în `racordari`), 2 rapoarte de tabletă cu adresă vagă (`mnt-06`, `mnt-07`, „pentru trace") și 2 decizii (`om-*`; `NOU-0001/0002` sunt ID-uri de exemplu, de înlocuit cu predicții reale).
- Forma e verificată în `backend/extract/test_extract.py`.
