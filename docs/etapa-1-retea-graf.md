# Etapa 1: rețeaua în graf (B)

Date FICTIVE (PTAB 7812).

## Ce face
`backend/engine/network.py` citește `data/network/Retea_JT_PTAB_7812.kmz` și construiește rețeaua: 1 post de transformare, 265 noduri, 264 tronsoane, cu capetele fiecărui tronson legate de nodul cel mai apropiat. `backend/engine/defects.py` produce versiunea pe care o „crede" modelul, cu două defecte.

## Cum se rulează și se verifică
```bash
python3 -m backend.engine.network       # scrie data/model/network.geojson
python3 -m backend.engine.defects       # scrie data/model/network_model.geojson și defects.json
python3 -m backend.engine.smoke_network # așteptat: OK: 1 post, 265 noduri, 264 tronsoane, ...
```
Doar biblioteca standard Python 3.

## Fișiere produse (`data/model/`)
- `network.geojson`: realitatea (tot ce e în KMZ).
- `network_model.geojson`: ce știe modelul GIS, fără nodul lipsă și cu secțiunea veche la un tronson.
- `defects.json`: adevărul despre defecte, folosit de A pentru rapoartele dummy.

## ID-uri (important pentru rapoarte)
- **Noduri:** codul din KMZ, numeric (ex. `6925190`). Nu are forma `6-031`.
- **Post:** `DX10-2-099812` (PTAB 7812).
- **Tronsoane:** codurile `T-001` se repetă în cele 3 categorii din KMZ, deci id-ul unic are prefix: `A-T-001` (aerian), `R-T-001` (ramuri aeriene), `S-T-001` (subteran). Codul original e în `cod_original`.
- Un raport poate spune „T-054" fără prefix; potrivirea (etapa 4) trebuie să trateze asta ca ambiguu.

## Defecte introduse (din `defects.json`)
1. **Nod lipsă** `6925190`, împreună cu tronsoanele `A-T-054` și `A-T-057`; vecinii sunt `6513200` și `7824201`. Frângere de ~121 de grade în nod, deci un colț de stradă: linia dreaptă între vecini ar greși.
2. **Cablu înlocuit nerecordat:** `A-T-002` are în model `TYIR 3x35+54,6 OL-Al`, iar în teren `TYIR 3x70+54,6 OL-Al`.

## Decizii
- Capetele se leagă de nod la cel mult 12 m: cablurile subterane (desenate punctat în KMZ, ca mai multe segmente scurte, pe care le-am unit) se opresc la 5–10 m de nod. Cu 3 m rămâneau 7 capete nelegate.
- Realitatea și modelul sunt fișiere separate; originalul nu e modificat.

## Limite cunoscute
- Legătura nod–tronson e dedusă din coordonate, nu din KMZ (nu are conexiuni explicite).
- Nu am verificat vizual pe hartă; verificarea e numerică (smoke test).
- Scenariul 3 (coordonată greșită) nu cere defect în model; vine doar din rapoartele lui A.

## Ce trebuie să știe ceilalți
- A: folosește ID-urile de mai sus și `defects.json` pentru scenariile 1 și 2.
- C: `network.geojson` și `network_model.geojson` pot servi ca eșantion de hartă până apar instantaneele cu scoruri.
