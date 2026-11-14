# Design

## Decisions

- Un singur loc pentru numere: `weights.yaml`. Orice constantă nouă introdusă în cod în acest val se mută în el (verificare în review).
- Limite: `weights.limits.yaml` are `cheie: [min, max]`. `verifica_reglaje` compară setul de chei cu `weights.yaml` (aceleași chei, aceleași tipuri).
- Referința de calibrare: `data/golden/calibrare-referinta.json` = rezultatul calibrării la înghețare. Diferența se arată ca tabel (eveniment, decizie înainte/după, scor înainte/după); nu blochează, doar informează; blochează doar ruperea smoke-urilor sau a limitelor.
- Cerere de logică (format): ce vrei să se întâmple, exemplu de intrare, ieșirea așteptată, de ce. Victor (sau un sub-agent Sonnet) o face în ≤ 30 min sau răspunde de ce nu.
- Excepția de scriere: commit-urile `reglaj:` pot atinge DOAR `contracts/weights.yaml` (valori). Folderele rolurilor rămân cum erau.
- `GET /reguli` expune valorile curente, read-only, pentru bancul de test și pentru o eventuală pagină de reglaj în UI; nu există scriere prin API.
- Prompturile AI rămân ale lui A; schimbarea unui prompt invalidează cache-ul AI (cheia include promptul) și cere re-umplere.

## Risks / Trade-offs

- Reglajul fără înțelegerea efectelor poate strica calibrarea; de aceea tabelul de diferențe e obligatoriu în `board/`.
