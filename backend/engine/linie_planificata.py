"""Linie planificată (`linie_planificata`): scara de localizare și predicția punctată pe străzi (sesiunea 4, 7.1).

Un raport de investiții „linie nouă planificată" nu schimbă rețeaua (nu e executat), dar trebuie să apară pe hartă ca
predicție punctată `PLAN-<event_id>`. `LiniePlanificata` e un mixin pentru `GridModel` (folosește `self.net`, `self.w`,
`self.ancore`, `self.predictii`, `self._pune`, `self._publica`, `self._scor_pas`, `self._eronat`).

Scara (prima treaptă care se aplică; rezultatul e MEREU predicție, niciodată aplicat):
  1. 2 noduri cunoscute (`detalii.noduri`, `referinta.element_id`, ID-uri de 7 cifre din text) -> traseu pe străzi între ele
     (`analiza_harta.traseu_pe_strazi`, de la primul nod la al doilea). Sursa locației `id`.
  2. 2 puncte GPS (`detalii.puncte` = [{lat, lon}, {lat, lon}], sau `referinta.coordonate` + `detalii.coordonate_2`) ->
     traseu pe străzi între ele (`osm.traseu`). Sursa `coordonate`. Fără stradă credibilă: linie dreaptă, `metoda` rămâne
     `linie_dreapta` și calitatea scade la `analiza_harta.fara_drum`.
  3. un punct de ancorare (un nod/ID, sau un punct GPS, sau poziția potrivită cu un stâlp existent) + stradă (adresă) ->
     segment de stradă de la ancoră, în sensul ferestrei (altfel spre capătul opus startului), lung cât `detalii.lungime_m`
     (altfel `LINIE_IMPLICITA_M`). Ancoră nod = `id`, GPS = `coordonate`. Ancoră + doar un punct (fără stradă): traseu pe
     străzi de la cel mai apropiat stâlp existent la punct (sursa `coordonate`).
  4. adresă/stradă (cu sau fără indiciu: „între nr. 10 și 40", „colț cu Y", „de la colțul cu Y până la capăt") ->
     segmentul de stradă din fereastra `backend.geo.fereastra_strada` (sursa după indiciu: adresa_numar | intersectie |
     strada | reper); lungimea din `detalii.lungime_m` taie sau prelungește fereastra (nu și `intre`, care e explicit);
     fără lungime, cel mult `LINIE_MAX_M`. Dacă începutul/sfârșitul e la peste `LEGAT_MAX_M` de cel mai apropiat stâlp
     existent, segmentul se leagă de acel stâlp pe străzi (`traseu_pe_strazi`), iar calitatea se înmulțește cu factorul lui.
  5. niciun indiciu de loc (sau doar un nod fără direcție) -> `neaplicat`.

Stâlpii intermediari NU se generează (doar tronsonul `PLAN-*`): o linie planificată nu are încă stâlpi stabiliți.
Safeguard: un capăt în afara zonei de `zona.raza_max_m` -> „eronat în cadrul prototipului", neaplicat.
Determinist, fără AI aici (numele străzii e ales în `backend.geo`)."""
from __future__ import annotations

import math
import re

from backend.engine import analiza_harta as AH
from backend.engine import osm
from backend.engine import scoring as S
from backend.engine.network import dist_m
from backend.engine.zona import zona_ok

LINIE_IMPLICITA_M = 100.0   # lungimea segmentului pornit dintr-o ancoră, când raportul nu dă `lungime_m`
LINIE_MAX_M = 300.0         # fără lungime declarată, o fereastră mai lungă (ex. toată strada) se taie la atât, centrat
LEGAT_MAX_M = 40.0          # începutul/sfârșitul segmentului mai departe de atât de un stâlp existent se leagă pe străzi
_CAPAT = re.compile(r"\bpana\s+la\s+(?:capat|sfarsit)", re.I)


def _fd(s: str) -> str:
    from backend.geo.fereastra import fara_diac
    return fara_diac(s or "").lower()


def _punct(d) -> tuple[float, float] | None:
    try:
        return (float(d["lat"]), float(d["lon"]))
    except (KeyError, TypeError, ValueError):
        return None


