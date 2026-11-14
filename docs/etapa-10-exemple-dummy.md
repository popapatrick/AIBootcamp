# Etapa 10: exemple dummy pentru „Generează exemplu"

Date FICTIVE. Rol A.

## Ce face
`data/reports/exemple-dummy.json` conține texte messy (typo-uri, prescurtări, câmpuri lipsă) pe sursă, pentru butonul „Generează exemplu" din UI și pentru teste de extracție.

## Intrări / ieșiri
- Obiect cu cheile `mentenanta` (10), `investitii` (5), `racordari` (7), `apel_client` (5), `om_teren` (2). `GET /exemple?sursa=<sursa>` (C) întoarce lista de la cheie.
- Item: `{id, titlu, text, data, asteptat: {tip, element_id|null, nota}}`.
- Acoperire: stâlpi existenți (ex. 6414087, 7101969, A-T-014, R-T-006, S-T-006) și inexistenți (9999001..9999003, 8800123); cod de tronson fără prefix (`T-002`); coordonate greșite; apel fără locație; 3 giratorii (`mut-01..03`, tip `mutare_fire`, centru în text, unul fără rază, unul fără centru); 3 cereri de racordare (`cer-01..03`: coordonate fără date GIS, nod casă cunoscut, fără locație); 2 rapoarte de tabletă cu adresă vagă (`mnt-06`, `mnt-07`, „pentru trace"); 2 decizii om (`om-01` accepta, `om-02` respinge).

## Verificare
`.venv/bin/python -m backend.extract.test_extract` verifică forma fișierului (chei, câmpuri, ID-uri unice, date ISO).

## Decizii
- `mutare_fire` și `cerere_racordare` stau sub `mentenanta`/`racordari`, ca să apară în `/exemple?sursa=` (enum-ul API nu are cheie separată). `om_teren` e cheie proprie, neexpusă de `/exemple`.
- `asteptat` e orientativ, nu ground truth.

## Limite
- `NOU-0001/0002` din `om_teren` sunt ID-uri de exemplu; UI trebuie să le înlocuiască cu o predicție reală (decizie reală = `POST /predictii/{id}/decizie`).
- Coordonatele sunt în zona rețelei demonstrative, dar nu sunt verificate pe stradă la nivel de metri.
- Extracția pe textele `apel_client` cu API real (task 3.2) nu e rulată încă.

## Pentru ceilalți
C: citește fișierul direct; câmpul `asteptat` nu trebuie afișat utilizatorului. B: textele cu stâlp inexistent testează calea „nod nou -> predicție".
