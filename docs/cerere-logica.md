# Cerere de logică (șablon)

Pentru orice schimbare care NU e doar o valoare numerică în `contracts/weights.yaml` (o regulă nouă, un comportament diferit, un câmp nou). Valorile se schimbă direct cu `reglaj:` (vezi `docs/etapa-23-reglaje.md`).

Lipește blocul în `board/<laptop-tău>.md`, adresat `@Victor`:

```
## CERERE-LOGICĂ: <titlu scurt> (<nume>, <rol>)
@Victor
Ce vreau: <comportamentul dorit, o propoziție>
Intrare exemplu: <text de raport sau JSON de eveniment, cu coordonate/adresă>
Ieșire așteptată: <decizie, nivel, scor aproximativ, ce apare în „De ce?">
De ce: <motivul, de la demo sau din banc>
Urgență: <acum | înainte de demo | oricând>
```

Ce face B:
1. În cel mult 30 de minute (agent Sonnet, model mare doar dacă e algoritm greu) implementează cererea, cu test în `smoke_*`, sau răspunde pe board de ce nu (încalcă un principiu: ponderile pentru tot sistemul, regula de intrare, nu inventăm date).
2. Rulează `scripts/verifica_tot.sh`; dacă schimbarea mută scoruri, scrie diferența în `docs/calibrare.md`.
3. Răspunde în `board/Victor.md` cu `@<cine a cerut>` și commit-ul.

Reguli: o cerere = o schimbare. Dacă ai nevoie de un câmp nou în contract, spune-o în cerere (commit `contract:`, doar B). După tag-ul `logic-v1`, cererea are nevoie de aprobarea lui Victor ca să atingă motorul.
