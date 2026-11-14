# Design

## Context

Există `backend/trace` (opriri, `localizeaza`) și traseele dummy gata făcute. Lipsește generarea automată la crearea raportului și efectul parametrilor asupra acurateței.

## Decisions

- `genereaza_traseu(punct, strazi, params, seed)` (în `backend/trace/genereaza.py`, A) întoarce puncte cu timp: mers pe stradă către punct, oprire de `durata_oprire_min`, plecare. Zgomotul e gaussian de `zgomot_m`; `acoperire` elimină puncte la întâmplare. Determinist pe `event_id`.
- Locul opririi: la punctul din raport (consistent) sau decalat cu `decalaj_m` (inconsistent, pentru test). Generatorul NU folosește rezultatul geocodării ca adevăr: oprirea e generată în jurul punctului primit, iar `localizeaza` o redescoperă, deci testul e onest.
- Efectul în scor (B): `factor_trace = clamp(1 + bonus − penalizare)` cu `bonus` crescând cu durata opririi peste `durata_min_min` și scăzând cu zgomotul, plafonat la `bonus_max`; `penalizare` pentru acoperire sub `acoperire_min` și pentru distanța oprire–adresă peste `toleranta_adresa_m`. Toate valorile în `weights.yaml`.
- Contradicție între oprire și adresa geocodată (> `toleranta_adresa_m`): acuratețea scade și jurnalul spune de ce; omul decide.
- Traseul generat e marcat `trace_sursa: simulat` și afișat ca atare. Fluxul cu trace real rămâne neschimbat.

## Risks / Trade-offs

- Un traseu generat lângă punctul din raport poate părea circular; de aceea e etichetat simulat și testat și cu decalaj, zgomot mare și acoperire mică.
