# Etapa 6: traseul probabil al cablului pe stradă, din OSM (B)

Rețeaua e FICTIVĂ; străzile sunt reale (OpenStreetMap).

## Ce face
`backend/engine/osm.py` construiește un graf de străzi din `data/model/osm/streets_raw.json` (descărcat o singură dată din Overpass) și calculează cel mai scurt drum pe stradă între două puncte. Motorul îl folosește când propune un element lipsit (nod lipsă): în loc de linie dreaptă către nodurile vecine, desenează legătura pe stradă, cu un scor `urmeaza_strada`.

## Cum se rulează și se verifică
```bash
.venv/bin/python -m backend.engine.smoke_osm      # așteptat: OK: 9 verificări
.venv/bin/python -m backend.engine.osm --fetch    # doar dacă vrei să refaci cache-ul (necesită internet)
```
Rutarea e locală, fără internet; la demo nu se apelează Overpass. `backend.engine.engine.get_model()` pune automat `traseu_fn` dacă cache-ul există; altfel rămân linii drepte.

## Cum se calculează `urmeaza_strada` (0–1)
Media dintre:
- apropierea capetelor de stradă: 1 la 0 m, 0 la ≥ 30 m;
- cât de scurt e ocolul pe stradă față de linia dreaptă: 1 până la 1,3×, 0 la ≥ 2,5×.

Dacă strada cea mai apropiată e la > 40 m, nu există drum sau ocolul e > 3×, întoarce `None` și legătura rămâne linie dreaptă. Pentru fiecare legătură din `StepTrace` (pasul „predicție", `rezultat.legaturi`) se vede: metoda, `urmeaza_strada`, lungimea pe stradă și cea a dreptei și `abatere_dreapta_m` (cât s-ar abate linia dreaptă de stradă). O legătură fără stradă contează neutru (0,5), nici confirmată, nici infirmată; propunerea primește media legăturilor.

## Rezultate pe scenariul 1 (nodul lipsă `6948201`)
- Legătura către `6166490`: traseu pe stradă de 45,1 m față de 40,0 m în linie dreaptă, `urmeaza_strada` 0,96; linia dreaptă s-ar fi abătut până la 4,1 m de stradă.
- Legătura către `6396507`: niciun traseu credibil (cea mai apropiată stradă la ~34 m), rămâne linie dreaptă.
- Scorul propunerii: 0,88 fără OSM, 0,85 cu OSM. **Traseul pe stradă NU a crescut scorul** față de linia dreaptă: factorul nou (0,73) e sub media celorlalți (0,93), deci mută scorul în jos. Rămâne peste pragul de aplicare (0,75), deci nodul se adaugă oricum. Plusul traseului e geometria justificată și explicația, nu un scor mai mare.
- Pe toate cele 264 de tronsoane, 206 au un traseu pe stradă între capetele lor; media `urmeaza_strada` e 0,75. Asta arată câte ar fi acoperite, nu cât de exact e traseul.

## Decizii
- Rutăm doar pe străzi pentru care e plauzibil un cablu JT: excludem trotuare, poteci, piste, `track`, `trunk` și `motorway`.
- Proiectăm capetele pe cel mai apropiat segment de stradă și adăugăm un scurt tronson până la punct.
- Cache-ul de străzi (64 KB) e în repo, ca demo-ul să meargă fără internet pe oricare laptop.

## Limite cunoscute
- **Nu putem măsura corectitudinea traseului:** KMZ-ul e fictiv și nu urmează străzile reale (tronsoanele lui sunt linii drepte între noduri; doar 47 din 161 de tronsoane aeriene au mijlocul la ≤ 15 m de un punct de stradă). Arătăm mecanismul, nu o precizie.
- Rutarea ignoră sensurile, pasajele, gardurile și proprietățile; cablurile aeriene pot trece peste curți.
- `urmeaza_strada` e o euristică explicabilă, nu o probabilitate calibrată.
- Cablurile îngropate nu se văd în imagini; nu folosim imagini satelitare în prototip.
- Cache-ul acoperă doar zona rețelei (± ~150 m).

## Atribuire
Date de străzi © contribuitorii OpenStreetMap, licența ODbL (https://www.openstreetmap.org/copyright). Se poate afișa „© OpenStreetMap" pe hartă.

## Ce trebuie să știe ceilalți
- C: harta de bază poate fi OSM (Leaflet); pasul „predicție" din `StepTrace` are acum `legaturi` cu detalii pe fiecare legătură.
- Elementele prezise au `predictie.metoda = traseu_strada_osm` și `urmeaza_strada` când există traseu.
