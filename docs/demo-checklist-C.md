# Checklist demo, partea C (API + UI), după `docs/DEMO.md`

## Înainte
1. `backend/api/demo_start.sh` pornește uvicorn (:8000) și tunelul și afișează linkul. Dacă rulează deja, doar îl afișează.
2. `backend/api/demo_start.sh --reset-model`: model curat, fără rapoartele live ale repetițiilor (tunelul și URL-ul rămân). Fă-l chiar înainte de demo.
3. Deschide linkul `https://id-preview--fd19026a-1ce3-4de6-8f4d-355c351e028a.lovable.app/?api=<URL tunel>`.
4. Verifică colțul `mod`: `retea=motor, evenimente=motor, motor=real`. `extractie=stub` e normal fără `.env` cu cheie.
5. Marcajul „date fictive" se vede; harta arată 530 de elemente.

## În timpul demo-ului (timpii din DEMO.md)
- 0-29 s: harta pe date 4 aug., apoi Play. Se văd: punct violet punctat (predicție), elemente care se înverzesc, un element roșu (conflict, 29 aug.), aplicare 10 sept., închidere la portocaliu în octombrie.
- 29-45 s: pauză, ecranul **Proces raport**; se lipește textul: `Confirm în teren nodul 6925190 din curba străzii, la coordonatele 44.2830311, 26.063942, între nodurile 6513200 și 7824201.` (sursa: mentenanță, data 2026-10-28). Pașii vizibili: text, structură, potrivire, propunere, scor.
- 45-60 s: „Vezi pe hartă": punctul violet devine solid. Rezultat așteptat: `adaugat`, scor 0,95, nodul și 2 legături în model.

## Plan B
- Dacă tunelul sau Lovable pică: `http://localhost:8000/ui/` (UI Leaflet servit de FastAPI, același scenariu).
- Tunelul își schimbă URL-ul la fiecare repornire: refă linkul cu `demo_start.sh` (afișează unul nou) și deschide-l din nou. URL-ul curent e și în `/tmp/claude-1000/tunnel.url`.
- Hărți de bază: plăcile OSM cer internet; fără ele fundalul e gri, liniile rămân.
- Ultima soluție: înregistrare video.

## Ce NU promitem
- Geocodarea adreselor nu e implementată: rapoartele fără coordonate nu se potrivesc pe hartă (apar ca „de verificat").
- Extracția cu Claude cere `.env` cu cheia; fără ea se folosește rezerva stub regex, vizibilă în pas (`metoda` = „stub_regex (rezervă: ...)"), iar tipul poate diferi (ex. „avarie"), dar nodul tot e tratat ca lipsă.
- Proiectul Lovable e nepublicat; se folosește preview-ul.
