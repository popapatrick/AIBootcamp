"""Reguli noi ale motorului pentru sesiunea 2 (date FICTIVE), ca mixin pentru `GridModel`.

- `mutare_fire`: firele dintr-o zonă au fost mutate (sens giratoriu etc.): elementele din rază trec „de verificat",
  se propune punctat un traseu nou pe străzi.
- `activ_demontat`: element scos din uz, doar cu rapoarte de la cel puțin două echipe și scor peste prag.
- `cerere_racordare`: lanț de stâlpi prezis spre o casă nouă (modulul `backend.racordare`, scris de A).
- locația din traseul tabletei (`backend.trace`, scris de A) când raportul nu are ID sau coordonate.
- val de apeluri: mai multe apeluri pe același element în aceeași fereastră cântăresc mai mult decât unul.
- căutare pe stradă (sesiunea 4, V6): o adresă fără ID/coordonate (stradă + număr/indiciu/doar stradă) dă o fereastră pe stradă
  (`backend.geo.fereastra_strada`); motorul caută elementele din ea (1 = potrivit, 2..N = predicție „probabil acest element”,
  peste N = de verificat, 0 = element nou sau pin „de verificat”), cu pasul `cautare_strada` în StepTrace și ancore pentru
  rapoartele următoare.

Toate pragurile vin din `contracts/weights.yaml`. Contracte: `contracts/interfaces.md`.
"""
from __future__ import annotations

import math
import re

from backend.engine import scoring as S
from backend.engine.network import dist_m
from backend.engine.zona import zona_ok


