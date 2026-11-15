"""Tracking echipe (sesiunea 4b, B2): evenimentul `tracking_tura`, tura simulată a unei tablete GPS aplicată în model.

Mixin pentru `GridModel` (folosește `self.net`, `self.w`, `self.istoric`, `self.predictii`, `self.ture_aplicate`,
`self._pune`, `self._publica`, `self._curent`, `self._eff`, `self._motiv`, `self._scor_pas`). Date FICTIVE.
Plan: `docs/plan-tracking-echipe.md` (2.2); documentație: `docs/etapa-32-tracking-echipe.md`, secțiunea „Motor (B2)”.

Evenimentul vine deja structurat (`detalii.tura.puncte` = [{t, lat, lon}]), fără text de standardizat, deci nu trece prin
extracție/potrivire. Opririle se detectează din puncte cu `backend.trace.gaseste_opriri`, cu `trace.durata_min_min` coborât
la 1 min (altfel opririle scurte, de semafor, de 1-2 min, ar rămâne nevăzute; așa apar ca `scurta`).

Clasificarea fiecărei opriri (valorile din `weights.yaml`, secțiunea `tracking`):
  scurta          durată < `durata_validare_min`: ignorată, fără efect;
  validare        stâlp existent la <= `raza_validare_m` (durata >= `durata_validare_min`): confirmare
                  `scor.confirmare_teren × fiabilitate_sursa.tracking_gps × calitate`, calitatea = 1 la 0 m, scade liniar
                  la 0,5 la `raza_validare_m`; scorul pornește de la scorul efectiv la data turei (regimul corect ca la V1),
                  plafonat după sursa locației (poziția devine cel puțin `coordonate`, plafon 0,85, pentru ce nu e GIS);
  stalp_presupus  niciun nod la <= `raza_fara_stalp_m` și durata >= `durata_stalp_nou_min`: predicție `TRK-<event>-<n>`
                  (scor <= `plafon_stalp_presupus`) cu legătura pe străzi `TRK-<event>-<n>-L`; niciodată aplicat;
  neclara         orice altceva (între praguri, același stâlp validat deja, în afara zonei): doar în jurnal.
"""
from __future__ import annotations

from datetime import datetime

from backend.engine import analiza_harta as AH
from backend.engine import scoring as S
from backend.engine.network import dist_m
from backend.engine.zona import motiv_afara, zona_ok

DURATA_MIN_DETECTIE = 1.0       # minute: opririle sub asta nu sunt raportate deloc de detector


def _n(x: float, z: int = 1) -> str:
    """Număr cu virgulă, fără zerouri inutile (8 / 8,5)."""
    s = f"{x:.{z}f}".rstrip("0").rstrip(".")
    return (s or "0").replace(".", ",")


def _pl(n: int, sg: str, pl: str) -> str:
    return f"{n} {sg if n == 1 else pl}"


