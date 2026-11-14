# Proposal

## Why

Rețeaua se schimbă și fără ca cineva să mute explicit elementul: o intersecție devine sens giratoriu, iar firele nu se mai găsesc acolo. Sistemul trebuie să primească un astfel de mesaj, să nu mai creadă că elementele din zonă sunt corecte și să propună unde ar putea fi acum.

## What Changes

- Buton în UI pentru mesajul „firele au fost mutate": text liber plus locația (coordonate din text sau clic pe hartă).
- Tip nou de eveniment `mutare_fire` cu centrul zonei, raza și motivul (de exemplu sens giratoriu).
- Motorul marchează elementele din rază „de verificat" (galben, scor scăzut) cu jurnal și „de ce".
- Sistemul propune punctat un traseu nou pe străzile din jur (OSM), cu scor, neaplicat până la confirmare.

## Capabilities

### New Capabilities
- `mutare-fire-zona`: mesajul de mutare a firelor într-o zonă și efectul lui în model.

### Modified Capabilities

## Impact

- `contracts/event.schema.json`: tip `mutare_fire` și `detalii` (centru, rază, motiv); commit `contract:`.
- `backend/extract` (A): prompt și exemplu pentru acest tip.
- `backend/engine` (B): regula de zonă și propunerea de traseu pe străzi (refolosește `osm.py`).
- Frontend Lovable (C): butonul și selectarea locației.
