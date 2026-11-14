# Design

## Context

Pipeline-ul există: `POST /rapoarte` -> `extract_event` (A) -> `match_event` și `apply_event` (B) -> StepTrace. Sursele au ponderi în `weights.yaml` (tableta 0,90, formular 0,75, text_liber 0,55, apel_client 0,25). Traseul pe străzi există în `backend/engine/osm.py` (etapa 6) și se aplică deja la `nod_lipsa` fără ID.

## Goals / Non-Goals

**Goals:**
- Un om poate scrie sau genera un raport din oricare dintre cele 4 surse și vede imediat efectul.
- „Show pipeline" explică fiecare pas și fiecare schimbare, cu scoruri.

**Non-Goals:**
- Nu geocodăm adrese (rămâne în afara scopului).
- Nu construim autentificare sau roluri de utilizator.

## Decisions

- Apelul clientului este doar o sursă cu pondere mică (`apel_client`), tratată de același calcul de scor ca restul, conform principiilor produsului.
- Exemplele dummy vin din fișier (`data/reports/exemple-dummy.json`, A), mai multe pe sursă, nu din apel LLM, ca să meargă fără internet.
- Schimbările din rețea se întorc structurat: `{element_id, ce (adaugat|actualizat|predictie|neaplicat|conflict), scor_inainte, scor_dupa, de_ce}`; UI-ul le afișează în pipeline și le colorează pe hartă.
- Data ultimei actualizări = data ultimului eveniment aplicat sau actualizat (nu data de sistem).

## Risks / Trade-offs

- Extracția cu stub regex (laptopuri fără cheie) dă rezultate mai slabe decât cu Claude; demo-ul folosește cache pentru textele cunoscute.
- Apelurile cu coordonate sau fără ele pot rămâne nepotrivite; pipeline-ul trebuie să arate asta deschis, nu să ascundă cazul.
