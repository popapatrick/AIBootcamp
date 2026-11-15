"""Ștergere de către om (sesiunea 4, etapa 34): eveniment `stergere_om`.

Mixin pentru `GridModel`. Date FICTIVE. Vezi `docs/etapa-34-stergere-om.md`.

Ce se poate șterge: tot ce a adăugat sistemul după start. Predicțiile punctate (`self.predictii`: NOU-/MUT-/PLAN-/TRK-,
lanțuri de racordare), elementele aplicate din rapoarte/tracking (`origine: generat_model`, fără `t0`) și pinurile `VER-*`.
NU se șterg: elementele rețelei de start (`t0: true`: KMZ/GIS și SIM-*) și cele deja retrase/șterse.

Efect = retras cu jurnal: elementul dispare din `snapshot` de la data ștergerii, rămâne în istoric (date anterioare),
motivul „Șters de om: <motiv>” e primul în „De ce?”. Fără penalizare pentru metodă (diferit de „Respinge”).
Grup: un stâlp + legăturile lui ștergibile; o legătură + stâlpii ei ștergibili rămași fără alte legături (niciun fir în aer).
Decizia din StepTrace: `sters`; eticheta din timeline: `stergere`.
"""
from __future__ import annotations


class Stergere:
    """Metodele ștergerii, amestecate în `GridModel` (folosesc `self.net`, `self.predictii`, `self.pinuri`, `self.retrase`, `self.istoric`)."""

    # ------------------------------------------------------------------ ce se poate șterge
    def _stergibil(self, eid: str) -> bool:
        """True dacă elementul poate fi șters acum: adăugat de sistem (nu `t0`, nu `retea_start`), încă activ
        (predicție, pin sau element aplicat în `net`), neretras."""
        cur = (self.istoric.get(eid) or [None])[-1]
        if cur is None or cur.get("retras") or cur.get("t0") or cur.get("origine") == "retea_start":
            return False
        return (eid in self.predictii or eid in self.pinuri
                or eid in self.net["noduri"] or eid in self.net["tronsoane"])

    def _capete_legatura(self, eid: str):
        """Capetele unei legături (aplicată sau prezisă); None dacă `eid` nu e legătură."""
        t = self.net["tronsoane"].get(eid)
        if t is not None:
            return tuple(t["capete"])
        p = self.predictii.get(eid)
        return tuple(p["capete"]) if p and "capete" in p else None

    def _legaturi_nod(self, nid: str) -> list[str]:
        """Toate legăturile active (aplicate sau prezise) care au `nid` între capete."""
        out = [t for t, v in self.net["tronsoane"].items() if nid in v["capete"]]
        out += [t for t, v in self.predictii.items() if "capete" in v and nid in v["capete"]]
        return sorted(out)

    def _este_nod(self, eid: str) -> bool:
        return (eid in self.net["noduri"] or eid in self.pinuri
                or (eid in self.predictii and "punct" in self.predictii[eid]))

    def _grup_stergere(self, tinta: str) -> list[str]:
        """Grupul șters odată cu `tinta` (ștergibil). Stâlp: el + legăturile lui ștergibile. Legătură: ea + capetele ștergibile
        rămase fără alte legături. Stâlpii rămași izolați după ștergerea legăturilor se șterg și ei. Noduri întâi, apoi legături."""
        sters = {tinta}
        if self._este_nod(tinta):
            sters |= {l for l in self._legaturi_nod(tinta) if self._stergibil(l)}
        cap_leg = [l for l in sters if self._capete_legatura(l)]
        for l in cap_leg:
            for c in self._capete_legatura(l):
                if c in sters or not self._stergibil(c) or not self._este_nod(c) or c in self.pinuri:
                    continue
                if all(x in sters for x in self._legaturi_nod(c)):
                    sters.add(c)
        return sorted(sters, key=lambda x: (self._capete_legatura(x) is not None, x))

    # ------------------------------------------------------------------ evenimentul
    def _stergere_om(self, event: dict, trace: dict):
        """Aplică `stergere_om` (`detalii.tinta_id`, `detalii.motiv` opțional). Refuzuri (`neaplicat` + `trace["eroare"]`):
        `necunoscut`, `deja_sters`, `nu_se_sterge_retea_start`. Altfel decizia `sters`, `schimbari[].ce = "sters"`."""
        data, det = event["data"], event.get("detalii") or {}
        tinta = (det.get("tinta_id") or "").strip()
        motiv = (det.get("motiv") or "").strip()
        trace["pasi"].append({"nume": "potrivire", "incredere": 1.0,
                              "rezultat": {"status": "potrivit", "element_id": tinta, "metoda": "tinta_id", "calitate": 1.0,
                                           "candidati": [], "semnale": [], "motiv": "Elementul ales de om."}})
        trace["pasi"].append({"nume": "predictie", "rezultat": None, "incredere": None})

        def refuz(cod: str, mesaj: str):
            trace["eroare"] = {"cod": cod, "mesaj": mesaj}
            self._scor_pas(trace, "neaplicat", {"nivel": None}, [mesaj])
            trace["_rezumat"] = f"Ștergere neaplicată: {mesaj}"

        cur = (self.istoric.get(tinta) or [None])[-1]
        if not tinta or cur is None:
            return refuz("necunoscut", f"Nu există niciun element cu ID-ul {tinta or '(gol)'}: ștergere neaplicată.")
        if cur.get("retras"):
            cum = "șters de om" if cur.get("sters") else "retras (respins sau înlocuit)"
            return refuz("deja_sters", f"{tinta} e deja {cum}: nu mai e pe hartă.")
        if not self._stergibil(tinta):
            return refuz("nu_se_sterge_retea_start",
                         f"{tinta} face parte din rețeaua de start (GIS sau simulat): nu se poate șterge, doar verifica.")
        grup = self._grup_stergere(tinta)
        txt_motiv = f"Șters de om: {motiv}" if motiv else "Șters de om (fără motiv indicat)"
        text = (f"{txt_motiv}. Retras de la {data} ({event['event_id']}); rămâne în istoric, vizibil la datele anterioare. "
                f"Fără penalizare pentru metoda care l-a propus.")
        trace["_ce"] = {}
        for sid in grup:
            c = self._curent(sid)
            geom = self._geometrie(sid)       # înainte de scoaterea din predicții / net: rămâne pentru date anterioare
            if sid in self.predictii:
                self.retrase[sid] = self.predictii.pop(sid)
            elif sid in self.pinuri:
                self.retrase[sid] = self.pinuri.pop(sid)
            else:
                el = self.net["noduri"].pop(sid, None) or self.net["tronsoane"].pop(sid)
                self.retrase[sid] = {"geometrie": geom, "el": el}     # nu mai e potrivit de rapoarte; istoricul păstrează forma
            self._pune(sid, c["tip_element"], data, retras=True, sters=True, sters_data=data, sters_motiv=motiv or None,
                       motive=[{"text": text, "efect": 0.0, "eveniment": event["event_id"], "data": data}] + c["motive"])
            trace["_ce"][sid] = "sters"
            trace["modificari"].append(self._publica(sid, self._curent(sid)))
        ids = ", ".join(grup[:8]) + (f" și încă {len(grup) - 8}" if len(grup) > 8 else "")
        rezumat = f"Șters de om: {len(grup)} {'element' if len(grup) == 1 else 'elemente'} ({ids})"
        self._scor_pas(trace, "sters", {"nivel": None, "tinta": tinta, "grup": grup, "sters": len(grup)}, [text])
        trace["stergere"] = {"tinta_id": tinta, "elemente": grup, "n": len(grup), "motiv": motiv or None}
        trace["_rezumat"] = rezumat
