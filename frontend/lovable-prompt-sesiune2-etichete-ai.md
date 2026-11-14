# Prompt Lovable sesiunea 2: etichete AI / Regex / Predicție AI (cerere Victor, contract 93d21f4)

- **Dependențe:** API cu `pasi[extractie].metoda_cod` și `/health.extractie_cod` (commit 05d0d49, pe main).
- **Cost estimat:** ~1-2 credite.
- **Verificare după:** un exemplu din „Generează exemplu" arată „AI (cache)"; un text scris de mână arată „Regex (simplificat)"; colțul de stare arată modul global; o predicție arată „Predicție AI · <metodă> · <scor>".

---

## PROMPT (de lipit în Lovable)

Schimbare mică, doar afișare (frontend, română, date FICTIVE). Nu schimba nimic altceva.

1. **Pasul Extracție din „Show pipeline"**: lângă numele pasului, un semn colorat după `metoda_cod` din pasul `extractie`:
   - `ai_cache` -> „AI (cache)" (albastru);
   - `ai_api` -> „AI (API)" (violet);
   - `regex` -> „Regex (simplificat)" (gri-portocaliu), cu tooltip „Regex = extracție simplă, fără AI, pentru text nou fără cache". Dacă pasul are `motiv`, arată-l ca text mic sub semn.
   - lipsă -> „—".
2. **Colțul de stare** (unde e `mod` din `/health`): semn global din `/health.extractie_cod`, cu aceleași texte și culori: „Extracție: AI (cache)" / „AI (API)" / „Regex (simplificat)"; lipsă -> „Extracție: —".
3. **Etichete pe elemente** (tooltip pe hartă și panoul „De ce?"):
   - `nivel` = `predictie` -> „Predicție AI · <`predictie.metoda`> · scor <scor>", cu metodele afișate lizibil: `traseu_strada_osm` = „traseu pe străzi OSM", `lant_racordare` = „lanț de racordare", `zona_mutata` = „fire mutate", `pozitie_din_trace` = „poziție din traseul GPS", `propunere_proprietate` = „propunere din raport"; metodă necunoscută -> textul brut.
   - `confirmat_de` = `om` -> „Confirmat de om" (are prioritate față de celelalte etichete).
   - restul elementelor `in_model` atinse de rapoarte -> „Din raport".
   - Tooltip onest pe „Predicție AI": „Extracția textului folosește AI; poziția prezisă vine din scor plus străzile OSM, nu e aplicată în model până la confirmare."
4. Orice câmp lipsă -> „—", fără erori în consolă.
