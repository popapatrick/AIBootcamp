# Proposal

## Why

Timeline-ul actual are buton Play și o bară de dată: arată cum se schimbă harta, dar nu ce s-a modificat și de ce. Utilizatorul vrea o listă de evenimente derulabilă, în care fiecare modificare a rețelei se vede cu data, decizia și efectul, iar derularea mută harta pe acea dată.

## What Changes

- Panou vertical lateral cu toate evenimentele (scenariul extrem, ~70), în ordine cronologică, în locul butonului Play și al barei de dată.
- Derularea listei mută harta automat: evenimentul din mijlocul panoului devine activ, iar harta arată starea rețelei la data lui; elementele atinse de el sunt evidențiate.
- Fiecare intrare arată: data, eticheta (mutare fire, racordare, decizie om, val de apeluri...), decizia (adăugat, aplicat, predicție, neaplicat, eronat în prototip) și scorul înainte -> după al elementelor atinse.
- Clic pe o intrare deschide „De ce?": pașii pipeline-ului (extracție, geocodare, trace, potrivire, predicție, scor) cu motivele.
- Motorul dă deja tot ce trebuie: `timeline()` / `GET /evenimente` întoarce acum și `schimbari[]`, `pasi[]`, `eronat_prototip` pe fiecare intrare (aditiv).

## Capabilities

### New Capabilities
- `timeline-derulabil`: lista derulabilă de modificări, sincronizată cu harta.

### Modified Capabilities

## Impact

- B: `timeline()` extins (făcut), `contracts/interfaces.md` (commit `contract:`), test în `smoke_sesiune2.py`.
- C: interfața (Lovable, un prompt grupat, netrimis până decide omul) și plan-B (Leaflet) ca rezervă; teste API pentru `GET /evenimente?scenariu=extrem`.
- A: nimic.
- În afara scopului: editarea evenimentelor din timeline; redare automată (Play) — se poate păstra ca opțiune, dar nu mai e interacțiunea principală; filtre pe etichetă (extindere).
