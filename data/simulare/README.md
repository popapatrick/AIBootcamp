# data/simulare (rol A)

`puncte-simulare.json` = stâlpi și case SIMULATE (date FICTIVE) pe străzile OSM, generate o dată de `genereaza_puncte.py` și hardcodate; încărcate de motor cu `origine: retea_start`. Nu se regenerează la rulare/demo.

## Format (fixat de B)
```
{"noduri": [{"id": "SIM-001", "lat", "lon", "serie": "serie 5" | "serie 7"}],
 "tronsoane": [{"id": "SIM-L1", "capete": [id, id], "puncte": [[lat, lon], ...], "categorie": "aerian"}]}
```
- `serie 5` = stâlp (40), `serie 7` = casă (15); ID-uri `SIM-001`...`SIM-055` (stâlpii primii).
- Stâlpii sunt lanțuri pe străzi cu nume (pas 35-50 m, max 8 per lanț); tronsonul = porțiunea de stradă dintre doi stâlpi. Primul stâlp al unui lanț se leagă de nodul existent cel mai apropiat dacă e la <= 80 m (capăt = ID real din rețea; acum 1 din 48 de tronsoane). Fiecare casă are un tronson drept spre un stâlp (8-14 m lateral de stradă). Total 48 de tronsoane.

## Garanții (assert-uri în script)
Seed fix `20260811`; fiecare nod la >= 2,5 m de orice nod existent și de celelalte noduri noi (regula nodului nou, `potrivire.distanta_max_element_nou_m`); în raza 3000 m (`zona.raza_max_m`) față de centroidul nodurilor (media punctelor din `network.geojson`); ID-uri unice; capete valide; fără noduri izolate; 40 + 15 noduri.

## Rulare
`.venv/bin/python data/simulare/genereaza_puncte.py` (din rădăcina repo; `data/` nu e pachet). Determinist: două rulări dau același fișier (md5 identic). Limite: stâlpii nu respectă pasul real al rețelei; casele nu au adrese; tronsoanele de pe stradă nu au tip/secțiune.
