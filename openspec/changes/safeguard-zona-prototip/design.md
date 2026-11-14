# Design

## Decisions

- Centrul: centroidul nodurilor rețelei de start (calculat o dată la încărcarea modelului, nu hardcodat); raza din `weights.yaml` (3000 m). Distanța se măsoară față de centroid (decis de Victor), nu față de cel mai apropiat element.
- `zona_ok(lat, lon, net, cfg) -> {ok, distanta_m}` e funcție pură în `backend/engine/zona.py`; A o importă pentru geocodare și trace.
- Rezultatul unui punct din afară: `decizie: neaplicat`, `nivel: null`, `eronat_prototip: true`, semnal `in_afara_zonei_prototip`, motiv cu distanța și limita. Nu se șterge din jurnal.
- Fără excepții pe sursă: nici `om_teren`, nici apelul clientului nu pot aduce un punct în afara zonei.
- Un eveniment cu mai multe puncte (racordare cu lanț) e eronat dacă locația casei e în afară; stâlpii prezicși care ar ieși din zonă se taie.

## Risks / Trade-offs

- O rețea reală mai mare decât 3 km nu poate fi încărcată fără schimbarea razei; e intenționat pentru prototip.
