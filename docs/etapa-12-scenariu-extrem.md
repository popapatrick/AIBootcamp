# Etapa 12: scenariul extrem (A6)

DATE FICTIVE. Proprietar: A (Patrick). Spec: `openspec/changes/timeline-cazuri-extreme/`.

## Ce face
`data/events/events.extreme.json` = cele 29 evenimente din `events.json` (neatinse) + 10 evenimente noi `EV-X01..EV-X10` (39 în total), cu 10 rapoarte text noi în `data/reports/` și 10 intrări în `data/reports/index.json` (`scenariu: null`, ca în README-ul folderului).

| Caz | Evenimente | Date | Elemente reale folosite |
|---|---|---|---|
| Ramură pe etape | X01 `linie_planificata` (investitii), X02 `racord_nou` (racordari), X03 `nod_lipsa` (mentenanta, tabletă), X06 `verificare` (mentenanta) | 07.09, 30.09, 14.10, 05.11 | ancore noduri `7261864` și `7363515`; nod nou `7900101` (ID fictiv, inexistent în model) |
| Segment demontat | X04 `activ_demontat` (investitii, formular), X05 `activ_demontat` (mentenanta, text liber) | 19.10, 04.11 | tronson `A-T-012` (6166490-6240749) |
| Val de apeluri | X07..X10 `avarie_semnalata` (apel_client), 4 apeluri în 4 zile | 09-12.11 | coordonate în jur de 44.2765, 26.0633 (lângă `A-T-004`/`A-T-005`), 4 clienți diferiți |

Câmpurile `tip_sursa_pondere`, `forma_sursa`, `incredere_extractie`, `campuri_lipsa` sunt completate ca la evenimentele existente; ce nu apare în text e în `campuri_lipsa` (ex. `lungime_m`, `element_id`, `coordonate`). Evenimentele X au fost scrise de mână din rapoartele noi (fără apel Claude), deci `incredere_extractie` e estimată.

## Cum se verifică
```
.venv/bin/python - <<'PY'
import json, jsonschema
v = jsonschema.Draft202012Validator(json.load(open('contracts/event.schema.json')), format_checker=jsonschema.FormatChecker())
ev = json.load(open('data/events/events.extreme.json'))
print(len(ev), sum(len(list(v.iter_errors(e))) for e in ev), 'erori')   # 39 0
PY
.venv/bin/python -m backend.engine.smoke_engine     # baza trece (25 OK)
```
Rulare pe motor (fără endpoint încă): `GridModel()` + `apply_event` pe evenimentele sortate după `(data, event_id)`, cum face `engine._incarca_evenimente`.

## Rezultat pe motorul actual (fără regulile 3.1/3.2 ale lui B)
- X01: `predictie` `PLAN-EV-X01`, scor 0,80, neaplicată (planificat).
- X02: `adaugat` `NOU-EV-X02` (racord în afara oricărui element, scor 0,75). Coordonatele sunt alese ca racordul să nu se potrivească pe un tronson existent (la 44.28483, 26.06056 s-ar fi potrivit pe `A-T-133`).
- X03: `adaugat` nod `7900101` + 2 tronsoane `NOU-7900101-*`, scor 0,933; același loc ca X02, deci ramura se "îngroașă" pe aceeași zonă.
- X06: `verificare` pe `7900101`, scor 1,0 (verde).
- X04/X05: tratate acum ca "confirmare din teren": `A-T-012` urcă 0,656 apoi 0,767. NU e comportamentul dorit (trebuie semnal de demontare, scos din uz doar peste prag): așteaptă `activ_demontat` din `model.py` (task 3.1 B).
- X07..X10: fiecare apel scade `A-T-005` (de verificat) cu ~0,034, fără agregare: 0,399 -> 0,293. Valul agregat cu plafon 0,40 (`val_apeluri`) așteaptă task 3.2 (B).

## Decizii
- Fișier separat, `events.json` și `exemple-dummy.json` neatinse (demo-ul de 60 s rămâne la fel).
- Nod nou cu ID fictiv `7900101` (cum e `6925190` la scenariul 1); raportul îl dă explicit, nu e inventat de extracție.
- Valul are 4 apeluri (peste `numar_min: 3`) în 4 zile (sub `fereastra_zile: 7`), coordonate la câțiva metri între ele.
- Demontare: 2 echipe diferite (investitii + mentenanta), pentru ca pragul de aplicare să poată fi depășit doar cu ambele.

## Limite
- Datele extreme sunt neverificate pe real; pragurile nu sunt calibrate.
- Fără regulile B, X04/X05/X07-X10 nu arată încă cazul dorit (vezi mai sus).
- Evenimentele nu au trecut prin `extract_event` (Claude), deci nu testează extracția.

## Ce trebuie să știe ceilalți
- B: ținta pentru 3.1 este `A-T-012` (X04 sub prag, X04+X05 peste prag); pentru 3.2, zona X07-X10 (aprox. 44.2765, 26.0633); `get_model()` trebuie să accepte sursa `extreme` din `events.extreme.json`.
- C: `?scenariu=extrem` servește acest fișier; datele X se întind 07.09-12.11, deci slider-ul trebuie să acopere până la 2026-11-12.