# tipurile de eveniment care caută pe stradă; cele de mai jos creează element nou când fereastra nu are niciun candidat
TIPURI_CAUTARE = ("avarie_semnalata", "activ_inlocuit", "verificare", "activ_demontat", "nod_lipsa", "racord_nou")
TIPURI_NOI = ("nod_lipsa", "racord_nou")
_CABLU = re.compile(r"\b(tronson\w*|cablu\w*|cabluri\w*|conductor\w*|linia|linie)\b", re.I)
_STALP = re.compile(r"\b(st[aâ]lp\w*|nod\w*|post\w*)\b", re.I)
_CU_NUMAR = ("numar", "langa", "vizavi", "intre", "dupa", "inainte")


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
    # ------------------------------------------------------------ acuratețe (sesiunea 4)
    @staticmethod
    def _e_gis(st: dict) -> bool:
        """Element din rețeaua GIS (fără plafon de locație) sau verificat de om."""
        return S.regim_stare(st) in ("gis", "verificat_om")

    def _eff(self, st: dict, data: str) -> float:
        """Scorul efectiv al stării `st` la `data`, cu regimul ei de scădere (gis | verificat_om | normal)."""
        return S.scor_la_data(st["scor"], st["valid_de_la"], data, self.w, S.regim_stare(st))

    def _plafoneaza(self, st: dict, scor: float, eff: float | None = None) -> float:
        """Plafonul sursei de locație al elementului din raport (GIS și verificat de om: fără plafon).
        Un scor deja peste plafon (`eff`) nu e coborât de plafon."""
        if self._e_gis(st) or not st.get("sursa_locatie"):
            return scor
        return min(scor, max(S.plafon(st["sursa_locatie"], self.w), eff if eff is not None else 0.0))

    @staticmethod
    def _sursa_din_geocodare(geo: dict) -> str:
        """Sursa locației dintr-un rezultat de geocodare: intersectie | adresa_numar | strada | reper
        (din `tip` dacă există, altfel din textul `motiv` al geocodării)."""
        tip = geo.get("tip") or geo.get("loc")
        if tip in ("intersectie", "strada", "reper"):
            return tip
        if tip in ("strada_numar", "adresa_numar"):
            return "adresa_numar"
        mt = (geo.get("motiv") or "").lower()
        if mt.startswith("intersec"):
            return "intersectie"
        if "nr." in mt and "interpolat" in mt:
            return "adresa_numar"
        if mt.startswith("reper"):
            return "reper"
        return "strada"

    def _sursa_eveniment(self, event: dict, pozitie_dedusa: bool = False) -> str:
        """Cum a fost localizat elementul creat de raport: id | coordonate | intersectie | adresa_numar | strada | reper |
        analiza_harta (poziție dedusă din vecini)."""
        ref, det = event.get("referinta") or {}, event.get("detalii") or {}
        if (ref.get("element_id") or "").strip():
            return "id"
        geo, c = det.get("geocodare"), ref.get("coordonate")
        if geo and c and (geo.get("lat"), geo.get("lon")) == (c.get("lat"), c.get("lon")):
            return self._sursa_din_geocodare(geo)
        if c or det.get("locatie"):
            return "coordonate"
        return "analiza_harta" if pozitie_dedusa else "coordonate"

    def _executat_teren(self, event: dict) -> bool:
        """Raport executat al unei echipe din teren: aplică de la `acuratete.aplicat_raport_executat` (P1).
        Racordări doar pentru racord_nou; cererile de racordare rămân predicții."""
        if event.get("status") != "executat":
            return False
        e = event.get("echipa_sursa")
        return e in ("mentenanta", "investitii") or (e == "racordari" and event.get("tip") == "racord_nou")

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

    @staticmethod
    def _localizator(ref: dict) -> str | None:
        """Cel mai bun localizator din text: id | coordonate | strada_numar | strada | reper | None."""
        if (ref.get("element_id") or "").strip():
            return "id"
        if ref.get("coordonate"):
            return "coordonate"
        ad = ref.get("adresa_structurata") or {}
        if ad.get("strada") and ad.get("numar"):
            return "strada_numar"
        if ad.get("strada"):
            return "strada"
        if ad.get("reper") or ref.get("adresa"):
            return "strada_numar" if re.search(r"\b(nr\.?|numarul|nr)\s*\d+", ref.get("adresa") or "", re.I) else "strada"
        return None

    def _plafon_standardizare(self, event: dict, trace: dict) -> dict:
        """Încrederea extracției nu depășește plafonul localizatorului cel mai bun din text (weights.standardizare)."""
        pl = (self.w.get("standardizare") or {}).get("plafon_dupa_localizator") or {}
        loc = self._localizator(event.get("referinta") or {})
        inc = float(event.get("incredere_extractie", 1.0))
        if loc in pl and inc > pl[loc]:
            trace["pasi"][0]["incredere"] = pl[loc]
            trace["pasi"][0]["rezultat"]["plafon_standardizare"] = {"localizator": loc, "plafon": pl[loc], "initial": inc}
            return {**event, "incredere_extractie": pl[loc]}
        return event

    def _foloseste_geocodare(self, event: dict, trace: dict) -> dict:
        """Fără ID și fără coordonate, dar cu adresă: backend.geo dă coordonate aproximative (doar cache OSM + AI)."""
        ref, det0 = event.get("referinta") or {}, event.get("detalii") or {}
        if (ref.get("element_id") or "").strip() or ref.get("coordonate") or not (ref.get("adresa") or ref.get("adresa_structurata")):
            return event
        if det0.get("locatie") or det0.get("locatie_operator") or det0.get("trace"):
            return event        # clic pe hartă, poziția operatorului sau trace au deja o locație (mai precisă decât adresa)
        try:
            from backend.engine import osm
            from backend.geo import geocodeaza
            g = geocodeaza(ref, osm.strazi(), self.w, self.net, self.ancore)
        except Exception as e:      # fără cache OSM sau modul: ca înainte, nepotrivit
            trace["pasi"].append({"nume": "geocodare", "incredere": 0.0, "rezultat": {"status": "necunoscut", "motiv": f"geocodare indisponibilă: {e}"}})
            return event
        trace["pasi"].append({"nume": "geocodare", "incredere": g.get("acuratete"), "rezultat": g})
        if g.get("status") != "gasit":
            return event
        z = zona_ok(g["lat"], g["lon"], self.net, self.w)
        if not z["ok"]:
            g["status"] = "in_afara_zonei"
            return {**event, "_eronat": (g["lat"], g["lon"])}
        fer = g.get("fereastra") or None
        if fer and fer.get("status") == "in_afara_zonei" and fer.get("punct"):
            return {**event, "_eronat": (fer["punct"]["lat"], fer["punct"]["lon"])}
        det = event.get("detalii") or {}
        geo = {k: g.get(k) for k in ("lat", "lon", "precizie_m", "metoda", "acuratete", "motiv", "tip") if g.get(k) is not None}
        if fer and fer.get("status") == "gasit":
            geo["tip"] = self._sursa_fereastra(fer, g)     # sursa locației (adresa_numar | strada | intersectie | reper) pentru plafon
        out = {**event, "referinta": {**ref, "coordonate": {"lat": g["lat"], "lon": g["lon"]}},
               "detalii": {**det, "geocodare": geo}}
        if fer and fer.get("status") == "gasit":
            out["_fereastra"] = fer      # cheie internă: căutarea pe stradă (apply_event), nu iese din motor
        return out

    # ------------------------------------------------------------ căutare pe stradă (V6, D11)
    @staticmethod
    def _sursa_fereastra(fer: dict, geo: dict | None = None) -> str:
        """Sursa locației dintr-o fereastră pe stradă: intersectie (colț) | adresa_numar (indiciu cu număr) | reper | strada."""
        ind = fer.get("indiciu") or {}
        tip = ind.get("tip")
        if tip == "colt":
            return "intersectie"
        if tip in _CU_NUMAR and ind.get("numar"):
            return "adresa_numar"
        if ((geo or {}).get("motiv") or "").lower().startswith("reper"):
            return "reper"
        return "strada"

    @staticmethod
    def _text_indiciu(ind: dict | None) -> str:
        """Textul scurt, în română, al indiciului de loc (pentru UI și jurnal)."""
        if not ind or not ind.get("tip"):
            return "doar strada"
        t, n, n2 = ind["tip"], ind.get("numar"), ind.get("numar_2")
        return {"numar": f"nr. {n}", "langa": f"lângă nr. {n}", "vizavi": f"vizavi de nr. {n}",
                "intre": f"între nr. {n} și {n2 or n}", "dupa": f"după nr. {n}", "inainte": f"înainte de nr. {n}",
                "capat": "la capătul străzii", "inceput": "la începutul străzii",
                "colt": f"colț cu {ind.get('strada_2') or 'altă stradă'}",
                "element": f"lângă stâlpul {ind.get('element_id')}",
                "parte": f"partea cu numere {ind.get('paritate') or ''}".strip()}.get(t, "doar strada")

    def _tip_cautat(self, event: dict) -> str:
        """`tronson` dacă evenimentul vizează un cablu/tronson (secțiune dată sau text despre cablu fără stâlp), altfel `nod`."""
        if event["tip"] in TIPURI_NOI:
            return "nod"
        det, text = event.get("detalii") or {}, event.get("text_original") or ""
        if det.get("sectiune_noua") or det.get("sectiune_observata"):
            return "tronson"
        return "tronson" if _CABLU.search(text) and not _STALP.search(text) else "nod"

    def _candidati_fereastra(self, fer: dict, tip_el: str, punct: tuple[float, float]) -> list[dict]:
        """Elementele existente (nod sau tronson, fără retrase) din fereastra de pe stradă, ordonate după distanța la `punct`:
        [{element_id, distanta_m, pozitie_m}]. Un element e în fereastră dacă se află la cel mult `latime_laterala_m` de porțiunea
        de stradă dintre `de_la_m` și `pana_la_m` (`fer["linie"]`); capetele ferestrei se extind deci cu cel mult atât. Tronsoanele: orice punct."""
        from backend.engine.match import _dist_la_punct
        from backend.geo.fereastra import Cale
        lat_max = float(self.w["cautare_strada"]["latime_laterala_m"])
        linie = fer.get("linie") or []
        if len(linie) < 2:
            return []
        cale, de_la = Cale(linie), float(fer["de_la_m"])
        marj = lat_max / 111_320 * 1.2
        la0, la1 = min(p[0] for p in linie) - marj, max(p[0] for p in linie) + marj
        lo0, lo1 = min(p[1] for p in linie) - marj * 2, max(p[1] for p in linie) + marj * 2
        out = []
        for eid, el in (self.net["tronsoane"] if tip_el == "tronson" else self.net["noduri"]).items():
            if eid.endswith("-casa") or (self.istoric.get(eid) or [{}])[-1].get("retras"):
                continue
            if tip_el == "nod":
                pcte = [(el["lat"], el["lon"])]
            else:
                pcte = []
                for a, b in zip(el["puncte"], el["puncte"][1:]):
                    n = max(1, int(dist_m(a, b) // 5))
                    pcte += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
            if not any(la0 <= p[0] <= la1 and lo0 <= p[1] <= lo1 for p in pcte):
                continue
            best = None
            for p in pcte:
                s_, d_ = cale.proiecteaza(p)
                if d_ <= lat_max and (best is None or d_ < best[1]):
                    best = (s_, d_)
            if best:
                out.append({"element_id": eid, "distanta_m": round(_dist_la_punct(punct, el), 1), "pozitie_m": round(de_la + best[0], 1)})
        return sorted(out, key=lambda c: (c["distanta_m"], c["element_id"]))

    def _cautare_strada(self, event: dict, m: dict, trace: dict) -> tuple[dict, dict]:
        """Caută pe stradă elementul din raport: fereastra (`event["_fereastra"]`) -> candidați -> potrivire.

        Adaugă pasul `cautare_strada` în `trace["pasi"]` (înaintea `potrivire`) și întoarce `(m_nou, cs)`:
        - tipuri noi (nod_lipsa, racord_nou): mereu element nou la `fereastra.punct`; candidații rămân informativ (`ales` null);
        - 1 candidat: `m` potrivit (metoda `cautare_strada`, calitatea `calitate_cautare_unic`), `cs["actiune"]` None: raportul se aplică pe el;
        - 2..`max_candidati_predictie`: `cs["actiune"]` = `predictie` (elementul cel mai apropiat primește „probabil acest element”);
        - mai mulți: `cs["actiune"]` = `de_verificat` (pe fereastră, niciun element atins);
        - niciunul (tipuri existente): `cs["actiune"]` = `pin`."""
        fer, c = event["_fereastra"], self.w["cautare_strada"]
        punct = (fer["punct"]["lat"], fer["punct"]["lon"])
        tip_el = self._tip_cautat(event)
        cands = self._candidati_fereastra(fer, tip_el, punct)
        ind = fer.get("indiciu")
        text = self._text_indiciu(ind)
        n = len(cands)
        sursa = self._sursa_fereastra(fer, (event.get("detalii") or {}).get("geocodare"))
        ales, actiune = None, None
        if event["tip"] in TIPURI_NOI:
            # decizia lui Victor (15 nov.): element NOU/lipsă => mereu element nou la `fereastra.punct`, indiferent câți stâlpi există în
            # fereastră; ei rămân doar informativ (`candidati`, `ales` null; alternative/motiv pe elementul nou)
            motiv_rez = (f"Element nou la punctul estimat ({text}); niciun element existent din fereastră nu se potrivește"
                         + (f", dar {n} stâlp{'i' if n > 1 else ''} din fereastră ar putea fi același (informativ): "
                            + ", ".join(x["element_id"] for x in cands[:5]) + (" ..." if n > 5 else "") + "." if n else "."))
        elif n == 1:
            ales = cands[0]["element_id"]
            motiv_rez = f"Un singur {'stâlp' if tip_el == 'nod' else 'tronson'} în fereastră ({text}): {ales}."
        elif 2 <= n <= int(c["max_candidati_predictie"]):
            ales, actiune = cands[0]["element_id"], "predictie"
            motiv_rez = f"{n} candidați în fereastră ({text}): cel mai apropiat de punctul estimat e {ales}; propunere, neaplicată."
        elif n > int(c["max_candidati_predictie"]):
            actiune = "de_verificat"
            motiv_rez = f"{n} candidați în fereastră ({text}), peste {c['max_candidati_predictie']}: de verificat pe fereastră."
        else:
            actiune = "pin"
            motiv_rez = (f"Nu există {'stâlp' if tip_el == 'nod' else 'tronson'} în fereastra de pe {fer['strada']} ({text}): "
                         "pin de verificat la punctul estimat.")
        rez = {"strada": fer["strada"], "de_la_m": fer["de_la_m"], "pana_la_m": fer["pana_la_m"], "punct": fer["punct"],
               "precizie_m": fer["precizie_m"], "metoda": fer["metoda"],
               "indiciu": {**(ind or {"tip": None, "numar": None, "numar_2": None, "strada_2": None, "element_id": None,
                                     "distanta_stalpi": None, "paritate": None}), "text": text},
               "ancore": fer.get("ancore_folosite") or [], "tip_cautat": tip_el, "sursa_locatie": sursa,
               "candidati": cands, "ales": ales, "linie": fer.get("linie") or [],
               "motiv": f"{fer['motiv']} {motiv_rez}"}
        trace["pasi"].append({"nume": "cautare_strada", "incredere": fer["acuratete"], "rezultat": rez})
        det_cs = {k: rez[k] for k in ("strada", "de_la_m", "pana_la_m", "punct", "precizie_m", "metoda", "candidati", "ales")}
        top3 = [{"element_id": x["element_id"], "distanta_m": x["distanta_m"]} for x in cands[:3]]
        base = {"element_id": None, "metoda": "cautare_strada", "calitate": 0.0, "candidati": top3,
                "coordonate_folosite": {"lat": punct[0], "lon": punct[1]}, "semnale": list(m["semnale"]) + ["cautare_strada"]}
        if n == 1 and event["tip"] not in TIPURI_NOI:
            m2 = {**base, "status": "potrivit", "element_id": ales, "calitate": round(float(c["calitate_cautare_unic"]), 3),
                  "motiv": rez["motiv"]}
        elif actiune in ("predictie", "de_verificat"):
            m2 = {**base, "status": "ambiguu", "motiv": rez["motiv"]}
        else:
            m2 = {**base, "status": "absent_din_model", "motiv": rez["motiv"]}
        return m2, {"detalii": det_cs, "actiune": actiune, "fer": fer, "rez": rez, "cands": cands, "tip_el": tip_el, "sursa": sursa, "text": text}

    def _rezultat_cautare(self, event: dict, m: dict, cs: dict, trace: dict):
        """Ce se întâmplă când căutarea pe stradă nu dă un element unic: predicție, de verificat pe fereastră sau pin."""
        w, data, c = self.w, event["data"], self.w["cautare_strada"]
        fer, cands, text, sursa = cs["fer"], cs["cands"], cs["text"], cs["sursa"]
        trace["pasi"].append({"nume": "predictie", "rezultat": None, "incredere": None})
        if cs["actiune"] == "de_verificat":
            t = (f"{len(cands)} elemente în fereastra de pe {fer['strada']} ({text}, {fer['de_la_m']:g}–{fer['pana_la_m']:g} m), "
                 f"peste {c['max_candidati_predictie']}: nu alegem unul. De verificat în teren; nimic aplicat.")
            return self._scor_pas(trace, "de_verificat", {"nivel": None, "fereastra": {k: fer[k] for k in ("strada", "de_la_m", "pana_la_m")},
                                                          "candidati": len(cands)}, [t])
        if cs["actiune"] == "pin":
            pid = f"VER-{event['event_id']}"
            pt = (fer["punct"]["lat"], fer["punct"]["lon"])
            scor = round(S.plafon(sursa, w) * 0.5, 3)
            t = (f"Nu există {'stâlp' if cs['tip_el'] == 'nod' else 'tronson'} în fereastra de pe {fer['strada']} ({text}): "
                 f"pin de verificat la punctul estimat, scor {S.fmt(scor)} (jumătate din plafonul sursei {sursa}). Nimic existent nu e atins.")
            self.pinuri[pid] = {"geometrie": {"type": "Point", "coordinates": [pt[1], pt[0]]}}
            st = self._pune(pid, "nod", data, nivel="de_verificat", scor=scor, ultima_verificare=None, origine="generat_model", t0=False,
                            sursa_locatie=sursa, verificat_om=False, verificat_om_data=None, predictie=None,
                            motive=[{"text": t, "efect": 0.0, "eveniment": event["event_id"], "data": data}])
            trace["modificari"].append(self._publica(pid, st))
            return self._scor_pas(trace, "de_verificat", {"scor_nou": scor, "nivel": "de_verificat", "pin": pid}, [t])
        # predicție: 2..max candidați; cel mai apropiat de punct e ales, ponderile ∝ 1/(d+10)
        sp, factori = S.scor_propunere(event, fer["acuratete"], w)
        sp = min(sp, round(S.plafon(sursa, w), 3))
        if sp < w["praguri"]["predictie"]:
            t = (f"{len(cands)} candidați în fereastra de pe {fer['strada']} ({text}), dar scorul propunerii {sp} e sub "
                 f"{w['praguri']['predictie']}: doar de verificat; nimic aplicat.")
            return self._scor_pas(trace, "de_verificat", {"nivel": None, "scor_propunere": sp, "candidati": len(cands)}, [t], sp)
        pond = [1.0 / (x["distanta_m"] + 10.0) for x in cands]
        tot = sum(pond)
        pond = [round(p / tot, 3) for p in pond]
        ales = cands[0]["element_id"]
        alt = [{"element_id": x["element_id"], "distanta_m": x["distanta_m"], "pondere": p, "scor_propunere": round(sp * p, 3),
                "motiv": f"la {x['distanta_m']:g} m de punctul estimat; pondere {p:g}"} for x, p in zip(cands[1:], pond[1:])]
        cur = self._curent(ales)
        eff = self._eff(cur, data)
        sp_ales = round(sp * pond[0], 3)
        t = (f"Probabil acest element: {ales}, la {cands[0]['distanta_m']:g} m de punctul estimat pe {fer['strada']} ({text}); "
             f"{len(cands)} candidați în fereastră, pondere {pond[0]:g} din propunerea {sp} (scor propunere {sp_ales}). "
             "Raportul nu se aplică direct; starea elementului rămâne neschimbată.")
        marker = {"metoda": "cautare_strada", "urmeaza_strada": None, "propunere": {"proprietate": "element_probabil", "valoare": ales},
                  "scor_propunere": sp_ales, "pondere": pond[0], "alternative": alt, "strada": fer["strada"], "indiciu": text}
        st = self._pune(ales, cur["tip_element"], data, nivel=cur["nivel"], scor=eff, predictie=marker,
                        motive=self._motiv(ales, t, 0.0, event))
        trace["modificari"].append(self._publica(ales, st))
        trace.setdefault("_ce", {})[ales] = "predictie"
        trace["pasi"][-1] = {"nume": "predictie", "incredere": sp_ales, "rezultat": {
            "metoda": "cautare_strada", "element_ales": ales, "alternative": alt, "scor_propunere": sp_ales}}
        self._scor_pas(trace, "predictie", {"scor_propunere": sp_ales, "factori": factori, "nivel": "predictie", "element": ales}, [t], sp_ales)

    @staticmethod
    def _fara_marker(cur: dict) -> dict:
        """Argument pentru `_pune`: șterge marcajul „probabil acest element” (cautare_strada) când un raport sigur atinge elementul."""
        return {"predictie": None} if (cur.get("predictie") or {}).get("metoda") == "cautare_strada" else {}

    def _inregistreaza_ancora(self, event: dict, m: dict, cs: dict | None):
        """Adresă + număr la o locație sigură => ancoră pentru rapoartele următoare (`self.ancore`): potrivit cu ID, coordonate
        explicite în același raport, sau 1 candidat unic în fereastră (doar indiciul `numar`)."""
        ref, det = event.get("referinta") or {}, event.get("detalii") or {}
        ad = ref.get("adresa_structurata") or {}
        strada, nr = (ad.get("strada") or "").strip(), str(ad.get("numar") or "").strip()
        if not strada or not nr.isdigit():
            return
        loc = None
        if m.get("status") == "potrivit" and m.get("metoda") == "id":
            el = self.net["noduri"].get(m.get("element_id"))
            loc = (el["lat"], el["lon"]) if el else None
        elif ref.get("coordonate") and not det.get("geocodare") and not det.get("trace_rezumat") and m.get("metoda") == "coordonate":
            loc = (ref["coordonate"]["lat"], ref["coordonate"]["lon"])
        elif cs and cs["actiune"] is None and event["tip"] not in TIPURI_NOI and len(cs["cands"]) == 1 and (cs["fer"].get("indiciu") or {}).get("tip") == "numar":
            el = self.net["noduri"].get(cs["cands"][0]["element_id"])
            loc = (el["lat"], el["lon"]) if el else None
            strada = cs["fer"]["strada"]
        if not loc or any(a["numar"] == int(nr) and a["strada"].lower() == strada.lower() for a in self.ancore):
            return
        self.ancore.append({"strada": strada, "numar": int(nr), "lat": round(loc[0], 6), "lon": round(loc[1], 6)})

    def _trace_generat(self, event: dict, trace: dict) -> dict:
        """Traseu simulat al tabletei lângă punctul din raport (feature traseu-generat-din-raport).

        Doar pentru rapoarte de echipă (nu apel/om) cu locație (coordonate sau adresă geocodată), fără ID și fără trace real.
        Complementar: nu schimbă locația, doar acuratețea ei (`detalii.trace_factor`): oprire lungă, zgomot mic, acoperire bună și
        oprire consistentă cu adresa o cresc (plafon `bonus_max`); zgomot/acoperire slabă sau contradicție o scad.
        Dezactivare per raport: `detalii.trace_params = {"dezactivat": true}`.
        """
        ref, det = event.get("referinta") or {}, event.get("detalii") or {}
        pt = ref.get("coordonate")
        w = self.w
        cfg = w.get("trace_generat")
        par = det.get("trace_params") or {}
        if (not cfg or par.get("dezactivat") or det.get("trace") or (ref.get("element_id") or "").strip() or not pt
                or event["echipa_sursa"] not in S.ECHIPE_TEREN or event["tip"] in ("mutare_fire", "cerere_racordare", "activ_demontat", "verificare")):
            return event
        try:
            from backend.engine import osm
            from backend.trace import localizeaza
            from backend.trace.genereaza import genereaza_traseu
            params = {**cfg, **{k: v for k, v in par.items() if k != "dezactivat"}}
            punct = {"lat": pt["lat"], "lon": pt["lon"], "t": f"{event['data']}T14:00:00"}
            strazi = osm.strazi()
            tr = genereaza_traseu(punct, strazi, params, event["event_id"])
            rez = localizeaza(tr, ref.get("adresa"), self.net, strazi, w)
        except Exception as e:
            trace["pasi"].append({"nume": "trace", "incredere": 0.0, "rezultat": {"sursa": "simulat", "status": "indisponibil", "motiv": str(e)}})
            return event
        a = rez.get("alegere")
        bonus = pen = 0.0
        motive = []
        if a:
            dur = a["durata_min"]
            dmin = w["trace"]["durata_min_min"]
            b_dur = max(0.0, min(1.0, (dur - dmin) / max(1e-9, cfg["durata_bonus_min"])))
            b_zg = max(0.0, 1 - params["zgomot_m"] / max(1e-9, cfg["zgomot_max_bonus_m"]))
            bonus = cfg["bonus_max"] * b_dur * b_zg
            d = dist_m((pt["lat"], pt["lon"]), (a["lat"], a["lon"]))
            if d > cfg["toleranta_adresa_m"]:
                pen += cfg["penalizare_contradictie"]
                motive.append(f"oprirea e la {d:.0f} m de locația din raport (peste {cfg['toleranta_adresa_m']} m): contradicție")
            motive.append(f"oprire {dur:.0f} min, zgomot {params['zgomot_m']:g} m: bonus {bonus:.3f}")
        else:
            pen += cfg["penalizare_contradictie"]
            motive.append("nicio oprire detectată în traseu")
        if params["acoperire"] < cfg["acoperire_min"]:
            pen += cfg["penalizare_acoperire"]
            motive.append(f"acoperire {params['acoperire']:g} sub {cfg['acoperire_min']}")
        factor = round(max(0.3, 1 + bonus - pen), 3)
        trace["pasi"].append({"nume": "trace", "incredere": factor, "rezultat": {
            "sursa": "simulat", "status": rez.get("status"), "alegere": a, "opriri": rez.get("opriri"), "puncte": len(tr),
            "params": params, "factor_trace": factor, "motiv": "; ".join(motive)}})
        return {**event, "detalii": {**det, "trace_sursa": "simulat", "trace_factor": factor, "trace_params": params}}

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
            eff = self._eff(cur, data)
            delta = w["scor"]["confirmare_teren"] * f * w["potrivire"]["calitate_dupa_coordonate"]
            nivel = "in_model" if (cur["nivel"] == "de_verificat" and eff + delta >= w["praguri"]["predictie"]) else cur["nivel"]
            st = self._pune(eid, cur["tip_element"], data, nivel=nivel, scor=self._plafoneaza(cur, S.clamp(eff + delta, w), eff), ultima_verificare=data,
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
        if not zona_ok(c["lat"], c["lon"], self.net, w)["ok"]:
            return self._eronat(event, trace, None, c["lat"], c["lon"])
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
            eff = self._eff(cur, data)
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
            sp = min(sp, round(S.plafon("analiza_harta", w), 3))     # traseul propus vine din analiza hărții
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
                            sursa_locatie="analiza_harta", t0=False,
                            motive=[{"text": txt + " " + S.text_plafon("analiza_harta", w), "efect": 0.0, "eveniment": event["event_id"], "data": data}],
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
        eff = self._eff(cur, data)
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
        st = self._pune(eid, el["tip_element"], data, nivel=nivel, scor=scor, motive=self._motiv(eid, t, delta, event), **self._fara_marker(cur))
        trace["modificari"].append(self._publica(eid, st))
        self._scor_pas(trace, "scor_actualizat", {"scor_nou": scor, "nivel": nivel, "efect": "semnal_demontare"}, [t])

    # ------------------------------------------------------------ cerere de racordare
    def _cerere_racordare(self, event: dict, m: dict, trace: dict):
        w, data = self.w, event["data"]
        cfg = w["racordare"]
        det, ref = event.get("detalii") or {}, event.get("referinta") or {}
        op = det.get("locatie_operator")
        # sursa locației: coordonate din text > clic pe hartă > poziția simulată a operatorului (doar dacă lipsesc celelalte)
        if ref.get("coordonate"):
            geo = det.get("geocodare")
            sursa_loc = ("clic" if ref["coordonate"] == det.get("locatie") else
                         "adresa" if geo and (geo.get("lat"), geo.get("lon")) == (ref["coordonate"]["lat"], ref["coordonate"]["lon"]) else "text")
            loc = ref["coordonate"]
        elif det.get("locatie"):
            loc, sursa_loc = det["locatie"], "clic"
        elif op and op.get("lat") is not None and op.get("lon") is not None:
            loc, sursa_loc = op, "operator_simulat"
        else:
            loc, sursa_loc = None, None
        for p in trace["pasi"]:     # pasul potrivire arată și sursa locației (nu doar predicția)
            if p["nume"] == "potrivire" and sursa_loc:
                p["rezultat"] = {**p["rezultat"], "sursa_locatie": sursa_loc}
        trace["pasi"].append({"nume": "predictie", "rezultat": None, "incredere": None})
        if loc and not zona_ok(loc["lat"], loc["lon"], self.net, w)["ok"]:
            return self._eronat(event, trace, None, loc["lat"], loc["lon"])
        if not loc:
            return self._scor_pas(trace, "neaplicat", {"nivel": None},
                                  ["Cerere de racordare fără locația casei (coordonate, clic pe hartă sau poziția operatorului): nu putem prezice lanțul."])
        try:
            from backend.engine import osm
            from backend.racordare import prezice_lant
        except ImportError:
            return self._scor_pas(trace, "neaplicat", {"nivel": None}, ["Modulul backend.racordare lipsește."])
        r = prezice_lant({"lat": loc["lat"], "lon": loc["lon"]}, self.net, osm.strazi(), w)
        trace["pasi"][-1] = {"nume": "predictie", "incredere": r.get("urmeaza_strada"),
                             "rezultat": {"metoda": "lant_racordare", "sursa_locatie": sursa_loc, **{k: r.get(k) for k in
                                          ("status", "nod_start", "distanta_m", "urmeaza_strada", "ambiguu", "motiv")},
                                          "stalpi": len(r.get("stalpi") or [])}}
        # safeguard: stâlpii prezicși care ar ieși din zona prototipului se taie (lanțul se oprește la primul din afară)
        taiat = False
        for i_, st_ in enumerate(r.get("stalpi") or []):
            if not zona_ok(st_["lat"], st_["lon"], self.net, w)["ok"]:
                r = {**r, "stalpi": r["stalpi"][:i_], "cabluri": r["cabluri"][:i_]}
                taiat = True
                break
        treapta = int(r.get("treapta") or (4 if r["status"] == "fara_nod" or not r.get("nod_start") else 1))
        trace["pasi"][-1]["rezultat"]["treapta"] = treapta
        ev = event["event_id"]
        nume = {f"stalp-{s['ordine']}": f"NOU-{ev}-S{s['ordine']}" for s in r["stalpi"]}
        nume["casa"] = f"NOU-{ev}-casa"
        # sursa locației casei (coordonate/clic -> coordonate, adresă -> tipul geocodării, operator simulat -> strada);
        # stâlpii și cablurile prezise vin din analiza hărții
        sursa_casa = ("coordonate" if sursa_loc in ("clic", "text") else
                      self._sursa_din_geocodare(det["geocodare"]) if sursa_loc == "adresa" else "strada")
        specs = []
        for s in r["stalpi"]:
            specs.append((nume[f"stalp-{s['ordine']}"], "nod", {"punct": (s["lat"], s["lon"]), "sursa_locatie": "analiza_harta",
                          "geometrie": {"type": "Point", "coordinates": [s["lon"], s["lat"]]}}))
        specs.append((nume["casa"], "nod", {"punct": (loc["lat"], loc["lon"]), "sursa_locatie": sursa_casa,
                      "geometrie": {"type": "Point", "coordinates": [loc["lon"], loc["lat"]]}}))
        urm = r.get("urmeaza_strada")
        for k, cab in enumerate(r["cabluri"]):
            a, b = (nume.get(cab["de_la"], cab["de_la"]), nume.get(cab["la"], cab["la"]))
            pts = [tuple(p) for p in cab["puncte"]]
            specs.append((f"NOU-{ev}-L{k + 1}", "tronson", {
                "puncte": pts, "metoda": "traseu_strada_osm" if urm is not None else "linie_dreapta", "capete": (a, b),
                "sursa_locatie": "analiza_harta",
                "urmeaza": urm, "geometrie": {"type": "LineString", "coordinates": [[o, la] for la, o in pts]}}))
        q = w["potrivire"]["calitate_dupa_coordonate"] * (0.8 if r.get("ambiguu") else 1.0)
        if sursa_loc == "adresa":
            q = min(q, det["geocodare"]["acuratete"])       # locația casei vine din adresă: acuratețea geocodării
        sp, factori = S.scor_propunere(event, q, w, urm)
        if urm is None and treapta <= 2:
            sp = round(sp * cfg["factor_fara_strada"], 3)
        sp = round(sp * {1: 1.0, 2: cfg["factor_raza_extinsa"], 3: cfg["factor_linie_dreapta_lunga"], 4: cfg["factor_doar_casa"]}[treapta], 3)
        if sursa_loc == "operator_simulat":
            sp = round(sp * cfg["factor_locatie_operator"], 3)
        cap_casa = S.plafon(sursa_casa, w)
        plafonat = sp > cap_casa
        if plafonat:
            sp = round(cap_casa, 3)         # decizia se ia pe scorul plafonat după sursa locației casei
        niv = S.decizie(sp, w, planificat=event["status"] == "planificat" or sursa_loc == "operator_simulat")
        txt = (f"Cerere de racordare: lanț de {len(r['stalpi'])} stâlp(i) de la nodul {r['nod_start']} ({r['distanta_m']} m) spre casă, "
               f"scor {sp} (fiabilitate {factori['fiabilitate_sursa']}, extracție {factori['incredere_extractie']}, "
               f"potrivire {factori['calitate_potrivire']}" + (f", urmează strada {urm}" if urm is not None else ", fără stradă") + ").")
        if sursa_loc == "operator_simulat":
            prec = op.get("precizie_m")
            txt += (f" Locația e din poziția SIMULATĂ a operatorului" + (f", ±{prec:g} m" if prec is not None else "") +
                    f" (nu GPS real, nu coordonate exacte): scor × {cfg['factor_locatie_operator']}; rămâne predicție până confirmă omul.")
        if plafonat:
            txt += " " + S.text_plafon(sursa_casa, w) + f" Stâlpii și cablurile prezise (analiza hărții): cel mult {S.fmt(S.plafon('analiza_harta', w))}."
        if taiat:
            txt += " Lanțul a fost tăiat la limita zonei prototipului (stâlpi în afara razei de 3 km eliminați)."
        txt += f" Treapta {treapta} din 4 (1 nod în rază, 2 rază extinsă, 3 linie dreaptă, 4 doar casa)."
        slaba = False
        if niv == "de_verificat":
            # fără „neaplicat” din lipsă de date: predicție slabă (punctată), niciodată aplicată fără om
            slaba = True
            if sp < cfg["prag_afisare"]:
                specs = [x for x in specs if x[0] == nume["casa"]]
                txt += (f" Scor {sp} sub pragul de afișare {cfg['prag_afisare']}: rămâne doar punctul casei, ca predicție slabă, fără lanț.")
            else:
                txt += f" Scor sub pragul {w['praguri']['predictie']}: predicție slabă (punctată), nu se aplică."
            niv = "predictie"
        if niv == "in_model":
            self._adauga_in_model(specs, event, sp, [txt + f" Peste pragul {w['praguri']['aplicat']}: adăugat în model, în timp real."], None)
            dec = "adaugat"
        else:
            for sid, tip_el, s in specs:
                self.predictii[sid] = s
                pr = {"metoda": "lant_racordare" if urm is not None or tip_el == "nod" else "linie_dreapta",
                      "urmeaza_strada": urm if tip_el == "tronson" else None,
                      "propunere": {"proprietate": "element_nou", "valoare": sid}, "scor_propunere": sp,
                      "slaba": slaba, "treapta": treapta}
                self._pune(sid, tip_el, data, nivel="predictie", scor=min(sp, S.plafon(s.get("sursa_locatie"), w)),
                           ultima_verificare=None, predictie=pr, sursa_locatie=s.get("sursa_locatie"), t0=False,
                           motive=[{"text": txt + f" Sub pragul {w['praguri']['aplicat']}: predicție, neaplicată; fiecare stâlp poate fi "
                                                  "acceptat sau respins separat.", "efect": 0.0, "eveniment": ev, "data": data}])
            dec = "predictie"
        for sid, _, _ in specs:
            trace["modificari"].append(self._publica(sid, self._curent(sid)))
        self._scor_pas(trace, dec, {"scor_propunere": sp, "factori": factori, "treapta": treapta, "slaba": slaba,
                                    "nivel": "in_model" if dec == "adaugat" else "predictie"}, [txt], sp)

    # ------------------------------------------------------------ val de apeluri
    def _val_apeluri(self, eid: str, data: str, delta: float, motive: list[str]) -> float:
        """Apelurile repetate pe același element, în fereastră, cântăresc mai mult decât unul, până la un plafon."""
        cfg = self.w["val_apeluri"]
        lista = [x for x in self.apeluri.setdefault(eid, []) if S.zile(x[0], data) <= cfg["fereastra_zile"]]
        n = len(lista) + 1
        if n >= cfg["numar_min"]:
            self._val_flag = True
            delta = delta * (1 + 0.5 * (n - 1))
            motive.append(f"Val de apeluri: {n} apeluri în {cfg['fereastra_zile']} zile pe același element, semnal mai puternic "
                          f"(plafon {cfg['plafon_semnal']}).")
        deja = sum(x[1] for x in lista)
        delta = max(delta, -cfg["plafon_semnal"] - deja)
        delta = min(delta, 0.0)
        lista.append((data, delta))
        self.apeluri[eid] = lista
        return delta
