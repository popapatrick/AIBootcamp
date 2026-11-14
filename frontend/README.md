# frontend/ (C)

Date FICTIVE.

- `plan-b/index.html`: UI complet în HTML + Leaflet, servit de FastAPI la `http://localhost:8000/ui/`. Hartă colorată după scor, predicții punctate, timeline cu play, panou „De ce?", ecranul procesului și formular de raport nou. E planul B din plan (secțiunea 7) și referința pentru Lovable.
- `lovable-prompts.md`: cele 4 prompturi pentru Lovable.

## Stare Lovable
- Proiect: **necreat încă**. Pluginul Lovable nu e conectat în sesiunea Claude de pe laptopul C; aștept omul (OAuth) și confirmarea pentru cele 4 prompturi.
- Trimis: nimic. Rămâne: prompturile 1–4, setarea API_BASE pe URL-ul tunelului.

## Tunel (pentru Lovable)
Nu e instalat încă. Varianta propusă, fără cont:
```bash
cloudflared tunnel --url http://localhost:8000    # dă un https://xxxx.trycloudflare.com
```
