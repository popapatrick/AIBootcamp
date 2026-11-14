# frontend/ (C)

Date FICTIVE.

- `plan-b/index.html`: UI complet în HTML + Leaflet, servit de FastAPI la `http://localhost:8000/ui/`. Hartă colorată după scor, predicții punctate, timeline cu play, panou „De ce?", ecranul procesului și formular de raport nou. E planul B din plan (secțiunea 7) și referința pentru Lovable.
- `lovable-prompts.md`: cele 4 prompturi pentru Lovable.

## Stare Lovable
- Editor: https://lovable.dev/projects/fd19026a-1ce3-4de6-8f4d-355c351e028a
- Preview: https://id-preview--fd19026a-1ce3-4de6-8f4d-355c351e028a.lovable.app
- **NEpublicat** (publicare doar cu confirmarea omului).
- Trimis 2026-11-14: toate 4 prompturile (credite: 1,4 + 0,9 + 1,9 + 2,8 ≈ 7,0). Adăugirile față de text sunt notate în `lovable-prompts.md`.
- Lovable a construit tot, dar **nu a fost testat cu API-ul real**.
- Rămâne: (1) tunel HTTPS (preview-ul e HTTPS, `http://localhost` e blocat ca mixed content; pe laptop nu există cloudflared/ngrok, are nevoie de om); (2) setat `API_BASE` în „Setări” în aplicație; (3) test cap-coadă (hartă, timeline, „De ce?”, proces raport); (4) eventuale corecturi; (5) publicare doar cu confirmarea omului. Plan B: `plan-b/` la `/ui/`.

## Tunel (pentru Lovable)
Nu e instalat încă. Varianta propusă, fără cont:
```bash
cloudflared tunnel --url http://localhost:8000    # dă un https://xxxx.trycloudflare.com
```
