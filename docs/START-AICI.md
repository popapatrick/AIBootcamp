# Pornire pentru laptopurile A, B, C

Toți lucrați pe același repo: `popapatrick/AIBootcamp`, branch `main`. Citiți întâi `PLAN-prototip.md` (secțiunile 10, 11, 12).

## Pași, o singură dată (fiecare laptop)
```bash
git clone https://github.com/popapatrick/AIBootcamp.git
cd AIBootcamp
echo A > .laptop        # sau B, sau C, după laptop
cp .env.example .env    # apoi pune cheia API Claude în .env (nu intră în git)
```
Apoi deschide folderul în Claude (aplicația Claude Code) și activează pluginul **Lovable** din contul claude.ai (autentificare OAuth). Îl folosește mai ales C.

## Ce îi spui lui Claude (copiază promptul laptopului tău)

**Laptop A**
> Ești laptopul A. Citește CLAUDE.md, PLAN-prototip.md și .claude/agents/patrick.md, apoi contracts/ și board/. Scrie prima intrare în board/Patrick.md și începe cu etapa 2 (date dummy), scriind întâi data/events/events.stub.json. Lucrează autonom, comite des, urmează regulile din CLAUDE.md.

**Laptop B**
> Ești laptopul B. Citește CLAUDE.md, PLAN-prototip.md și .claude/agents/victor.md, apoi contracts/ și board/. Scrie prima intrare în board/Victor.md și începe cu etapa 1 (rețeaua în graf), apoi publică data/model/sample/ pentru C. Lucrează autonom, comite des, urmează regulile din CLAUDE.md.

**Laptop C**
> Ești laptopul C. Citește CLAUDE.md, PLAN-prototip.md și .claude/agents/claudiu.md, apoi contracts/ și board/. Scrie prima intrare în board/Claudiu.md. Începe cu API-ul în mod stub (etapa 7) și cu prompturile Lovable în frontend/lovable-prompts.md; spune-mi câte prompturi trimiți în Lovable înainte să le trimiți. Lucrează autonom, comite des, urmează regulile din CLAUDE.md.

## Pe parcurs
- La fiecare ~30 min, spune-i lui Claude: „fă `git pull --rebase`, citește board/ și continuă".
- Dacă Claude zice că poate trebuie ridicat efortul sau modelul, decideți voi din selectorul aplicației.
- Punctele de sincronizare (H+0:30, 1:30, 3:30, 5:30, 7:00, 8:00) sunt în plan, secțiunea 10.7.
