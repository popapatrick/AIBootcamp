"""Verificat de om (D10, sesiunea 4, V5): eveniment `verificare_om`, acceptarea ca verificare, contradicția ulterioară.

Mixin pentru `GridModel`. Date FICTIVE. Vezi `docs/etapa-29-verificat-om.md`.

Reguli:
- element existent (orice origine): scor `verificat_om.scor`, `verificat_om: true`, `verificat_om_data`, `confirmat_de: om`,
  nivel `in_model`; decizia din StepTrace e `aplicat`, eticheta din jurnal `verificat_om`;
- predicție (NOU-/MUT-/PLAN-...): se aplică în model (grupul nod + legături) și e marcată verificată;
- pin `VER-...`: devine nod real în model, verificat;
- un raport ulterior care contrazice (semnal negativ, conflict de secțiune, demontare) pune `verificat_om: false`.
"""
from __future__ import annotations

from backend.engine import scoring as S


class VerificareOm:
    """Metodele V5, amestecate în `GridModel` (folosesc `self.w`, `self.istoric`, `self.predictii`, `self.pinuri`, `self.net`)."""

    def _marcheaza_verificat(self, eid: str, event: dict, text: str) -> dict:
        """Pune pe `eid` starea „verificat de om”; întoarce starea nouă (publicabilă). Nu schimbă elementul în rest."""
        data, vs = event["data"], self.w["verificat_om"]["scor"]
        cur = self._curent(eid)
        kw = self._fara_marker(cur)
        pr_prop = (cur.get("predictie") or {}).get("propunere") or {}
        if pr_prop.get("proprietate") == "sectiune" and "predictie" not in kw:
            nivel = cur["nivel"]       # propunere de secțiune încă deschisă: nivelul rămâne (decide omul prin „Acceptă”)
        else:
            nivel = "in_model"
        eff = self._eff(cur, data)
        return self._pune(eid, cur["tip_element"], data, nivel=nivel, scor=vs, ultima_verificare=data,
                          verificat_om=True, verificat_om_data=data, confirmat_de="om", **kw,
                          motive=self._motiv(eid, text, vs - eff, event))

    def _verificare_om(self, event: dict, tinta: str, trace: dict, pas_potrivire: bool = True):
        """Aplică `verificare_om` pe `tinta` (element existent, predicție sau pin). Fără element sigur: `neaplicat`."""
        w, data = self.w, event["data"]
        det = event.get("detalii") or {}
        motiv = (det.get("motiv") or "").strip()
        vs = w["verificat_om"]["scor"]
        txt = f"Verificat de om în teren ({data})" + (f": {motiv}" if motiv else "") + f". Scor {S.fmt(vs)}."
        if pas_potrivire:
            trace["pasi"].append({"nume": "potrivire", "incredere": 1.0,
                                  "rezultat": {"status": "potrivit", "element_id": tinta, "metoda": "tinta_id", "calitate": 1.0,
                                               "candidati": [], "semnale": [], "motiv": "Elementul ales de om."}})
        trace["pasi"].append({"nume": "predictie", "rezultat": None, "incredere": None})
        el = self._elemente().get(tinta)
        cur = self.istoric.get(tinta, [None])[-1]

        def refuz(mesaj: str):
            trace["eroare"] = {"cod": "tinta_necunoscuta", "mesaj": mesaj}
            self._scor_pas(trace, "neaplicat", {"nivel": None}, [mesaj])

        if tinta in self.pinuri and tinta not in self.net["noduri"]:
            # pinul „de verificat” devine nod real în model, verificat
            pin = self.pinuri[tinta]
            lon, lat = pin["geometrie"]["coordinates"]
            sursa = (cur or {}).get("sursa_locatie")
            self.pinuri.pop(tinta)
            self.net["noduri"][tinta] = {"id": tinta, "tip_element": "nod", "serie": "Nod JT (adăugat din raport)",
                                         "plecare": None, "lat": lat, "lon": lon}
            self._pune(tinta, "nod", data, nivel="in_model", scor=vs, t0=False, predictie=None,
                       motive=[{"text": "Pin de verificat confirmat de om: " + txt, "efect": 0.0,
                                "eveniment": event["event_id"], "data": data}],
                       **({"sursa_locatie": sursa} if sursa else {}))
            c = self._marcheaza_verificat(tinta, event, "Pin de verificat confirmat de om: " + txt)
            trace["_ce"] = {tinta: "adaugat"}
            trace["modificari"].append(self._publica(tinta, c))
            return self._scor_pas(trace, "aplicat", {"scor_nou": vs, "nivel": "in_model", "verificat_om": True}, [txt])
        if tinta in self.predictii:
            grup = self._grup_predictie(tinta, True)
            specs = [(sid, "nod" if "punct" in self.predictii[sid] else "tronson", self.predictii[sid])
                     for sid in sorted(grup, key=lambda x: "punct" not in self.predictii[x])]
            t2 = "Predicție aplicată de om în teren: " + txt
            self._adauga_in_model(specs, event, vs, [t2], None, plafoneaza=False)
            trace["_ce"] = {}
            for sid, _, _ in specs:
                c = self._marcheaza_verificat(sid, event, t2)
                self.decizii[sid] = {"decizie": "accepta", "event_id": event["event_id"], "data": data}
                trace["_ce"][sid] = "adaugat"
                trace["modificari"].append(self._publica(sid, c))
            return self._scor_pas(trace, "aplicat", {"scor_nou": vs, "nivel": "in_model", "grup": grup, "verificat_om": True}, [t2])
        if el is None or cur is None:
            return refuz(f"Nu există niciun element cu ID-ul {tinta}: verificare neaplicată.")
        if cur.get("retras") or cur["nivel"] == "scos_din_uz":
            return refuz(f"{tinta} e retras sau scos din uz: nu poate fi marcat verificat.")
        c = self._marcheaza_verificat(tinta, event, txt)
        trace["_ce"] = {tinta: "actualizat"}
        trace["modificari"].append(self._publica(tinta, c))
        self._scor_pas(trace, "aplicat", {"scor_nou": vs, "nivel": c["nivel"], "verificat_om": True}, [txt])

    def _grup_predictie(self, tinta: str, accepta: bool) -> list[str]:
        """Grupul unei predicții: nodul prezis și legăturile lui, sau legătura și nodurile ei încă prezise.
        La acceptare, o legătură intră doar dacă ambele capete există în model sau sunt în grup."""
        grup = [tinta]
        s0 = self.predictii[tinta]
        if "punct" in s0:
            grup += [sid for sid, s in self.predictii.items() if "capete" in s and tinta in s["capete"]]
        elif "capete" in s0:
            grup += [c for c in s0["capete"] if c in self.predictii and "punct" in self.predictii[c]]
        if accepta:
            noduri_ok = {c for c in grup if "punct" in self.predictii[c]} | set(self.net["noduri"])
            grup = [g for g in grup if "punct" in self.predictii[g] or g == tinta
                    or all(c in noduri_ok for c in self.predictii[g]["capete"])]
        return grup

    @staticmethod
    def _deverifica(cur: dict, event: dict) -> tuple[dict, str | None]:
        """Contradicție ulterioară: (argumente pentru `_pune`, text) dacă `cur` era verificat de om, altfel ({}, None).
        Scorul îl recalculează apelantul (scor efectiv + efectul contradicției)."""
        if not cur.get("verificat_om"):
            return {}, None
        return ({"verificat_om": False, "verificat_om_data": None},
                f"Verificarea de om din {cur.get('verificat_om_data') or 'o dată necunoscută'} a fost contrazisă de {event['event_id']}.")
