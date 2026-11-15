# Etapa 22: racordare cu rezerve, fără „neaplicat” (A + B, Sesiunea 3)

Date FICTIVE. Feature OpenSpec: `openspec/changes/racordare-fara-neaplicat/`.

## Ce face
- **Locația casei** (motor, `sesiune2.py::_cerere_racordare`): coordonate din text > clic pe hartă > adresă geocodată (`sursa_locatie: adresa`, scor limitat de acuratețea geocodării) > poziția simulată a operatorului. Trace-ul generat nu se aplică cererilor de racordare (locația lor e a casei, nu a unui stâlp).
- **Lanțul** (A, `backend/racordare.prezice_lant`): treapta 1 nod în `raza_nod_m`; 2 în `raza_extinsa_m`; 3 cel mai apropiat nod din rețea, linie dreaptă; 4 niciun nod, doar casa. `treapta` apare în pasul „predicție" și în `predictie.treapta`.
- **Scorul** scade cu treapta prin factorii din `weights.yaml`: `factor_raza_extinsa`, `factor_linie_dreapta_lunga`, `factor_doar_casa` (`factor_fara_strada` doar la treptele 1-2, ca să nu se dubleze penalizarea).
- **Predicție slabă**: sub `praguri.predictie` nu mai e `neaplicat`; apare ca predicție cu `predictie.slaba: true` (punctată în UI), niciodată aplicată fără decizia omului. Sub `racordare.prag_afisare` rămâne doar punctul casei (fără lanț), tot ca predicție slabă. Motivul spune scorul, treapta și ce lipsește.
- **Singurele `neaplicat`:** fără locație deductibilă (motiv „locația casei", cu sursele încercate) și în afara zonei prototipului (`eronat_prototip`).

> **Sesiunea 4 (V3, `docs/etapa-27-analiza-harta.md`): treapta 3 nouă.** Treapta 3 nu mai e „linie dreaptă la cel mai apropiat nod": e **analiza hărții pe străzi** (drum pe graful OSM, stâlpi la ~40 m, refolosire stâlpi existenți). Fără drum pe străzi rămâne linie dreaptă, cu scorul `analiza_harta.fara_drum`. Treapta 4 = niciun stâlp existent în `analiza_harta.raza_cautare_m` (doar casa). Scorul treptei 3 = scorul propunerii × `factor` din analiză (scade cu lungimea drumului), nu `factor_linie_dreapta_lunga` (rămas doar ca rezervă în cod). Treptele 1-2 neschimbate.

## Cum se verifică
```bash
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune2   # blocul „racordare cu rezerve” (58 verificări)
.venv/bin/python -m backend.racordare.smoke_racordare
.venv/bin/python -m backend.engine.calibrare                       # deciziile de bază neschimbate
```

## Decizii și limite
- Scara pentru locație include doar sursele pe care le are cererea; „trace” nu e folosit aici (decizie de proiectare, vezi mai sus).
- Predicțiile slabe pot aglomera harta; UI-ul le poate filtra după `slaba`/`scor` (C4).
- Factorii și `prag_afisare` sunt puncte de plecare, necalibrate; se reglează prin `reglaj:`.
- Ce trebuie să știe ceilalți: C expune `predictie.slaba` și `treapta` (C1) și afișează predicția slabă punctat și subțire (C4, prompt netrimis).
