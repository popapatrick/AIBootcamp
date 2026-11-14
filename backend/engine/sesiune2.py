"""Reguli noi ale motorului pentru sesiunea 2 (date FICTIVE), ca mixin pentru `GridModel`.

- `mutare_fire`: firele dintr-o zonă au fost mutate (sens giratoriu etc.): elementele din rază trec „de verificat",
  se propune punctat un traseu nou pe străzi.
- `activ_demontat`: element scos din uz, doar cu rapoarte de la cel puțin două echipe și scor peste prag.
- `cerere_racordare`: lanț de stâlpi prezis spre o casă nouă (modulul `backend.racordare`, scris de A).
- locația din traseul tabletei (`backend.trace`, scris de A) când raportul nu are ID sau coordonate.
- val de apeluri: mai multe apeluri pe același element în aceeași fereastră cântăresc mai mult decât unul.

Toate pragurile vin din `contracts/weights.yaml`. Contracte: `contracts/interfaces.md`.
"""
from __future__ import annotations

import math

from backend.engine import scoring as S
from backend.engine.network import dist_m


def _dist_la_linie(p: tuple[float, float], puncte: list) -> float:
    """Distanța în metri de la punct la o linie frântă (proiecție locală)."""
    k = math.cos(math.radians(p[0]))
    best = float("inf")
    pts = [((a - p[0]) * 111_320, (b - p[1]) * 111_320 * k) for a, b in puncte]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]) if len(pts) > 1 else [(pts[0], pts[0])]:
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, -(x1 * dx + y1 * dy) / L2))
        best = min(best, math.hypot(x1 + t * dx, y1 + t * dy))
    return best


