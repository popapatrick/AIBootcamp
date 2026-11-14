# Etapa 19: traseu generat la raport (A + B, Sesiunea 3)

Date FICTIVE. Feature OpenSpec: `openspec/changes/traseu-generat-din-raport/`.

## Ce face
- **A:** `backend/trace/genereaza.py::genereaza_traseu(punct, strazi, params, seed)`: traseu simulat de 60 min, determinist pe seed, cu parametri (puncte, zgomot, durată oprire, acoperire, decalaj).
- **B (motor):** `sesiune2.py::_trace_generat`. La orice raport de echipă (mentenanță/investiții/racordări; nu apel, nu om, nu verificare) cu locație (coordonate sau adresă geocodată), fără ID și fără trace real, motorul generează traseul lângă punct (seed = `event_id`), îl redescoperă cu `localizeaza` și calculează `factor_trace` = 1 + bonus − penalizări:
  - bonus (≤ `trace_generat.bonus_max`) crește cu durata opririi peste `trace.durata_min_min` și scade cu zgomotul (zero la `zgomot_max_bonus_m`);
  - penalizare dacă oprirea e la peste `toleranta_adresa_m` de locația din raport (contradicție) sau nu există oprire;
  - penalizare dacă acoperirea e sub `acoperire_min`.
  Factorul înmulțește calitatea potrivirii/locației (nu schimbă locația). Pasul „trace" (`sursa: simulat`) apare în StepTrace; `detalii.trace_sursa: simulat`, `detalii.trace_factor`.
- Parametrii implicit vin din `weights.yaml` (`trace_generat`); se suprascriu per raport cu `detalii.trace_params`; `{"dezactivat": true}` oprește generarea.

## Cum se verifică
```bash
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune2   # blocul „trace generat": bonus, zgomot, decalaj, acoperire, dezactivare, determinism
.venv/bin/python -m backend.trace.smoke_trace
.venv/bin/python -m backend.engine.calibrare                       # deciziile de bază neschimbate
```

## Decizii și limite
- Traseul e generat în jurul punctului primit, nu al rezultatului geocodării ca „adevăr"; de aceea contradicția apare doar când parametrii (decalaj) o produc. E un semnal complementar, etichetat „simulat".
- Valorile bonusului și penalizărilor sunt puncte de plecare, necalibrate pe date reale; se reglează prin `reglaj:`.
- Ce trebuie să știe ceilalți: C trece `trace_params` din `POST /rapoarte` și afișează pasul „trace" și `trace_sursa` (C1).
