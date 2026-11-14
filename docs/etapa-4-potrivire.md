# Etapa 4: potrivirea evenimentelor pe rețea (B)

Date FICTIVE.

## Ce face
`backend/engine/match.py`, funcția `match_event(event, net, weights=None)`, găsește elementul din model la care se referă un eveniment. Ordinea: ID, apoi coordonate, apoi adresă. Niciun eveniment nu rămâne fără rezultat.

## Cum se rulează și se verifică
```bash
python3 -m venv .venv && .venv/bin/pip install -r backend/engine/requirements.txt   # o singură dată (pyyaml)
.venv/bin/python -m backend.engine.smoke_match    # așteptat: OK: 13 cazuri
```

## Intrări și ieșiri
- Intrare: un Event (`contracts/event.schema.json`) și modelul curent `net` (din `load_network()` / `defects.build()["model"]`). Pragurile vin din `contracts/weights.yaml`, secțiunea `potrivire`.
- Ieșire: `{status, element_id, metoda, calitate, candidati, coordonate_folosite, semnale, motiv}`. Descrisă în `contracts/interfaces.md`.

| status | când |
|---|---|
| `potrivit` | ID găsit în model, sau element la ≤ 15 m de coordonate |
| `ambiguu` | cod de tronson fără prefix care se potrivește cu mai multe categorii |
| `absent_din_model` | ID valid dar inexistent în model, sau nimic în raza de 15 m. Nu e eroare: așa se descoperă ce lipsește |
| `nepotrivit` | doar adresă, coordonate în afara zonei sau nicio referință |

## Semnale (le folosește etapa 5 la scor)
`coordonate_corectate` (lat/lon inversate, corectate automat, calitate ×0,8), `coordonate_in_afara_zonei` (de ex. zecimale lipsă), `cod_fara_prefix`, `inconsecventa_id_coordonate` (ID găsit, dar coordonatele sunt la > 45 m de el: calitate ×0,6, semnal contradictoriu), `doar_adresa`.

## Decizii
- Calitatea vine din `weights.yaml`: 1,0 după ID, 0,7 după coordonate, scăzând liniar până la 0,35 spre marginea razei.
- Corectăm inversarea lat/lon doar dacă varianta inversată cade în zona rețelei (± 500 m), altfel marcăm „în afara zonei".
- Un cod `T-xxx` fără prefix cu un singur tronson posibil se potrivește cu calitate 0,6, pentru că nu putem ști că nu e elementul lipsit din model.
- Distanța la un tronson e distanța la linie, nu la capete.

## Limite cunoscute
- **Geocodarea adresei nu e implementată:** un raport doar cu adresă sau nr. cadastral rămâne `nepotrivit`. E scenariul 7, tăiat primul în caz de lipsă de timp.
- O coordonată fără ID nu poate distinge „nod lipsă" de „nod vecin aflat aproape": decizia o ia etapa 5 folosind și `tip` (nod_lipsa, racord_nou). Nodurile sunt dese (mediana distanței la cel mai apropiat nod e 8,7 m, raza e de 15 m), deci o coordonată poate pica între mai multe elemente; `candidati` le păstrează.
- Testat pe evenimente sintetice, nu pe rapoartele lui A (nu erau pe `main`).

## Ce trebuie să știe ceilalți
- A: ID-urile din rapoarte trebuie să fie cele din `network.geojson`; defectele s-au schimbat (vezi `data/model/defects.json` și `board/Victor.md`).
- C: pasul „potrivire" din StepTrace e rezultatul de mai sus.
