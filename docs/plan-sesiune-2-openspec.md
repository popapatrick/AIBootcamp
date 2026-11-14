# Sesiunea 2: features noi cu OpenSpec

Date FICTIVE. Plan scris de B (Victor). Detaliile fiecărui feature sunt în `openspec/changes/<nume>/` (proposal, design, specs, tasks).

## Cum lucrăm cu OpenSpec
1. Instalare, o singură dată: `brew install node`, apoi `npm install -g @fission-ai/openspec@latest`, apoi `git pull --rebase origin main`.
2. Citiți `openspec/changes/<feature>/tasks.md`: sarcinile sunt grupate pe rol (A, B, C). Faceți doar secțiunile voastre, în folderele voastre.
3. Implementare: în Claude spuneți „/openspec-apply-change <feature>" (sau „continuă sarcinile mele din <feature>"). Bifați `- [x]` în `tasks.md` doar când e gata și verificat. Fișierul `tasks.md` îl bifează fiecare, deci `git pull --rebase` înainte de push.
4. Dacă o specificație pare greșită sau lipsește ceva: nu o rescrieți singuri; scrieți în `board/<laptop>.md` cu `@Victor` (sau `/openspec-update-change`, apoi anunțați).
5. La final, un feature se arhivează (`/openspec-archive-change`) doar după ce toate sarcinile sunt bifate și rulează testele.
6. `openspec list` arată schimbările active, `openspec validate --all` verifică formatul.

## Cele 7 features (decise cu Victor)
| Feature | Ce | Ordine |
|---|---|---|
| `harta-aspect-kmz` | Harta ca în KMZ (case verzi, noduri importante, cabluri pe categorie) + halou de stare | 1 |
| `interfata-rapoarte-pipeline` | 4 butoane de sursă, text messy, generare exemple, Show pipeline, data ultimei actualizări | 2 |
| `mutare-fire-sens-giratoriu` | Mesaj „fire mutate": zonă „de verificat" + traseu propus pe străzi | 3 |
| `verificare-om-predictii` | Butoane Acceptă (verificat în teren) / Respinge pe predicții, sursă `om_teren` (0,95), marcaj confirmat de om | 3 |
| `cerere-racordare-predictie` | Buton Cerere racordare casă: actualizare directă sau lanț prezis de stâlpi pe străzi | 4 |
| `locatie-din-trace-tableta` | Trace GPS din ultima oră + adresă: opririle dau locul exact al stâlpului (fallback), cu trasee simulate | 5 |
| `timeline-cazuri-extreme` | Scenariu cu ramură pe etape, sens giratoriu, segment demontat, val de apeluri | 6 (depinde de 1, 3 și 4) |

## Cine face ce
- **B (Victor):** commit-ul de contract (primul pas, mai jos), motorul pentru toate cele 4, aliniere plan-B.
- **A (Patrick):** exemple dummy pe sursă, texte pentru sens giratoriu, `events.extreme.json` și rapoartele lui, prompt pentru `mutare_fire`.
- **C (Claudiu):** API (`schimbari`, exemple, centru din clic, scenariu) și UI în Lovable (contul lui Claudiu): simboluri, halou, 4 butoane, Show pipeline, buton fire mutate, buton „Încarcă rețeaua cu evenimente". Lovable rămâne NEpublicat până decide omul.

## Pasul 0 (înainte de orice): contractul
B face un singur commit `contract:` cu: `clasa` pe noduri/tronsoane, `schimbari[]` și `ultima_actualizare`, tipurile `mutare_fire`, `activ_demontat` și `cerere_racordare`, sursa `om_teren` și `detalii.decizie`, `detalii.trace`, endpointul de decizie, pragurile noi din `weights.yaml` (mutare, apeluri, racordare, trace). Până nu apare în `git log -- contracts/`, A și C doar pregătesc (texte, prompturi), nu scriu cod care depinde de câmpurile noi.

## Ordinea lucrului
1. B: contract. Între timp A scrie exemplele dummy și textele, C scrie prompturile Lovable (fără să le trimită până se vede contractul).
2. B: `clasa` + `schimbari` + `ultima_actualizare`. C: UI hartă și 4 butoane. A: `exemple-dummy.json`.
3. B: `mutare_fire`. A: prompt `mutare_fire`. C: buton fire mutate.
4. B: `activ_demontat`, val de apeluri, recalibrare. A: `events.extreme.json`. C: buton încărcare scenariu.
5. B: verificare om, cerere racordare, trace. A: `trasee-dummy.json` (inclusiv traseul cu stâlpi verificați și oprire unde nu era stâlp), texte de cerere racordare. C: butoane Acceptă/Respinge, cerere racordare, generare și editare traseu.
6. Repetiție de demo, `docs/DEMO.md` actualizat.

## Reguli neschimbate
Ponderile se aplică întregului sistem (apelul e doar alt input), regula de intrare (nou -> adaugă, sigur -> aplică, nesigur -> predicție neaplicată cu scor), nu inventăm date lipsă, documentația pe etapă obligatorie, commit-uri mici cu prefix `[A]`/`[B]`/`[C]`/`contract:`, fără `--force`.

## De confirmat
- „Casă" = serie 7 (verde) e o presupunere din simbolurile KMZ.
- Traseul GPS e simulat; adresa dă doar strada (numărul nu se geocodează). Pragurile trace-ului sunt necalibrate pe date reale.
- Plan-B (Leaflet) rămâne rezervă; nu îl dezvoltăm în plus decât pentru `clasa` și halou.
