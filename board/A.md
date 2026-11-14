# Panou laptop A

Scrie doar aici. Intrări noi deasupra. Format: ora, gata, în lucru, blocat / am nevoie de la X, contract atins.

## 19:01 events.json împins (A)
Gata: data/events/events.json, 28 evenimente extrase real (OpenRouter `anthropic/claude-haiku-5.5`), valide pe schemă. Față de index.json: element_id 28/28 (null pentru rapoarte doar cu coordonate și pentru T-054/T-002 fără prefix, cod brut în `detalii.id_partial`), tip 27/28. Prompt nou: `verificare` pentru inspecții fără defecte; `detalii.sectiune_noua` / `noduri_vecine` / `noduri`; forma_sursa doar campuri/text_liber. Stub EV-S05 are acum `detalii.noduri` = 6819943, 6132582.
În lucru: -
Blocat / @B: Scuze încă o dată pentru întârziere. Singura diferență de tip: 2026-08-29_racordari_02 (scenariul 5) iese `racord_nou`, nu `activ_inlocuit`. Calibrarea ta rulată la mine pe events.json: 12 scor_actualizat, 10 neaplicat, 2 predicție, 2 fără efect, 1 conflict, 1 aplicat; smoke_engine OK.
Contract atins: nu (`verificare` adăugat de B în bf8e4ae)

## 18:50 Extracție rulată pe OpenRouter (A)
Gata: events.stub.json (5 ev., valid); 28 rapoarte + index.json; backend/extract (OpenRouter `anthropic/claude-haiku-5.5`, cache, test offline OK). Extracție reală: 28/28 valide pe schemă; tip corect 21/28; element_id corect 18/28 (cele 10 diferențe = 8 rapoarte doar cu coordonate → null corect, potrivirea e la match_event; T-054/T-002 copiate fără prefix).
În lucru: verificările de rutină „fără defecte" nu au `tip` potrivit în schemă (modelul alege avarie_semnalata / nod_lipsa) → events.json NU e încă împins.
Blocat / @B: Scuze pentru întârziere! propun `tip: verificare` (inspecție fără modificări, reîmprospătează scorul; util pentru scenariul 6). Ești de acord cu schimbarea de contract?
Contract atins: nu

## 18:38 Extracție și date dummy gata (A)
Gata: events.stub.json pentru B (5 evenimente); 28 rapoarte în data/reports/ + index.json (ground truth); backend/extract (test offline OK). Documentație: docs/etapa-2-date-dummy.md, docs/etapa-3-extractie.md.
În lucru: rulare extracție reală (`python -m backend.extract.run_all`).
Blocat: lipsește ANTHROPIC_API_KEY în .env.
Contract atins: nu

## start
Gata: -
În lucru: nu am început. Aștept să citesc CLAUDE.md, planul și contractele.
Blocat: -
Contract atins: nu
