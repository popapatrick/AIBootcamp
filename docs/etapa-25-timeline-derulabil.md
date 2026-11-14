# Etapa 25: timeline derulabil (B motor, C interfață)

Date FICTIVE. Feature OpenSpec: `openspec/changes/timeline-derulabil/`. Decizii luate cu omul: panou vertical lateral; scroll mută harta automat; scenariul extrem; fiecare intrare arată dată, etichetă, decizie, scor înainte -> după, elemente atinse evidențiate, „De ce?" la clic.

## Ce face (partea B, gata)
`GridModel.timeline()` (deci `engine.timeline()` și `GET /evenimente`, cu sau fără `?scenariu=extrem`) întoarce pe fiecare intrare, pe lângă `{data, event_id, decizie, tip, eticheta, rezumat, elemente_atinse}`: `schimbari[]` (`{element_id, ce, scor_inainte, scor_dupa, de_ce}`), `pasi[]` (pașii StepTrace: extracție, geocodare, trace, potrivire, predicție, scor, cu `rezultat` și `motive`) și `eronat_prototip`. Sunt aceleași obiecte ca în StepTrace, copiate în jurnal la fiecare `apply_event`.

## Cum se verifică
```bash
EXTRACT_CLI=0 .venv/bin/python -m backend.engine.smoke_sesiune2   # blocul „timeline derulabil" (65 de verificări)
EXTRACT_CLI=0 .venv/bin/python -c "from backend.engine.engine import model_scenariu; t=model_scenariu('extrem').timeline(); print(len(t), t[0].keys())"
```
Scenariul extrem: 70 de intrări, ~116 KB JSON.

## Ce rămâne (C)
UI-ul: panoul, sincronizarea cu harta (`GET /retea?data=&scenariu=extrem`, cache pe dată, debounce), evidențierea elementelor atinse, „De ce?" din `pasi`, eliminarea butonului Play și a barei de dată. Sarcinile 2.1, 3.1-3.3, 4.1 din `tasks.md`; un singur prompt Lovable grupat, netrimis până decide omul.

## Decizii și limite
- Mai multe evenimente în aceeași zi au aceeași hartă (`snapshot(data)` e la sfârșitul zilei); diferența se vede prin evidențierea elementelor atinse.
- Dimensiunea (116 KB) e acceptabilă la o singură încărcare; dacă devine problemă, `pasi` se poate cere separat per eveniment.
- Ce trebuie să știe ceilalți: C trece câmpurile noi neatinse prin API și construiește lista din ele; A nu are nimic de făcut.
