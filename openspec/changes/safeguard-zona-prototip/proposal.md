# Proposal

## Why

Prototipul are rețea doar într-o zonă mică (~1 km). Un punct greșit (geocodare eronată, coordonate cu zecimale lipsă, un traseu rătăcit) ar putea ajunge la zeci de km și ar strica modelul. Trebuie un safeguard: nimic nu iese dintr-o zonă de 3 km în jurul rețelei, iar un punct din afară e declarat „eronat în cadrul prototipului".

## What Changes

- Zonă de prototip: cerc de 3 km (`zona.raza_max_m`) în jurul centroidului rețelei de start.
- Orice punct care intră în sistem (coordonate din raport, rezultat de geocodare, puncte de trace, centru de mutare fire, locația unei cereri de racordare, clic pe hartă) e verificat. În afara zonei: evenimentul nu se aplică și nu intră în model, jurnalul spune „în afara zonei prototipului, eronat în cadrul prototipului" cu distanța, iar UI-ul îl poate arăta separat.
- Punctele AI sau generate nu ies niciodată din zonă: geocodarea și generatorul de trace întorc `in_afara_zonei` în loc de coordonate.
- Înlocuiește verificarea actuală cu bbox +500 m din `match.py`.

## Capabilities

### New Capabilities
- `zona-prototip`: limitarea tuturor punctelor la zona de 3 km și etichetarea celor eronate.

### Modified Capabilities

## Impact

- B: `backend/engine/zona.py` (nou), `match.py`, `model.py`, `sesiune2.py`, `weights.yaml` (`zona`), `StepTrace` (`eronat_prototip`).
- A: `backend/geo` și `backend/trace` importă `zona_ok` și întorc `in_afara_zonei`.
- C: flag `eronat_prototip` în API și mesaj în UI (după înghețarea logicii).
- Contract (`contract:`, B): `eronat_prototip` și semnalul `in_afara_zonei_prototip`.
- În afara scopului: extinderea zonei, alte limite geografice.
