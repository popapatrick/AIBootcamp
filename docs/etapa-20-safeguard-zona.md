# Etapa 20: safeguard-ul zonei prototipului (B, Sesiunea 3)

Date FICTIVE. Feature OpenSpec: `openspec/changes/safeguard-zona-prototip/`.

## Ce face
Nimic nu iese din cercul de `zona.raza_max_m` (3000 m, `contracts/weights.yaml`) în jurul **centroidului rețelei de start**. Un punct din afară e „eronat în cadrul prototipului": decizie `neaplicat`, `eronat_prototip: true` în StepTrace, semnalul `in_afara_zonei_prototip` în pasul „potrivire", motiv cu distanța și limita în „De ce?". Nu intră în model. Fără excepții pe sursă (nici `om_teren`, nici apel client).

## Unde se aplică (acum)
- `backend/engine/zona.py`: `centru_retea(net)` (calculat o dată la încărcarea modelului, reținut în `net["_zona_centru"]`), `zona_ok(lat, lon, net, cfg)` -> `{ok, distanta_m, raza_m, centru}`, `motiv_afara(z)`.
- `match.py`: coordonatele din raport (cu repararea inversării lat/lon și a zecimalelor) se testează pe cerc, nu pe bbox +500 m. Coordonate care rămân în afară = `nepotrivit/absent_din_model` + semnal; `model.py::apply_event` le marchează eronate (doar dacă nu s-a potrivit pe ID).
- `mutare_fire`: centrul zonei. `cerere_racordare`: locația casei (inclusiv clic și poziția operatorului).
- Încă de făcut (alte sarcini): geocodarea (A1/B2), punctele din trace (A3/B4) și tăierea stâlpilor prezicși care ies din zonă (B5) apelează aceeași `zona_ok`.

## Cum se verifică
```bash
.venv/bin/python -m backend.engine.smoke_sesiune2   # 36 verificări, inclusiv 2,9 / 3,1 km, 40 km, mutare_fire, racordare, om_teren
.venv/bin/python -m backend.engine.smoke_engine && .venv/bin/python -m backend.engine.smoke_match
.venv/bin/python -m backend.engine.calibrare        # neschimbat: 13 scor_actualizat, 8 neaplicat, 3 predicție, 2 fără efect, 1 conflict, 1 aplicat, 1 adăugat
```

## Decizii și limite
- Distanța se măsoară față de centroid (decis de Victor), nu față de cel mai apropiat element; o rețea mai mare de 3 km nu poate fi încărcată fără schimbarea razei (intenționat pentru prototip).
- Nodurile adăugate ulterior nu mută centrul (centroidul e înghețat la încărcare).
- Câmpul `zona {centru, raza_m}` în `GET /retea` și `eronat_prototip` în răspuns sunt sarcina C1 a lui Claudiu.
- Ce trebuie să știe ceilalți: A importă `from backend.engine.zona import zona_ok` și întoarce `in_afara_zonei` în loc de coordonate; C expune câmpurile și arată mesajul.
