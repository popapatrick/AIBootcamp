# CLAUDE.md: reguli pentru toți agenții

Proiect: prototip „A grid model that keeps itself up to date" (hackathon PPC, Challenge 2). Planul complet e în `PLAN-prototip.md`. Răspunde în română. Datele sunt FICTIVE (rețea demonstrativă); nu se pun date reale PPC în repo.

## Rolul tău
Roluri: A = Patrick, B = Victor, C = Claudiu (agenți `.claude/agents/patrick.md`, `victor.md`, `claudiu.md`; panouri `board/Patrick.md`, `board/Victor.md`, `board/Claudiu.md`). Citește fișierul local `.laptop` (conține A, B sau C). Dacă lipsește, întreabă omul și creează-l. Apoi urmează agentul tău: `.claude/agents/patrick.md`, `victor.md` sau `claudiu.md`.

## La începutul fiecărui bloc de lucru
1. `git pull --rebase origin main`
2. Citește `board/*.md` (în special întrebările către tine, marcate `@A`/`@B`/`@C` sau `@Patrick`/`@Victor`/`@Claudiu`) și `git log --oneline -20 -- contracts/`.
3. Alege următoarea etapă din `PLAN-prototip.md` care e a ta.

## Reguli git
- Scrii DOAR în folderele rolului tău (tabel în `PLAN-prototip.md`, 10.1). Dacă ai nevoie de ceva în alt folder, scrie în `board/<laptop-tău>.md` cu `@X`.
- Commit-uri mici, minimum la ~20–30 min, cu prefix: `[A]`, `[B]`, `[C]` sau `contract:`.
- Push direct pe `main`. Înainte: rulează smoke test-ul sau pornește serverul. Nu împinge cod care strică `main`.
- Dacă push e respins: `git pull --rebase origin main`, rezolvă, push. Niciodată `--force`.
- Schimbare de contract = doar commit `contract:`, anunțat în `board/`, cu `contracts/interfaces.md` actualizat în același commit.
- Secrete: cheia API doar în `.env` local. Nu o scrie în fișiere, commit-uri sau chat-ul din repo.

## Documentație (obligatorie)
O etapă nu e terminată fără `docs/etapa-N-<nume>.md` (ce face, cum se rulează/verifică, intrări/ieșiri, decizii, limite, ce trebuie să știe ceilalți), plus README în folderele tale și docstring la funcțiile publice. Vezi secțiunea 12 din plan.

## Panou
Scrie în `board/<laptop-tău>.md`, noi intrări deasupra: ora, gata, în lucru, blocat / am nevoie de la X, contract atins. Citește panourile celorlalți.

## Efort și model
Dacă un bug nu se rezolvă după 2 încercări sau o eroare se repetă, spune explicit omului și în `board/` că „poate trebuie ridicat efortul sau modelul", cu motivul. Nu insista la nesfârșit.

## Principii de produs (nu le încălca)
- Ponderile se aplică întregului sistem: toate inputurile și toate predicțiile trec prin același calcul de scor și același `contracts/weights.yaml`. Apelul clientului e doar un alt input.
- Regula de intrare: nimic existent → se adaugă; există ceva și e sigur → se aplică; există ceva și e nesigur → predicție vizibil diferită, neaplicată, cu scor. Fiecare modificare are jurnal și „de ce".
- Nu inventa date lipsă: marchează „lipsă" sau „de verificat".

## OpenSpec (features noi)
Features noi se planifică cu OpenSpec: `openspec/changes/<feature>/` (propunere, spec, sarcini pe roluri), creat cu `/openspec-propose "idee"`; implementare cu `/openspec-apply-change`; la final `/openspec-archive-change`. Citește `openspec/changes/` și `openspec/specs/` la începutul blocului de lucru. Instalare: `brew install node`, `npm install -g @fission-ai/openspec@latest`, apoi `git pull`. Cine deține feature-ul scrie în `openspec/changes/<feature>/`; `openspec/specs/` se schimbă doar prin arhivare.
