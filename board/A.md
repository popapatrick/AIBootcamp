# Panou laptop A

Scrie doar aici. Intrări noi deasupra. Format: ora, gata, în lucru, blocat / am nevoie de la X, contract atins.

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