class Tracking:
    """Metodele B2, amestecate în `GridModel`: `_tracking_tura` (ramura `tip == "tracking_tura"` din `apply_event`)."""

    # ------------------------------------------------------------------ utilitare
    def _stalpi_eligibili(self) -> list[dict]:
        """Stâlpii existenți care pot fi validați: noduri din rețea, fără case `*-casa`, fără retrase / scoase din uz /
        predicții (predicțiile nu sunt în `net`)."""
        out = []
        for nid, n in self.net["noduri"].items():
            if str(nid).endswith("-casa") or nid in self.predictii:
                continue
            cur = self.istoric.get(nid, [None])[-1]
            if cur is None or cur.get("retras") or cur["nivel"] not in ("in_model", "de_verificat"):
                continue
            out.append(n)
        return out

    def _detecteaza_opriri(self, puncte: list[dict]) -> list[dict]:
        """Opririle din puncte (`gaseste_opriri`), cu `trace.durata_min_min` coborât la 1 min (sau la `durata_validare_min`,
        dacă e mai mică), ca opririle scurte să fie raportate."""
        from backend.trace import gaseste_opriri
        cfg = {**self.w, "trace": {**self.w["trace"],
                                   "durata_min_min": min(DURATA_MIN_DETECTIE, float(self.w["tracking"]["durata_validare_min"]))}}
        return gaseste_opriri(puncte, cfg)

    def _clasifica(self, opriri: list[dict]) -> list[dict]:
        """Pune `tip` (+ `element_id`, `distanta_m`, `motiv`) pe fiecare oprire, după tabelul din docstring-ul modulului."""
        T = self.w["tracking"]
        stalpi = self._stalpi_eligibili()
        toate = list(self.net["noduri"].values())
        out = []
        for o in opriri:
            p, d_min = (o["lat"], o["lon"]), o["durata_min"]
            r = {"lat": round(o["lat"], 6), "lon": round(o["lon"], 6), "inceput": o["inceput"], "sfarsit": o["sfarsit"],
                 "durata_min": d_min, "tip": "neclara", "t_ajungere": o["inceput"], "motiv": ""}
            if d_min < T["durata_validare_min"]:
                r.update(tip="scurta", motiv=f"Oprire scurtă ({_n(d_min)} min, sub {_n(T['durata_validare_min'])} min): ignorată.")
                out.append(r)
                continue
            cel = min(((dist_m(p, (n["lat"], n["lon"])), n["id"]) for n in stalpi), default=(None, None))
            if cel[0] is not None and cel[0] <= T["raza_validare_m"]:
                r.update(tip="validare", element_id=cel[1], distanta_m=round(cel[0], 1))
            else:
                any_d = min((dist_m(p, (n["lat"], n["lon"])) for n in toate), default=None)
                if (any_d is None or any_d > T["raza_fara_stalp_m"]) and d_min >= T["durata_stalp_nou_min"]:
                    r.update(tip="stalp_presupus", distanta_m=None if cel[0] is None else round(cel[0], 1),
                             element_id=None)
                    r["_cel_mai_apropiat"] = cel
                else:
                    r.update(motiv=f"Oprire neclară ({_n(d_min)} min; cel mai apropiat stâlp la "
                                   f"{'?' if cel[0] is None else _n(cel[0])} m): nici validare, nici stâlp nou.",
                             distanta_m=None if cel[0] is None else round(cel[0], 1))
            out.append(r)
        # un stâlp se validează o singură dată pe tură: oprirea cea mai lungă (la egalitate, prima)
        cele_mai = {}
        for i, r in enumerate(out):
            if r["tip"] == "validare":
                j = cele_mai.get(r["element_id"])
                if j is None or r["durata_min"] > out[j]["durata_min"]:
                    cele_mai[r["element_id"]] = i
        for i, r in enumerate(out):
            if r["tip"] == "validare" and cele_mai[r["element_id"]] != i:
                r.update(tip="neclara", motiv=f"{r['element_id']} e validat în această tură de o oprire mai lungă: numărat o singură dată.")
        return out

    # ------------------------------------------------------------------ validare
    def _valideaza(self, event: dict, o: dict, tura_id: str, echipa: str, inainte: dict, trace: dict) -> dict | None:
        """Aplică validarea unei opriri pe stâlpul `o["element_id"]`; completează scorurile pe `o`; întoarce starea nouă (sau None)."""
        w, data, eid = self.w, event["data"], o["element_id"]
        T = w["tracking"]
        cur = self._curent(eid)
        eff = self._eff(cur, data)
        o["scor_inainte"], o["banda_inainte"] = round(eff, 3), S.banda(eff, w)
        inainte[eid] = eff              # „înainte” = scorul efectiv la data turei (ce arată harta), nu scorul stocat
        cal = max(0.5, 1.0 - 0.5 * o["distanta_m"] / T["raza_validare_m"])
        o["calitate"] = round(cal, 3)
        durata, dist = _n(o["durata_min"]), _n(o["distanta_m"])
        baza = f"Tura {tura_id} a echipei {echipa}: oprire de {durata} min la {dist} m"
        if cur.get("verificat_om"):
            o.update(scor_dupa=round(eff, 3), banda_dupa=S.banda(eff, w), om=True,
                     motiv=f"{baza} de stâlp; elementul e verificat de om, scorul nu se schimbă.")
            # versiune nouă cu scorul efectiv (aceeași valoare) ca motivul să intre în jurnal fără să reseteze scăderea în timp
            return self._pune(eid, cur["tip_element"], data, scor=eff, motive=self._motiv(eid, o["motiv"], 0.0, event))
        delta = w["scor"]["confirmare_teren"] * w["fiabilitate_sursa"]["tracking_gps"] * cal
        scor = S.clamp(eff + delta, w)
        motive = [f"Confirmat de tura {tura_id} a echipei {echipa}: oprire de {durata} min la {dist} m. "
                  f"Confirmare {delta:+.3f} (fiabilitate GPS {w['fiabilitate_sursa']['tracking_gps']:g}, calitate {_n(cal, 2)})."]
        extra: dict = {}
        if not self._e_gis(cur):
            veche = cur.get("sursa_locatie")
            noua = S.mai_buna(veche, "coordonate")
            if noua != veche:
                extra["sursa_locatie"] = noua
                motive.append(f"Poziția vine acum din GPS (coordonate): plafonul crește de la {S.fmt(S.plafon(veche, w))} la {S.fmt(S.plafon(noua, w))}.")
            sursa = extra.get("sursa_locatie", veche)
            if sursa and scor > S.plafon(sursa, w) and scor > eff:
                scor = max(S.plafon(sursa, w), eff)
                motive.append(S.text_plafon(sursa, w))
        nivel = cur["nivel"]
        if nivel == "de_verificat" and scor >= w["praguri"]["predictie"]:
            nivel = "in_model"
        delta_real = scor - eff
        st = self._pune(eid, cur["tip_element"], data, **extra, **self._fara_marker(cur), nivel=nivel, scor=scor,
                        ultima_verificare=data, ultima_validare_tracking=data,
                        motive=self._motiv(eid, " ".join(motive), delta_real, event))
        o.update(scor_dupa=round(scor, 3), banda_dupa=S.banda(scor, w), motiv=" ".join(motive))
        return st

    # ------------------------------------------------------------------ stâlp presupus
    def _presupune(self, event: dict, o: dict, n: int, tura_id: str, echipa: str, trace: dict) -> list[str]:
        """Predicție `TRK-<event>-<n>` (nod) + legătura pe străzi `TRK-<event>-<n>-L`; întoarce ID-urile create (poate fi gol
        dacă punctul e în afara zonei: atunci oprirea devine `neclara`)."""
        w, data = self.w, event["data"]
        T = w["tracking"]
        pt = (o["lat"], o["lon"])
        z = zona_ok(pt[0], pt[1], self.net, w)
        if not z["ok"]:
            o.update(tip="neclara", motiv="Oprire în afara zonei prototipului: " + motiv_afara(z))
            return []
        sid = f"TRK-{event['event_id']}-{n}"
        lid = f"{sid}-L"
        ev = {**event, "tip_sursa_pondere": "tracking_gps", "incredere_extractie": 1.0}
        q = float(w["potrivire"]["calitate_dupa_coordonate"])
        try:
            ah = AH.traseu_pe_strazi(pt, self.net, w)
        except Exception as e:      # fără cache OSM: stâlpul rămâne presupus, fără legătură
            ah = None
            trace["pasi"].append({"nume": "analiza_harta", "incredere": 0.0,
                                  "rezultat": {"capat": sid, "motiv": f"analiza hărții indisponibilă: {e}"}})
        leg = bool(ah and ah["ales"])
        urm = ah["factor"] if leg and not ah["fara_drum"] else None
        sp, factori = S.scor_propunere(ev, q, w, urm)
        pen = self.penalizare_metoda.get("oprire_tracking", 0.0)
        if pen:
            sp = S.clamp(sp - pen, w)
        scor = round(min(sp, float(T["plafon_stalp_presupus"]), S.plafon("coordonate", w)), 3)
        cel = o.pop("_cel_mai_apropiat", (None, None))
        txt = (f"Stâlp presupus de tura {tura_id} a echipei {echipa}: oprire de {_n(o['durata_min'])} min fără niciun nod la mai puțin de "
               f"{_n(T['raza_fara_stalp_m'])} m"
               + (f" (cel mai apropiat stâlp: {cel[1]}, la {_n(cel[0])} m)" if cel[0] is not None else "")
               + f". Scor propunere {sp}, plafonat la {_n(T['plafon_stalp_presupus'], 2)}: {scor}. Predicție, neaplicată în model.")
        self.predictii[sid] = {"punct": pt, "sursa_locatie": "coordonate",
                               "geometrie": {"type": "Point", "coordinates": [pt[1], pt[0]]}}
        pr = {"metoda": "oprire_tracking", "urmeaza_strada": urm, "propunere": {"proprietate": "element_nou", "valoare": sid},
              "scor_propunere": sp, "tura_id": tura_id, "durata_min": o["durata_min"]}
        st = self._pune(sid, "nod", data, nivel="predictie", scor=scor, ultima_verificare=None, t0=False, predictie=pr,
                        sursa_locatie="coordonate", motive=[{"text": txt, "efect": 0.0, "eveniment": event["event_id"], "data": data}])
        ids = [sid]
        mods = [self._publica(sid, st)]
        if leg:
            ales = ah["ales"]
            trace["pasi"].append({"nume": "analiza_harta", "incredere": ah["acuratete"],
                                  "rezultat": {**ah, "vecin": ales["de_la"], "capat": sid}})
            pts = [tuple(p) for p in ales["traseu"]]
            metoda = "linie_dreapta" if ah["fara_drum"] else "traseu_pe_strazi"
            scor_l = round(min(sp, float(S.plafon("analiza_harta", w)), scor), 3)
            an = {"traseu": ales["traseu"], "alternative": ah["alternative"]}
            self.predictii[lid] = {"puncte": pts, "metoda": metoda, "capete": (ales["de_la"], sid), "urmeaza": urm,
                                   "sursa_locatie": "analiza_harta", "analiza": an,
                                   "geometrie": {"type": "LineString", "coordinates": [[b, a] for a, b in pts]}}
            tl = (f"Legătură presupusă între stâlpul existent {ales['de_la']} și {sid}, {ales['lungime_m']:g} m "
                  f"{'pe străzi' if metoda == 'traseu_pe_strazi' else 'în linie dreaptă (nicio stradă credibilă)'}, scor {scor_l} "
                  f"(plafon analiza hărții {_n(S.plafon('analiza_harta', w), 2)}). Predicție, neaplicată în model.")
            sl = self._pune(lid, "tronson", data, nivel="predictie", scor=scor_l, ultima_verificare=None, t0=False,
                            sursa_locatie="analiza_harta",
                            predictie={"metoda": metoda, "urmeaza_strada": urm,
                                       "propunere": {"proprietate": "element_nou", "valoare": lid}, "scor_propunere": sp,
                                       "traseu": ales["traseu"], "alternative": ah["alternative"], "legat_de": ales["de_la"],
                                       "lungime_m": ales["lungime_m"]},
                            motive=[{"text": tl, "efect": 0.0, "eveniment": event["event_id"], "data": data}])
            ids.append(lid)
            mods.append(self._publica(lid, sl))
        elif ah is not None:
            trace["pasi"].append({"nume": "analiza_harta", "incredere": ah["acuratete"],
                                  "rezultat": {**ah, "capat": sid, "motiv": "Niciun stâlp existent în raza de căutare: fără legătură."}})
        trace["modificari"].extend(mods)
        o.update(element_id=sid, scor_dupa=scor, banda_dupa=S.banda(scor, w), motiv=txt, scor_propunere=sp,
                 legatura_id=lid if leg else None)
        trace["_ce"] = {**trace.get("_ce", {}), **{i: "predictie" for i in ids}}
        return ids

    # ------------------------------------------------------------------ eveniment
    def _tracking_tura(self, event: dict, trace: dict, inainte: dict) -> None:
        """Aplică o tură: opriri -> clasificare -> validări / stâlpi presupuși. Scrie `detalii.tracking` pe eveniment,
        pașii `opriri` și `validari_tracking`, `jurnal[-1]` primește `rezumat` (prin `trace["_rezumat"]`)."""
        w, data = self.w, event["data"]
        det = event.setdefault("detalii", {})
        tura = det.get("tura") or {}
        tura_id = tura.get("tura_id") or f"TURA-{event['event_id']}"
        echipa = tura.get("echipa") or event.get("echipa_sursa") or "echipa"

        def tracking_gol(motiv: str):
            det["tracking"] = {"opriri": [], "validari": [], "presupuneri": [], "ignorate": 0, "de_ce": motiv}

        if tura_id in self.ture_aplicate:
            motiv = f"Tura {tura_id} a fost deja aplicată (eveniment {self.ture_aplicate[tura_id]}): fără efect."
            tracking_gol(motiv)
            trace["pasi"].append({"nume": "opriri", "incredere": None, "rezultat": {"tura_id": tura_id, "opriri": [], "motiv": motiv}})
            trace["_rezumat"] = motiv
            return self._scor_pas(trace, "fara_efect", {"nivel": None, "tura_id": tura_id, "duplicat": True}, [motiv])
        self.ture_aplicate[tura_id] = event["event_id"]
        puncte = tura.get("puncte") or []
        if len(puncte) < 2:
            motiv = f"Tura {tura_id} nu are destule puncte GPS (cel puțin 2): fără efect."
            tracking_gol(motiv)
            trace["pasi"].append({"nume": "opriri", "incredere": None, "rezultat": {"tura_id": tura_id, "opriri": [], "motiv": motiv}})
            trace["_rezumat"] = motiv
            return self._scor_pas(trace, "fara_efect", {"nivel": None, "tura_id": tura_id}, [motiv])

        opriri = self._clasifica(self._detecteaza_opriri(puncte))
        dur = (datetime.fromisoformat(puncte[-1]["t"]) - datetime.fromisoformat(puncte[0]["t"])).total_seconds() / 60
        pas_opriri = {"nume": "opriri", "incredere": None,
                      "rezultat": {"tura_id": tura_id, "echipa": echipa, "n_puncte": len(puncte), "durata_tura_min": round(dur, 1),
                                   "opriri": opriri, "pe_tip": {}}}
        trace["pasi"].append(pas_opriri)

        validari, om_neschimbate = [], []
        for o in opriri:
            if o["tip"] != "validare":
                continue
            st = self._valideaza(event, o, tura_id, echipa, inainte, trace)
            if st is None:
                continue
            trace["modificari"].append(self._publica(o["element_id"], st))
            (om_neschimbate if o.get("om") else validari).append(o["element_id"])
            trace.setdefault("_ce", {})[o["element_id"]] = "actualizat"
        trace["pasi"].append({"nume": "validari_tracking", "incredere": None,
                              "rezultat": {"validari": [o for o in opriri if o["tip"] == "validare"],
                                           "verificat_om_neschimbat": om_neschimbate}})
        presupuneri, n = [], 0
        for o in opriri:
            if o["tip"] != "stalp_presupus":
                continue
            # un al doilea stâlp presupus la mai puțin de `raza_fara_stalp_m` de unul deja presupus în tură sau existent ca predicție
            raza = w["tracking"]["raza_fara_stalp_m"]
            deja = next((p for p, s in self.predictii.items() if "punct" in s and p.startswith("TRK-")
                         and dist_m((o["lat"], o["lon"]), s["punct"]) <= raza), None)
            if deja:
                o.pop("_cel_mai_apropiat", None)
                o.update(tip="neclara", element_id=None,
                         motiv=f"Există deja un stâlp presupus ({deja}) la mai puțin de {_n(raza)} m: nu se mai presupune unul.")
                continue
            ids = self._presupune(event, o, n + 1, tura_id, echipa, trace)
            if ids:
                n += 1
                presupuneri.append(ids[0])
        for o in opriri:
            o.pop("_cel_mai_apropiat", None)
        if presupuneri:
            trace["pasi"].append({"nume": "predictie", "incredere": None,
                                  "rezultat": {"metoda": "oprire_tracking", "elemente": presupuneri}})
        scurte = sum(o["tip"] == "scurta" for o in opriri)
        neclare = sum(o["tip"] == "neclara" for o in opriri)
        pas_opriri["rezultat"]["pe_tip"] = {t: sum(o["tip"] == t for o in opriri) for t in ("validare", "stalp_presupus", "scurta", "neclara")}
        # rezumat lizibil
        bucati = []
        if validari:
            bucati.append(_pl(len(validari), "stâlp confirmat", "stâlpi confirmați"))
        if om_neschimbate:
            bucati.append(_pl(len(om_neschimbate), "stâlp verificat de om (neschimbat)", "stâlpi verificați de om (neschimbați)"))
        if presupuneri:
            bucati.append(_pl(len(presupuneri), "stâlp presupus", "stâlpi presupuși"))
        if scurte:
            bucati.append(_pl(scurte, "oprire scurtă", "opriri scurte"))
        if neclare:
            bucati.append(_pl(neclare, "oprire neclară", "opriri neclare"))
        rezumat = f"Tura echipei {echipa}: " + (", ".join(bucati) if bucati else "nicio oprire") + "."
        det["tracking"] = {"opriri": [{k: v for k, v in o.items() if k != "om"} for o in opriri],
                           "validari": validari, "presupuneri": presupuneri, "ignorate": scurte, "de_ce": rezumat}
        trace["_rezumat"] = rezumat
        if validari:
            self._scor_pas(trace, "scor_actualizat", {"nivel": None, "tura_id": tura_id, "validari": validari, "presupuneri": presupuneri}, [rezumat])
        elif presupuneri:
            self._scor_pas(trace, "predictie", {"nivel": "predictie", "tura_id": tura_id, "presupuneri": presupuneri}, [rezumat])
        else:
            self._scor_pas(trace, "fara_efect", {"nivel": None, "tura_id": tura_id}, [rezumat])