class LiniePlanificata:
    """Mixin: `_planificata(event, m, trace)` = scara de mai sus."""

    # ------------------------------------------------------------------ indicii de loc
    def _indicii_planificata(self, event: dict, m: dict) -> dict:
        """{noduri[id], gps2[(lat,lon)x2]|None, punct (lat,lon)|None, sursa_punct, q_punct, nod_potrivit}: ce loc dă raportul."""
        det, ref = event.get("detalii") or {}, event.get("referinta") or {}
        noduri: list[str] = []

        def adauga(x):
            x = str(x or "").strip()
            if x in self.net["noduri"] and not x.endswith("-casa") and x not in noduri:
                noduri.append(x)
        for n in det.get("noduri") or []:
            adauga(n)
        adauga(ref.get("element_id"))
        for tok in re.findall(r"\b\d{7}\b", event.get("text_original") or ""):
            adauga(tok)
        gps2 = None
        pcte = [_punct(p) for p in det.get("puncte") or []]
        if len([p for p in pcte if p]) >= 2:
            gps2 = [p for p in pcte if p][:2]
        c1, c2 = _punct(ref.get("coordonate")), _punct(det.get("coordonate_2"))
        geo = det.get("geocodare")
        din_geo = bool(geo and c1 and (geo.get("lat"), geo.get("lon")) == c1)
        if gps2 is None and c1 and c2 and not din_geo:
            gps2 = [c1, c2]
        punct = c1 or _punct(det.get("locatie")) or _punct(det.get("locatie_operator"))
        sursa_p, q_p = (self._sursa_din_geocodare(geo), float(geo["acuratete"])) if din_geo else (self._sursa_eveniment(event), None)
        nod_m = m.get("element_id") if m.get("status") == "potrivit" and m.get("element_id") in self.net["noduri"] else None
        return {"noduri": noduri, "gps2": gps2, "punct": punct, "sursa_punct": sursa_p, "q_punct": q_p, "nod_potrivit": nod_m,
                "geocodat": din_geo}

    def _fereastra_planificata(self, event: dict, trace: dict) -> dict | None:
        """Fereastra de pe stradă: cea din geocodare (`_fereastra`) sau, dacă raportul are deja coordonate, una calculată aici
        din adresă. Doar cu `status == "gasit"` (sau „in_afara_zonei", pe care chemătorul îl tratează ca eronat)."""
        fer = event.get("_fereastra")
        if fer:
            return fer
        ref = event.get("referinta") or {}
        if not (ref.get("adresa") or ref.get("adresa_structurata")):
            return None
        try:
            from backend.geo import fereastra_strada
            fer = fereastra_strada(ref, osm.strazi(), self.w, self.ancore, self.net)
        except Exception as e:      # fără cache OSM: fără fereastră
            trace["pasi"].append({"nume": "cautare_strada", "incredere": 0.0,
                                  "rezultat": {"status": "necunoscut", "motiv": f"căutare pe stradă indisponibilă: {e}"}})
            return None
        return fer if fer.get("status") in ("gasit", "in_afara_zonei") else None

    # ------------------------------------------------------------------ rutare
    def _ruta_nod(self, de_la: str, tinta: tuple[float, float], sursa: str) -> dict:
        """Traseu pe străzi de la nodul `de_la` la `tinta` (analiza_harta). {puncte, metoda, q, ah}."""
        ah = AH.traseu_pe_strazi(tinta, self.net, self.w, de_la=de_la, sursa=sursa)
        if not ah["ales"]:
            n = self.net["noduri"][de_la]
            return {"puncte": [(n["lat"], n["lon"]), tinta], "metoda": "linie_dreapta", "q": float(self.w["analiza_harta"]["fara_drum"]), "ah": ah}
        return {"puncte": [tuple(p) for p in ah["ales"]["traseu"]], "metoda": "linie_dreapta" if ah["fara_drum"] else "traseu_pe_strazi",
                "q": ah["factor"], "ah": ah}

    def _ruta_puncte(self, a: tuple[float, float], b: tuple[float, float]) -> dict:
        """Traseu pe străzi între două puncte GPS (`osm.traseu`); fără stradă credibilă, linie dreaptă. {puncte, metoda, q, r}."""
        c = self.w["analiza_harta"]
        r = osm.traseu(a, b)
        if not r:
            return {"puncte": [a, b], "metoda": "linie_dreapta", "q": float(c["fara_drum"]), "r": None}
        q = max(float(c["factor_min"]), math.exp(-r["lungime_m"] / float(c["lungime_referinta_m"])))
        return {"puncte": [tuple(p) for p in r["puncte"]], "metoda": "traseu_pe_strazi", "q": round(q, 4), "r": r}

    # ------------------------------------------------------------------ segment pe stradă
    def _strada_intreaga(self, strada: str):
        """Cale (orientată ca în fereastră) a întregii străzi `strada`, sau None."""
        from backend.geo import fereastra_strada
        from backend.geo.fereastra import Cale
        f = fereastra_strada({"adresa_structurata": {"strada": strada, "numar": None, "reper": None, "indiciu": None}, "adresa": strada},
                             osm.strazi(), self.w, self.ancore, self.net)
        return Cale(f["linie"]) if f.get("linie") and len(f["linie"]) >= 2 else None

    def _segment_strada(self, event: dict, fer: dict, ancora: tuple[float, float] | None) -> tuple[list, str, float]:
        """(puncte [(lat, lon)], text, lungime_m) ale segmentului de stradă pentru raport; vezi docstring-ul modulului, treapta 3/4."""
        cale = self._strada_intreaga(fer["strada"])
        if cale is None:
            pts = [tuple(p) for p in fer["linie"]]
            return pts, f"fereastra de pe {fer['strada']}", sum(dist_m(a, b) for a, b in zip(pts, pts[1:]))
        det = event.get("detalii") or {}
        try:
            lung = float(det.get("lungime_m")) if det.get("lungime_m") else None
        except (TypeError, ValueError):
            lung = None
        ind = fer.get("indiciu") or {}
        tip = ind.get("tip")
        s0, s1 = float(fer["de_la_m"]), float(fer["pana_la_m"])
        sc = (s0 + s1) / 2
        text_cap = _fd((event.get("text_original") or "") + " " + ((event.get("referinta") or {}).get("adresa") or ""))
        if ancora is not None:
            sa, _ = cale.proiecteaza(ancora)
            sens = 1 if sc >= sa - 5 else -1
            ln = lung or LINIE_IMPLICITA_M
            a, b = cale.clamp(sa), cale.clamp(sa + sens * ln)
            if abs(b - a) < ln - 0.5:                      # capătul străzii: se merge în sens opus cât mai rămâne
                b = cale.clamp(sa - sens * ln)
            s0, s1, expl = min(a, b), max(a, b), f"de la ancoră (la {sa:.0f} m de start) de-a lungul străzii {fer['strada']}, {abs(b - a):.0f} m"
        elif tip == "colt" and _CAPAT.search(text_cap):
            s0, s1, expl = cale.clamp(sc), cale.L, f"de la colțul cu {ind.get('strada_2') or 'cealaltă stradă'} până la capătul străzii {fer['strada']}"
        elif tip == "intre":
            expl = f"între cele două numere de pe {fer['strada']} ({s1 - s0:.0f} m)"
        else:
            ln = lung if lung else (LINIE_MAX_M if s1 - s0 > LINIE_MAX_M else None)
            if ln and s1 - s0 > ln:
                s0, s1 = sc - ln / 2, sc + ln / 2          # tăiat, centrat pe mijlocul ferestrei
            elif ln and s1 - s0 < ln:
                s1 = s0 + ln                                 # prelungit spre capătul opus startului
                if s1 > cale.L:
                    s0, s1 = cale.L - ln, cale.L
            s0, s1 = cale.clamp(s0), cale.clamp(s1)
            expl = f"în fereastra de pe {fer['strada']} ({self._text_indiciu(ind)}), {s1 - s0:.0f} m"
        pts = [tuple(p) for p in cale.linie(s0, s1)]
        return pts, expl, sum(dist_m(a, b) for a, b in zip(pts, pts[1:]))

    def _leaga_de_stalp(self, pts: list, sursa: str) -> tuple[list, float, dict | None]:
        """Dacă un capăt al segmentului e la > `LEGAT_MAX_M` de cel mai apropiat stâlp existent, îl leagă pe străzi de acel stâlp.
        Întoarce (puncte noi, factor, rezultatul analizei sau None)."""
        reale = [n for n in self.net["noduri"].values() if not str(n["id"]).endswith("-casa")]
        if not reale or len(pts) < 2:
            return pts, 1.0, None
        cap = []
        for cap_i, p in ((0, pts[0]), (1, pts[-1])):
            d = min(dist_m(p, (n["lat"], n["lon"])) for n in reale)
            cap.append((d, cap_i))
        d, i = min(cap)
        if d <= LEGAT_MAX_M:
            return pts, 1.0, None
        ah = AH.traseu_pe_strazi(pts[0] if i == 0 else pts[-1], self.net, self.w, sursa=sursa)
        if not ah["ales"] or ah["fara_drum"] or ah["ales"]["taiat"]:
            return pts, 1.0, ah if ah["ales"] else None
        leg = [tuple(p) for p in ah["ales"]["traseu"]]
        full = leg + (pts[1:] if i == 0 else list(reversed(pts[:-1])))
        return full, ah["factor"], ah

    # ------------------------------------------------------------------ eveniment
    def _planificata(self, event: dict, m: dict, trace: dict):
        """Linie planificată -> predicție punctată `PLAN-<event_id>` pe străzi (scara din docstring-ul modulului), sau neaplicat."""
        w, data = self.w, event["data"]
        ind = self._indicii_planificata(event, m)
        noduri, gps2, punct = ind["noduri"], ind["gps2"], ind["punct"]
        fer = None if (len(noduri) >= 2 or gps2) else self._fereastra_planificata(event, trace)
        if fer and fer.get("status") == "in_afara_zonei":
            p = fer.get("punct") or {}
            if p:
                return self._eronat(event, trace, m, p["lat"], p["lon"])
            fer = None
        if fer and fer.get("status") != "gasit":
            fer = None
        pasi_loc: list[dict] = []
        pts, metoda, q, sursa, expl, capete, legat = None, "traseu_pe_strazi", 0.0, "coordonate", "", (), None
        factori_loc: dict = {}

        if len(noduri) >= 2:                                        # 1. două noduri cunoscute
            sursa, capete = "id", tuple(noduri[:2])
            b = self.net["noduri"][noduri[1]]
            r = self._ruta_nod(noduri[0], (b["lat"], b["lon"]), sursa)
            pts, metoda, q = r["puncte"], r["metoda"], r["q"]
            pasi_loc.append({"nume": "analiza_harta", "incredere": r["ah"]["acuratete"], "rezultat": {**r["ah"], "vecin": noduri[0], "capat": noduri[1]}})
            expl = f"între nodurile {noduri[0]} și {noduri[1]}"
        elif gps2:                                                  # 2. două puncte GPS
            sursa = "coordonate"
            r = self._ruta_puncte(*gps2)
            pts, metoda, q = r["puncte"], r["metoda"], r["q"]
            pasi_loc.append({"nume": "analiza_harta", "incredere": q, "rezultat": {"metoda": metoda, "traseu": [list(p) for p in pts],
                             "lungime_m": (r["r"] or {}).get("lungime_m"), "explicatie": ["Traseu pe străzi între cele două puncte GPS."
                                                                                        if r["r"] else "Nicio stradă credibilă între puncte: linie dreaptă."]}})
            expl = "între cele două puncte GPS"
        else:
            ancora, sursa_a = None, "coordonate"
            if noduri:
                n = self.net["noduri"][noduri[0]]
                ancora, sursa_a = (n["lat"], n["lon"]), "id"
            elif ind["nod_potrivit"]:
                n = self.net["noduri"][ind["nod_potrivit"]]
                ancora = (n["lat"], n["lon"])
            elif punct and not ind["geocodat"]:
                ancora = punct
            if fer:                                                 # 3/4. segment de stradă
                sursa = sursa_a if ancora is not None else self._sursa_fereastra(fer, (event.get("detalii") or {}).get("geocodare"))
                pts, expl, lung = self._segment_strada(event, fer, ancora)
                q = float(fer["acuratete"]) if ancora is None else float(S.plafon(sursa, w))
                metoda = "traseu_pe_strazi"
                tx = self._text_indiciu(fer.get("indiciu"))
                trace["pasi"].append({"nume": "cautare_strada", "incredere": fer["acuratete"], "rezultat": {
                    "strada": fer["strada"], "de_la_m": fer["de_la_m"], "pana_la_m": fer["pana_la_m"], "punct": fer["punct"],
                    "precizie_m": fer["precizie_m"], "metoda": fer["metoda"],
                    "indiciu": {**(fer.get("indiciu") or {"tip": None}), "text": tx}, "ancore": fer.get("ancore_folosite") or [],
                    "tip_cautat": "linie", "sursa_locatie": sursa, "candidati": [], "ales": None, "linie": fer.get("linie") or [],
                    "segment": [list(p) for p in pts], "lungime_m": round(lung, 1), "motiv": f"{fer['motiv']} Segment: {expl}."}})
                if ancora is None:
                    pts, f_leg, ah = self._leaga_de_stalp(pts, sursa)
                    if ah and f_leg < 1.0:
                        q *= f_leg
                        capete = ()
                        legat = ah["ales"]["de_la"]
                        pasi_loc.append({"nume": "analiza_harta", "incredere": ah["acuratete"], "rezultat": {**ah, "capat": "legatura_la_stalp"}})
                        expl += f"; legat de stâlpul {legat} pe străzi"
            elif punct or ind["nod_potrivit"] or ind["geocodat"]:   # un singur punct, fără stradă: de la cel mai apropiat stâlp
                tinta = punct or ancora
                sursa = ind["sursa_punct"] if punct else "coordonate"
                ah = AH.traseu_pe_strazi(tinta, self.net, w, sursa=sursa)
                if ah["ales"]:
                    pts = [tuple(p) for p in ah["ales"]["traseu"]]
                    metoda = "linie_dreapta" if ah["fara_drum"] else "traseu_pe_strazi"
                    q = ah["factor"] if ind["q_punct"] is None else min(ah["factor"], ind["q_punct"])
                    legat = ah["ales"]["de_la"]
                    pasi_loc.append({"nume": "analiza_harta", "incredere": ah["acuratete"], "rezultat": ah})
                    expl = f"de la stâlpul existent {legat} la punctul din raport"
            elif noduri:
                trace["pasi"].append({"nume": "predictie", "incredere": None, "rezultat": None})
                return self._scor_pas(trace, "neaplicat", {"nivel": None},
                                      [f"Linie planificată cu un singur nod ({noduri[0]}), fără a doua poziție și fără stradă: nu are direcție."])
        if not pts or len(pts) < 2:
            trace["pasi"].append({"nume": "predictie", "incredere": None, "rezultat": None})
            return self._scor_pas(trace, "neaplicat", {"nivel": None},
                                  ["Linie planificată fără niciun indiciu de loc (noduri, coordonate, stradă): nu are geometrie."])
        for p in (pts[0], pts[-1]):
            z = zona_ok(p[0], p[1], self.net, w)
            if not z["ok"]:
                return self._eronat(event, trace, m, p[0], p[1])
        trace["pasi"].extend(pasi_loc)

        trace["pasi"].append({"nume": "predictie", "incredere": None, "rezultat": None})
        sp, factori = S.scor_propunere(event, max(0.0, min(1.0, q)), w)
        sp = min(sp, round(S.plafon(sursa, w), 3))
        sid = f"PLAN-{event['event_id']}"
        lung_tot = round(sum(dist_m(a, b) for a, b in zip(pts, pts[1:])), 1)
        self.predictii[sid] = {"puncte": pts, "metoda": metoda, "capete": capete, "sursa_locatie": sursa,
                               "geometrie": {"type": "LineString", "coordinates": [[o, la] for la, o in pts]}}
        txt = (f"Linie planificată {expl}, {lung_tot:g} m pe {'străzi' if metoda == 'traseu_pe_strazi' else 'linie dreaptă (nicio stradă credibilă)'}, "
               f"scor {sp} (locație: {sursa}). Ce e doar planificat nu se aplică în model până nu e executat, indiferent de scor.")
        st = self._pune(sid, "tronson", data, nivel="predictie", scor=sp, ultima_verificare=None, sursa_locatie=sursa, t0=False,
                        motive=[{"text": txt, "efect": 0.0, "eveniment": event["event_id"], "data": data}],
                        predictie={"metoda": metoda, "urmeaza_strada": round(q, 3) if metoda == "traseu_pe_strazi" else None,
                                   "propunere": {"proprietate": "linie_planificata", "valoare": sid},
                                   "scor_propunere": sp, "lungime_m": lung_tot, "traseu": [list(p) for p in pts],
                                   **({"legat_de": legat} if legat else {})})
        trace["modificari"].append(self._publica(sid, st))
        self._scor_pas(trace, "predictie", {"scor_propunere": sp, "factori": factori, "nivel": st["nivel"], "sursa_locatie": sursa,
                                            "lungime_m": lung_tot}, [txt], sp)