class Sesiune2:
    # ------------------------------------------------------------ locația din traseul tabletei
    def _foloseste_trace(self, event: dict, trace: dict) -> dict:
        """Dacă raportul are `detalii.trace` și nici ID, nici coordonate, deduce locația din opriri (backend/trace)."""
        det, ref = event.get("detalii") or {}, event.get("referinta") or {}
        pts = det.get("trace")
        if not pts or ref.get("element_id") or ref.get("coordonate"):
            return event
        try:
            from backend.engine import osm
            from backend.trace import localizeaza
        except ImportError:
            return event
        rez = localizeaza(pts, ref.get("adresa"), self.net, osm.strazi(), self.w)
        trace["pasi"].append({"nume": "trace", "incredere": rez.get("calitate"), "rezultat": rez})
        event = {**event, "detalii": {**det, "trace_rezumat": rez}}
        a = rez.get("alegere")
        if a:
            event["referinta"] = {**ref, "coordonate": {"lat": a["lat"], "lon": a["lon"]}}
        return event

    def _confirma_vizitate(self, event: dict, trace: dict):
        """Opririle scurte lângă stâlpi existenți sunt verificări în plus ale lor (doar rapoarte de teren executate)."""
        rez = (event.get("detalii") or {}).get("trace_rezumat") or {}
        if not rez.get("vizitate") or event.get("status") != "executat":
            return
        w, data = self.w, event["data"]
        deja = {s["element_id"] for s in trace["modificari"]}
        f = S.fiabilitate(event, w)
        for v in rez["vizitate"]:
            eid = v.get("element_id")
            if not eid or eid in deja or eid not in self.istoric or eid not in self._elemente():
                continue
            cur = self._curent(eid)
            eff = S.scor_la_data(cur["scor"], cur["valid_de_la"], data, w)
            delta = w["scor"]["confirmare_teren"] * f * w["potrivire"]["calitate_dupa_coordonate"]
            nivel = "in_model" if (cur["nivel"] == "de_verificat" and eff + delta >= w["praguri"]["predictie"]) else cur["nivel"]
            st = self._pune(eid, cur["tip_element"], data, nivel=nivel, scor=S.clamp(eff + delta, w), ultima_verificare=data,
                            motive=self._motiv(eid, f"Operatorul a stat {v.get('durata_min')} min lângă element (traseu tabletă): "
                                                    f"verificare, {delta:+.3f}.", delta, event))
            trace["modificari"].append(self._publica(eid, st))

    # ------------------------------------------------------------ mutare fire
    def _mutare_fire(self, event: dict, trace: dict):
        w, data = self.w, event["data"]
        cfg = w["mutare_fire"]
        det, ref = event.get("detalii") or {}, event.get("referinta") or {}
        c = det.get("centru") or ref.get("coordonate")
        if not c:
            return self._neaplicat(event, trace, "Mutare de fire fără locație: nu putem marca nicio zonă (dă coordonate sau clic pe hartă).")
        centru = (c["lat"], c["lon"])
        raza = float(det.get("raza_m") or cfg["raza_m"])
        motiv = det.get("motiv_mutare") or "mutare fire"
        f = S.fiabilitate(event, w)
        gasite = []
        for eid, el in self._elemente().items():
            if el["tip_element"] == "nod":
                d = dist_m(centru, (el["lat"], el["lon"]))
            elif el["tip_element"] == "tronson":
                d = _dist_la_linie(centru, el["puncte"])
            else:
                continue
            if d <= raza:
                gasite.append((d, eid))
        gasite.sort()
        trunchiat = len(gasite) > cfg["max_elemente"]
        gasite = gasite[:cfg["max_elemente"]]
        trace["pasi"][-1] = {"nume": "potrivire", "incredere": 1.0 if gasite else 0.0,
                             "rezultat": {"status": "zona" if gasite else "absent_din_model", "metoda": "zona",
                                          "centru": {"lat": centru[0], "lon": centru[1]}, "raza_m": raza,
                                          "elemente": len(gasite), "trunchiat": trunchiat, "motiv_mutare": motiv,
                                          "calitate": 1.0 if gasite else 0.0, "semnale": [], "candidati": [], "motiv": ""}}
        if not gasite:
            return self._neaplicat(event, trace, f"Niciun element al rețelei în raza de {raza:g} m: nimic de marcat.")
        trace["pasi"].append({"nume": "predictie", "rezultat": None, "incredere": None})
        marcate = {eid for _, eid in gasite}
        for d, eid in gasite:
            cur = self._curent(eid)
            eff = S.scor_la_data(cur["scor"], cur["valid_de_la"], data, w)
            q = 1 - 0.5 * d / raza
            delta = w["scor"]["contradictie"] * f * q
            scor = min(S.clamp(eff + delta, w), cfg["scor_marcat"])
            t = (f"Mutare de fire în zonă ({motiv}, raza {raza:g} m, la {d:.0f} m de centru, fiabilitate {f}): "
                 f"nu mai știm sigur că elementul e aici. De verificat în teren.")
            st = self._pune(eid, cur["tip_element"], data, nivel="de_verificat", scor=scor, predictie=None,
                            motive=self._motiv(eid, t, scor - eff, event))
            trace["modificari"].append(self._publica(eid, st))
        # ancore: nodurile din afara zonei legate de tronsoane marcate
        ancore = set()
        for eid in marcate:
            el = self.net["tronsoane"].get(eid)
            if el:
                ancore |= {n for n in el["capete"] if n and n not in marcate}
        ancore = sorted(ancore, key=lambda n: dist_m(centru, (self.net["noduri"][n]["lat"], self.net["noduri"][n]["lon"])))[:4]
        ancore.sort(key=lambda n: math.atan2(self.net["noduri"][n]["lat"] - centru[0], self.net["noduri"][n]["lon"] - centru[1]))
        perechi = ([(ancore[i], ancore[(i + 1) % len(ancore)]) for i in range(len(ancore))] if len(ancore) >= 3
                   else [(ancore[0], ancore[1])] if len(ancore) == 2 else [])
        propuneri, fara = 0, []
        for i, (a, b) in enumerate(perechi, 1):
            na, nb = self.net["noduri"][a], self.net["noduri"][b]
            pa, pb = (na["lat"], na["lon"]), (nb["lat"], nb["lon"])
            r = self.traseu_fn(pa, pb) if self.traseu_fn else None
            urm = r["urmeaza_strada"] if r else None
            puncte = r["puncte"] if r else [pa, pb]
            sp, factori = S.scor_propunere(event, cfg["calitate_propunere"], w, urm)
            if not r:
                sp = round(sp * cfg["factor_fara_strada"], 3)
            if sp < w["praguri"]["predictie"]:
                fara.append((a, b, sp))
                continue
            sid = f"MUT-{event['event_id']}-{i}"
            self.predictii[sid] = {"puncte": puncte, "metoda": "traseu_strada_osm" if r else "linie_dreapta",
                                   "capete": (a, b), "urmeaza": urm,
                                   "geometrie": {"type": "LineString", "coordinates": [[o, la] for la, o in puncte]}}
            txt = (f"Traseu propus între {a} și {b} după mutarea firelor ({motiv}): scor {sp}"
                   + (f", urmează strada {urm}" if urm is not None else ", fără stradă (linie dreaptă)")
                   + ". Neaplicat până la confirmarea din teren.")
            st = self._pune(sid, "tronson", data, nivel="predictie", scor=sp, ultima_verificare=None,
                            motive=[{"text": txt, "efect": 0.0, "eveniment": event["event_id"], "data": data}],
                            predictie={"metoda": "zona_mutata", "urmeaza_strada": urm,
                                       "propunere": {"proprietate": "element_nou", "valoare": sid}, "scor_propunere": sp})
            trace["modificari"].append(self._publica(sid, st))
            propuneri += 1
        if propuneri:
            trace["pasi"][-1] = {
                "nume": "predictie", "incredere": None,
                "rezultat": {"metoda": "zona_mutata", "propuneri": propuneri, "ancore": ancore}}
        elif perechi:
            trace["pasi"][-1]["rezultat"] = {"metoda": "zona_mutata", "propuneri": 0,
                                             "motiv": "scorul propunerilor sub pragul de predicție"}
        n = len(gasite)
        mesaj = (f"{n} elemente din raza de {raza:g} m marcate «de verificat» ({motiv})"
                 + (f" (plafon {w['mutare_fire']['max_elemente']}, restul nemarcate)" if trunchiat else "")
                 + (f"; {propuneri} traseu(ri) nou(i) propus(e) pe străzi, neaplicate." if propuneri
                    else "; nu s-a putut propune traseu (fără străzi apropiate sau ancore)."))
        self._scor_pas(trace, "de_verificat", {"nivel": "de_verificat", "elemente_marcate": n, "propuneri": propuneri}, [mesaj])

    # ------------------------------------------------------------ activ demontat
    def _demontat(self, event: dict, m: dict, trace: dict):
        w, data = self.w, event["data"]
        cfg = w["demontat"]
        trace["pasi"].append({"nume": "predictie", "rezultat": None, "incredere": None})
        eid = m.get("element_id")
        if m["status"] != "potrivit" or eid not in self._elemente():
            return self._scor_pas(trace, "neaplicat", {"nivel": None},
                                  [f"Demontare raportată, dar elementul nu a fost găsit în model ({m.get('motiv', '')})."])
        cur = self._curent(eid)
        eff = S.scor_la_data(cur["scor"], cur["valid_de_la"], data, w)
        sp, _ = S.scor_propunere(event, m["calitate"], w)
        lista = [x for x in self.demontari.setdefault(eid, []) if S.zile(x["data"], data) <= cfg["fereastra_zile"]]
        lista.append({"event_id": event["event_id"], "data": data, "echipa": event["echipa_sursa"], "sp": sp})
        self.demontari[eid] = lista
        echipe = {x["echipa"] for x in lista}
        necomb = 1.0
        for x in lista:
            necomb *= 1 - x["sp"]
        comb = round(1 - necomb, 3)
        el = self._elemente()[eid]
        if len(echipe) >= cfg["rapoarte_min"] and comb >= w["praguri"]["aplicat"]:
            t = (f"Demontat: {len(lista)} rapoarte de la {len(echipe)} echipe ({', '.join(sorted(echipe))}), scor combinat {comb} "
                 f"peste pragul {w['praguri']['aplicat']}: element scos din uz.")
            st = self._pune(eid, el["tip_element"], data, nivel="scos_din_uz", scor=comb, ultima_verificare=data,
                            predictie=None, motive=self._motiv(eid, t, comb - eff, event))
            trace["modificari"].append(self._publica(eid, st))
            return self._scor_pas(trace, "aplicat", {"scor_nou": comb, "nivel": "scos_din_uz", "rapoarte": len(lista)}, [t])
        f = S.fiabilitate(event, w)
        delta = w["scor"]["contradictie"] * f * m["calitate"]
        scor = S.clamp(eff + delta, w)
        nivel = "de_verificat" if scor < w["praguri"]["predictie"] else cur["nivel"]
        t = (f"Semnal de demontare ({len(lista)} raport(e) de la {len(echipe)} echipă/echipe, scor combinat {comb}): "
             f"trebuie cel puțin {cfg['rapoarte_min']} echipe și scor peste {w['praguri']['aplicat']} ca să fie scos din uz. "
             f"Elementul rămâne în model, scor {delta:+.3f}.")
        st = self._pune(eid, el["tip_element"], data, nivel=nivel, scor=scor, motive=self._motiv(eid, t, delta, event))
        trace["modificari"].append(self._publica(eid, st))
        self._scor_pas(trace, "scor_actualizat", {"scor_nou": scor, "nivel": nivel, "efect": "semnal_demontare"}, [t])

    # ------------------------------------------------------------ cerere de racordare
    def _cerere_racordare(self, event: dict, m: dict, trace: dict):
        w, data = self.w, event["data"]
        cfg = w["racordare"]
        det, ref = event.get("detalii") or {}, event.get("referinta") or {}
        loc = ref.get("coordonate") or det.get("locatie")
        trace["pasi"].append({"nume": "predictie", "rezultat": None, "incredere": None})
        if not loc:
            return self._scor_pas(trace, "neaplicat", {"nivel": None},
                                  ["Cerere de racordare fără locația casei (coordonate sau clic pe hartă): nu putem prezice lanțul."])
        try:
            from backend.engine import osm
            from backend.racordare import prezice_lant
        except ImportError:
            return self._scor_pas(trace, "neaplicat", {"nivel": None}, ["Modulul backend.racordare lipsește."])
        r = prezice_lant({"lat": loc["lat"], "lon": loc["lon"]}, self.net, osm.strazi(), w)
        trace["pasi"][-1] = {"nume": "predictie", "incredere": r.get("urmeaza_strada"),
                             "rezultat": {"metoda": "lant_racordare", **{k: r.get(k) for k in
                                          ("status", "nod_start", "distanta_m", "urmeaza_strada", "ambiguu", "motiv")},
                                          "stalpi": len(r.get("stalpi") or [])}}
        if r["status"] == "fara_nod" or not r.get("nod_start"):
            return self._scor_pas(trace, "neaplicat", {"nivel": None},
                                  [f"Niciun nod al rețelei în raza de {cfg['raza_nod_m']} m de casă: {r.get('motiv', '')}"])
        ev = event["event_id"]
        nume = {f"stalp-{s['ordine']}": f"NOU-{ev}-S{s['ordine']}" for s in r["stalpi"]}
        nume["casa"] = f"NOU-{ev}-casa"
        specs = []
        for s in r["stalpi"]:
            specs.append((nume[f"stalp-{s['ordine']}"], "nod", {"punct": (s["lat"], s["lon"]),
                          "geometrie": {"type": "Point", "coordinates": [s["lon"], s["lat"]]}}))
        specs.append((nume["casa"], "nod", {"punct": (loc["lat"], loc["lon"]),
                      "geometrie": {"type": "Point", "coordinates": [loc["lon"], loc["lat"]]}}))
        urm = r.get("urmeaza_strada")
        for k, cab in enumerate(r["cabluri"]):
            a, b = (nume.get(cab["de_la"], cab["de_la"]), nume.get(cab["la"], cab["la"]))
            pts = [tuple(p) for p in cab["puncte"]]
            specs.append((f"NOU-{ev}-L{k + 1}", "tronson", {
                "puncte": pts, "metoda": "traseu_strada_osm" if urm is not None else "linie_dreapta", "capete": (a, b),
                "urmeaza": urm, "geometrie": {"type": "LineString", "coordinates": [[o, la] for la, o in pts]}}))
        q = w["potrivire"]["calitate_dupa_coordonate"] * (0.8 if r.get("ambiguu") else 1.0)
        sp, factori = S.scor_propunere(event, q, w, urm)
        if urm is None:
            sp = round(sp * cfg["factor_fara_strada"], 3)
        niv = S.decizie(sp, w, planificat=event["status"] == "planificat")
        txt = (f"Cerere de racordare: lanț de {len(r['stalpi'])} stâlp(i) de la nodul {r['nod_start']} ({r['distanta_m']} m) spre casă, "
               f"scor {sp} (fiabilitate {factori['fiabilitate_sursa']}, extracție {factori['incredere_extractie']}, "
               f"potrivire {factori['calitate_potrivire']}" + (f", urmează strada {urm}" if urm is not None else ", fără stradă") + ").")
        if niv == "de_verificat":
            return self._scor_pas(trace, "neaplicat", {"scor_propunere": sp, "nivel": niv},
                                  [txt + f" Sub pragul {w['praguri']['predictie']}: nu se desenează."], sp)
        if niv == "in_model":
            self._adauga_in_model(specs, event, sp, [txt + f" Peste pragul {w['praguri']['aplicat']}: adăugat în model, în timp real."], None)
            dec = "adaugat"
        else:
            for sid, tip_el, s in specs:
                self.predictii[sid] = s
                pr = {"metoda": "lant_racordare" if urm is not None or tip_el == "nod" else "linie_dreapta",
                      "urmeaza_strada": urm if tip_el == "tronson" else None,
                      "propunere": {"proprietate": "element_nou", "valoare": sid}, "scor_propunere": sp}
                self._pune(sid, tip_el, data, nivel="predictie", scor=sp, ultima_verificare=None, predictie=pr,
                           motive=[{"text": txt + f" Sub pragul {w['praguri']['aplicat']}: predicție, neaplicată; fiecare stâlp poate fi "
                                                  "acceptat sau respins separat.", "efect": 0.0, "eveniment": ev, "data": data}])
            dec = "predictie"
        for sid, _, _ in specs:
            trace["modificari"].append(self._publica(sid, self._curent(sid)))
        self._scor_pas(trace, dec, {"scor_propunere": sp, "factori": factori, "nivel": "in_model" if dec == "adaugat" else "predictie"}, [txt], sp)

    # ------------------------------------------------------------ val de apeluri
    def _val_apeluri(self, eid: str, data: str, delta: float, motive: list[str]) -> float:
        """Apelurile repetate pe același element, în fereastră, cântăresc mai mult decât unul, până la un plafon."""
        cfg = self.w["val_apeluri"]
        lista = [x for x in self.apeluri.setdefault(eid, []) if S.zile(x[0], data) <= cfg["fereastra_zile"]]
        n = len(lista) + 1
        if n >= cfg["numar_min"]:
            delta = delta * (1 + 0.5 * (n - 1))
            motive.append(f"Val de apeluri: {n} apeluri în {cfg['fereastra_zile']} zile pe același element, semnal mai puternic "
                          f"(plafon {cfg['plafon_semnal']}).")
        deja = sum(x[1] for x in lista)
        delta = max(delta, -cfg["plafon_semnal"] - deja)
        delta = min(delta, 0.0)
        lista.append((data, delta))
        self.apeluri[eid] = lista
        return delta
