"""Etapa 5: modelul GIS versionat în timp, cu decizie (adaugă / aplică / predicție), jurnal și „de ce".

`GridModel` pornește de la modelul cu defecte (`defects.build()["model"]`), primește evenimente în ordinea
datelor, păstrează pentru fiecare element o listă de stări datate și poate reda starea la orice dată
(`snapshot(data)`), cu scăderea scorului în timp. Date FICTIVE.

Regula de intrare (decisă împreună cu Victor):
- nimic existent în acel loc -> se adaugă (dacă scorul propunerii e peste prag);
- există ceva și propunerea e sigură -> se aplică;
- există ceva și propunerea e nesigură -> predicție vizibilă, neaplicată, cu scor;
- ce e doar planificat rămâne propunere; orice modificare are jurnal și motiv.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from backend.engine import scoring as S
from backend.engine.config import load_weights
from backend.engine.defects import build
from backend.engine.match import match_event
from backend.engine.network import clasa_element, dist_m

ROOT = Path(__file__).resolve().parents[2]
START = "2026-08-01"      # data de la care „știe" modelul rețeaua inițială
MAX_MOTIVE = 8


class GridModel:
    def __init__(self, net: dict | None = None, weights: dict | None = None, start: str = START):
        self.w = weights or load_weights()
        self.net = net if net is not None else build()["model"]
        self.start = start
        self.ultima_data = start
        self.istoric: dict[str, list[dict]] = {}   # element_id -> versiuni de stare, cronologic
        self.predictii: dict[str, dict] = {}       # element_id -> {tip_element, geometrie, props} (neaplicate)
        self.retrase: dict[str, dict] = {}         # predicții înlocuite de un element cu ID real (pentru istoric)
        self.jurnal: list[dict] = []
        self.traseu_fn = None   # etapa 6: callable((lat,lon),(lat,lon)) -> {"puncte":[(lat,lon)..], "urmeaza_strada":0-1}
        init = self.w["scor"]["initial_element_kmz"]
        for eid, el in self._elemente().items():
            self._pune(eid, el["tip_element"], start, nivel="in_model", scor=init, ultima_verificare=None,
                       motive=[{"text": "Element din modelul GIS, neverificat recent", "efect": 0.0,
                                "eveniment": None, "data": start}])

    # ------------------------------------------------------------------ utilitare
    def _elemente(self) -> dict[str, dict]:
        out = dict(self.net["noduri"])
        out.update(self.net["tronsoane"])
        if self.net.get("post"):
            out[self.net["post"]["id"]] = self.net["post"]
        return out

    def _pune(self, eid: str, tip: str, data: str, **schimbari) -> dict:
        """Adaugă o versiune nouă de stare pentru element (copie a ultimei + schimbările)."""
        ist = self.istoric.setdefault(eid, [])
        baza = copy.deepcopy(ist[-1]) if ist else {"element_id": eid, "tip_element": tip, "props": {},
                                                    "predictie": None, "ultimul_aplicat": None}
        baza.update(schimbari)
        baza["valid_de_la"] = data
        if len(baza.get("motive", [])) > MAX_MOTIVE:
            baza["motive"] = baza["motive"][:MAX_MOTIVE]
        ist.append(baza)
        return baza

    def _curent(self, eid: str) -> dict:
        return self.istoric[eid][-1]

    def _stare_la(self, eid: str, data: str) -> dict | None:
        ok = [s for s in self.istoric.get(eid, []) if s["valid_de_la"] <= data]
        return ok[-1] if ok else None

    def _motiv(self, eid: str, text: str, efect: float, event: dict) -> list[dict]:
        m = {"text": text, "efect": round(efect, 3), "eveniment": event["event_id"], "data": event["data"]}
        return [m] + self._curent(eid)["motive"]

    # ------------------------------------------------------------------ apply_event
    def apply_event(self, event: dict) -> dict:
        """Aplică un Event. Întoarce StepTrace (contracts/interfaces.md)."""
        w = self.w
        ajustata = None
        if event["data"] < self.ultima_data:       # evenimentele se aplică în ordine cronologică
            ajustata = event["data"]
            event = {**event, "data": self.ultima_data}
        self.ultima_data = max(self.ultima_data, event["data"])
        trace = {"event_id": event["event_id"], "data": event["data"], "pasi": [], "modificari": [],
                 "decizie": None}
        if ajustata:
            trace["nota"] = f"Data {ajustata} e anterioară ultimului eveniment aplicat; folosită {event['data']}."
        trace["pasi"].append({"nume": "extractie", "incredere": float(event.get("incredere_extractie", 1.0)),
                              "rezultat": {"echipa_sursa": event["echipa_sursa"], "tip": event["tip"],
                                           "status": event["status"],
                                           "campuri_lipsa": event.get("campuri_lipsa", [])}})
        ref0, det0 = event.get("referinta") or {}, event.get("detalii") or {}
        if not ref0.get("element_id") and det0.get("id_partial"):
            # extracția a lăsat codul brut (ex. T-002, fără prefix de categorie); potrivirea îl dezambiguizează
            event = {**event, "referinta": {**ref0, "element_id": det0["id_partial"]}}
        m = match_event(event, self.net, w)
        trace["pasi"].append({"nume": "potrivire", "rezultat": m, "incredere": m["calitate"]})

        tip = event["tip"]
        # un raport de teren care pomenește un nod numeric inexistent în model, cu coordonate, descrie de fapt
        # un nod lipsă, oricum ar fi etichetat tipul (extracția poate zice „avarie" sau „verificare")
        eid0 = ((event.get("referinta") or {}).get("element_id") or "").strip()
        if (m["status"] == "absent_din_model" and tip not in ("nod_lipsa", "racord_nou", "linie_planificata")
                and event["echipa_sursa"] in S.ECHIPE_TEREN and eid0.isdigit() and len(eid0) >= 5
                and m.get("coordonate_folosite")):
            tip = "nod_lipsa"
            event = {**event, "tip": "nod_lipsa"}
            trace["pasi"][0]["rezultat"]["tip_tratat_ca"] = "nod_lipsa"
            trace["pasi"][0]["rezultat"]["nota"] = f"Nodul {eid0} nu există în model: raportul e tratat ca nod lipsă."
        m = self._ajusteaza_element_nou(event, m, trace)
        if tip == "linie_planificata" and m["status"] == "potrivit":
            self._efect_pe_element(event, m, trace)      # planificat pe un element existent: doar notă, fără schimbare
        elif tip == "linie_planificata":
            self._planificata(event, m, trace)
        elif m["status"] == "absent_din_model" and tip in ("nod_lipsa", "racord_nou"):
            self._propune_element_nou(event, m, trace)
        elif m["status"] == "potrivit":
            self._efect_pe_element(event, m, trace)
        else:
            self._neaplicat(event, trace, f"Potrivire {m['status']}: {m['motiv']}")
        self.jurnal.append({"event_id": event["event_id"], "data": event["data"], "echipa_sursa": event["echipa_sursa"],
                            "tip": tip, "decizie": trace["decizie"],
                            "elemente": [s["element_id"] for s in trace["modificari"]],
                            "motiv": trace["pasi"][-1].get("motive", [""])[0] if trace["pasi"][-1].get("motive") else ""})
        return trace

    def _ajusteaza_element_nou(self, event: dict, m: dict, trace: dict) -> dict:
        """Un nod lipsă nu se potrivește cu un nod vecin aflat la câțiva metri: peste
        `distanta_max_element_nou_m` față de elementul cel mai apropiat, e un element NOU."""
        lim = self.w["potrivire"]["distanta_max_element_nou_m"]
        if (event["tip"] == "nod_lipsa" and m["status"] == "potrivit" and m["metoda"] == "coordonate"
                and m["candidati"] and m["candidati"][0]["distanta_m"] > lim):
            m = {**m, "status": "absent_din_model", "element_id": None, "calitate": 0.0,
                 "semnale": m["semnale"] + ["element_nou_langa_existent"],
                 "motiv": f"Cel mai apropiat element ({m['candidati'][0]['element_id']}) e la "
                          f"{m['candidati'][0]['distanta_m']} m, peste {lim} m: se tratează ca element nou, nu ca acela."}
            trace["pasi"][-1] = {"nume": "potrivire", "rezultat": m, "incredere": 0.0}
        return m

    def _vecini_declarati(self, event: dict, exclus: str | None) -> list[str]:
        """Noduri vecine date în raport: `detalii.noduri_vecine`, altfel ID-uri de noduri existente din text."""
        det = event.get("detalii") or {}
        out = [v for v in (det.get("noduri_vecine") or []) if v in self.net["noduri"]]
        if len(out) < 2:
            for tok in re.findall(r"\b\d{7}\b", event.get("text_original") or ""):
                if tok in self.net["noduri"] and tok != exclus and tok not in out:
                    out.append(tok)
        return out

    def _scor_pas(self, trace: dict, decizie: str, rezultat: dict, motive: list[str], incredere: float | None = None):
        trace["decizie"] = decizie
        trace["pasi"].append({"nume": "scor", "rezultat": {**rezultat, "decizie": decizie},
                              "incredere": incredere, "motive": motive})

    def _neaplicat(self, event: dict, trace: dict, motiv: str):
        trace["pasi"].append({"nume": "predictie", "rezultat": None, "incredere": None})
        self._scor_pas(trace, "neaplicat", {"nivel": None}, [motiv])

    # ---------------------------------------------------- efect pe un element existent
    def _efect_pe_element(self, event: dict, m: dict, trace: dict):
        w, eid, data = self.w, m["element_id"], event["data"]
        cur = self._curent(eid)
        eff = S.scor_la_data(cur["scor"], cur["valid_de_la"], data, w)
        f, q = S.fiabilitate(event, w), m["calitate"]
        det = event.get("detalii") or {}
        el = self._elemente()[eid]
        sect_noua = det.get("sectiune_noua") or det.get("sectiune_observata")
        motive: list[str] = []
        trace["pasi"].append({"nume": "predictie", "rezultat": None, "incredere": None})
        # orice raport (nu planificat) care spune ce secțiune are un tronson e o observație, aplicată sau nu
        obs_kw = ({"ultima_observatie": {"event_id": event["event_id"], "data": data, "echipa": event["echipa_sursa"],
                                         "valoare": sect_noua}}
                  if sect_noua and el["tip_element"] == "tronson" and event["tip"] != "linie_planificata" else {})

        # a) schimbare de proprietate (secțiune) la un tronson
        if event["tip"] != "linie_planificata" and sect_noua and el["tip_element"] == "tronson":
            veche = cur["props"].get("sectiune", el.get("sectiune"))
            if sect_noua == veche:
                motive.append(f"Raportul confirmă secțiunea existentă ({veche}).")
            else:
                ua = cur.get("ultima_observatie")
                conflict = (ua and ua["valoare"] != sect_noua
                            and ua["event_id"] != event["event_id"]
                            and S.zile(ua["data"], data) <= w["scor"]["fereastra_conflict_zile"])
                if conflict:
                    delta = w["scor"]["contradictie"] * f * q
                    scor = S.clamp(eff + delta, w)
                    t = (f"Conflict: {ua['event_id']} ({ua['echipa']}, {ua['data']}) spune «{ua['valoare']}», "
                         f"acest raport spune «{sect_noua}». Nimic nou aplicat, de verificat.")
                    st = self._pune(eid, el["tip_element"], data, **obs_kw, nivel="de_verificat", scor=scor,
                                    motive=self._motiv(eid, t, delta, event),
                                    predictie={"metoda": "propunere_proprietate", "urmeaza_strada": None,
                                               "propunere": {"proprietate": "sectiune", "valoare": sect_noua},
                                               "scor_propunere": None})
                    trace["modificari"].append(self._publica(eid, st))
                    self._scor_pas(trace, "conflict", {"scor_nou": scor, "nivel": "de_verificat"}, [t])
                    return
                sp, factori = S.scor_propunere(event, q, w)
                niv = S.decizie(sp, w, planificat=event["status"] == "planificat")
                txt = (f"Propunere: secțiunea {veche} -> {sect_noua}, scor {sp} "
                       f"(fiabilitate {factori['fiabilitate_sursa']}, extracție {factori['incredere_extractie']}, "
                       f"potrivire {factori['calitate_potrivire']}).")
                if niv == "in_model":
                    delta = w["scor"]["confirmare_teren"] * f * q
                    scor = S.clamp(eff + delta, w)
                    t = txt + f" Peste pragul {w['praguri']['aplicat']}: aplicat."
                    st = self._pune(eid, el["tip_element"], data, **obs_kw, nivel="in_model", scor=scor,
                                    ultima_verificare=data, props={**cur["props"], "sectiune": sect_noua},
                                    motive=self._motiv(eid, t, delta, event), predictie=None,
                                    ultimul_aplicat={"event_id": event["event_id"], "data": data,
                                                     "echipa": event["echipa_sursa"],
                                                     "proprietate": "sectiune", "valoare": sect_noua})
                    dec = "aplicat"
                elif niv == "predictie":
                    t = txt + f" Sub pragul {w['praguri']['aplicat']}: rămâne predicție, neaplicată."
                    st = self._pune(eid, el["tip_element"], data, **obs_kw, nivel="predictie", scor=eff,
                                    motive=self._motiv(eid, t, 0.0, event),
                                    predictie={"metoda": "propunere_proprietate", "urmeaza_strada": None,
                                               "propunere": {"proprietate": "sectiune", "valoare": sect_noua},
                                               "scor_propunere": sp})
                    dec = "predictie"
                else:
                    t = txt + f" Sub pragul {w['praguri']['predictie']}: doar de verificat."
                    st = self._pune(eid, el["tip_element"], data, **obs_kw, nivel="de_verificat", scor=eff,
                                    motive=self._motiv(eid, t, 0.0, event))
                    dec = "de_verificat"
                trace["modificari"].append(self._publica(eid, st))
                self._scor_pas(trace, dec, {"scor_propunere": sp, "factori": factori, "scor_nou": st["scor"],
                                            "nivel": st["nivel"]}, [t], sp)
                return

        # b) confirmare / semnal negativ / fără efect
        delta, efect = S.efect_input(event, q, w)
        if "inconsecventa_id_coordonate" in m["semnale"]:
            extra = w["scor"]["contradictie"] * f * 0.5
            delta += extra
            motive.append("ID și coordonate se contrazic: semnal contradictoriu în plus.")
        scor = S.clamp(eff + delta, w)
        nivel = cur["nivel"]
        if efect == "confirmare" and scor >= w["praguri"]["predictie"] and nivel == "de_verificat":
            nivel = "in_model"
        if scor < w["praguri"]["predictie"] and nivel == "in_model":
            nivel = "de_verificat"
        text = {
            "confirmare": f"Confirmat din teren de {event['echipa_sursa']} (fiabilitate {f}, potrivire {q}): {delta:+.3f}.",
            "semnal_negativ": f"Apel de client în zonă (fiabilitate {f}, potrivire {q}): {delta:+.3f}. Nu înseamnă că rețeaua lipsește, doar scade încrederea.",
            "fara_efect": "Informație despre ceva planificat sau neexecutat: scorul nu se schimbă.",
        }[efect]
        if efect == "fara_efect" and not motive:
            motive.append(text)
        else:
            motive.insert(0, text)
        ver = event["data"] if efect == "confirmare" else cur["ultima_verificare"]
        st = self._pune(eid, el["tip_element"], data, **obs_kw, nivel=nivel, scor=scor, ultima_verificare=ver,
                        motive=self._motiv(eid, " ".join(motive), delta, event))
        trace["modificari"].append(self._publica(eid, st))
        self._scor_pas(trace, "scor_actualizat" if efect != "fara_efect" else "fara_efect",
                       {"scor_nou": scor, "nivel": nivel, "efect": efect}, motive)

    # ------------------------------------------------------ element nou (nod lipsă / racord)
    def _propune_element_nou(self, event: dict, m: dict, trace: dict):
        w, data = self.w, event["data"]
        cf = m["coordonate_folosite"]
        pt = (cf["lat"], cf["lon"]) if cf else None
        ref, det = event.get("referinta") or {}, event.get("detalii") or {}
        eid = (ref.get("element_id") or "").strip()
        id_dat = eid if (eid.isdigit() and len(eid) >= 5 and eid not in self.net["noduri"]) else None
        if not id_dat:
            eid = f"NOU-{event['event_id']}"
        cu_tronsoane = event["tip"] == "nod_lipsa"
        dati = self._vecini_declarati(event, id_dat) if cu_tronsoane else []
        pozitie_dedusa = False
        if not pt and cu_tronsoane and len(dati) >= 2:
            na, nb = (self.net["noduri"][x] for x in dati[:2])
            pt = ((na["lat"] + nb["lat"]) / 2, (na["lon"] + nb["lon"]) / 2)
            pozitie_dedusa = True      # fără coordonate: mijlocul dintre vecini, doar ca predicție slabă
        if not pt:
            return self._neaplicat(event, trace, "Element lipsă, dar fără coordonate (și fără doi vecini cunoscuți) nu îl putem plasa pe hartă.")

        vecini, dedusi = [], False
        if cu_tronsoane:
            if len(dati) >= 2:
                vecini = dati[:2]
            else:
                dedusi = True
                cand = sorted((n for n in self.net["noduri"].values() if dist_m(pt, (n["lat"], n["lon"])) >= 5),
                              key=lambda n: dist_m(pt, (n["lat"], n["lon"])))
                vecini = [n["id"] for n in cand[:2]]
        q = w["potrivire"]["calitate_dupa_id"] if ref.get("element_id") else w["potrivire"]["calitate_dupa_coordonate"]
        if dedusi:
            q *= w["propunere"]["factor_vecini_dedusi"]
        if "coordonate_corectate" in m["semnale"]:
            q *= 0.8
        if "coordonate_zecimale_reparate" in m["semnale"]:
            q *= w["potrivire"]["factor_zecimale_reparate"]
        if pozitie_dedusa:
            q *= w["potrivire"]["factor_pozitie_din_vecini"]

        # geometria legăturilor: traseu OSM dacă există (etapa 6), altfel linie dreaptă
        legaturi, urm, info_leg = [], [], []
        for v in vecini:
            nv = self.net["noduri"][v]
            a, b = pt, (nv["lat"], nv["lon"])
            r = self.traseu_fn(a, b) if self.traseu_fn else None
            if r:
                legaturi.append((v, r["puncte"], "traseu_strada_osm"))
                urm.append(r["urmeaza_strada"])
                info_leg.append({"vecin": v, "metoda": "traseu_strada_osm", "urmeaza_strada": r["urmeaza_strada"],
                                 "abatere_dreapta_m": r.get("abatere_dreapta_m"), "lungime_m": r["lungime_m"],
                                 "lungime_dreapta_m": r["lungime_dreapta_m"]})
            else:
                legaturi.append((v, [a, b], "linie_dreapta"))
                urm.append(None)
                info_leg.append({"vecin": v, "metoda": "linie_dreapta", "urmeaza_strada": None,
                                 "motiv": "nicio stradă credibilă aproape" if self.traseu_fn else "traseu OSM indisponibil"})
        # o legătură fără stradă credibilă rămâne linie dreaptă și contează neutru (0,5: nici confirmată,
        # nici infirmată); dacă nicio legătură nu are traseu, factorul lipsește și ponderile se renormalizează
        urmeaza = (round(sum(0.5 if u is None else u for u in urm) / len(urm), 3)
                   if any(u is not None for u in urm) else None)
        metoda = "traseu_strada_osm" if urmeaza is not None else "linie_dreapta"

        # există deja o predicție pentru același element? atunci acest raport o întărește
        vechi_ids: list[str] = []
        pid = next((p for p, v in self.predictii.items() if "punct" in v and (
            p == eid or dist_m(pt, v["punct"]) <= w["potrivire"]["distanta_max_m"])), None)
        sp, factori = S.scor_propunere(event, q, w, urmeaza)
        motive = []
        if pid:
            vechi = self._curent(pid)["predictie"]["scor_propunere"]
            sp = S.clamp(max(vechi, sp) + w["scor"]["confirmare_teren"] * S.fiabilitate(event, w) * q, w)
            motive.append(f"Al doilea raport despre {pid}: scorul propunerii crește de la {vechi} la {round(sp, 3)}.")
            if id_dat and id_dat != pid:
                vechi_ids = [pid] + [k for k in self.predictii if k.startswith(f"{pid}-") or k.startswith(f"NOU-{pid}-")]
                eid = id_dat          # raportul dă ID-ul real: predicția se „mută" pe el
            else:
                eid = pid
        niv = S.decizie(sp, w)
        planificat = event["status"] == "planificat"      # „semnalat" = observație din teren, nu lucrare viitoare
        if planificat and niv == "in_model":
            niv = "predictie"
        if pozitie_dedusa and niv == "in_model":
            niv = "predictie"       # poziția e doar un ghid (mijlocul dintre vecini): nu se aplică în model
            motive.append("Poziția nodului e dedusă din vecini (fără coordonate în raport): rămâne predicție.")
        txt = (f"Propunere: {'nod lipsă' if cu_tronsoane else 'racord nou'} {eid}"
               + (f" între {vecini[0]} și {vecini[1]}" + (" (vecini deduși)" if dedusi else "") if vecini else "")
               + f", scor {sp} (fiabilitate {factori['fiabilitate_sursa']}, extracție {factori['incredere_extractie']}, "
                 f"potrivire {factori['calitate_potrivire']}" + (f", urmează strada {urmeaza}" if urmeaza is not None else "") + ").")
        trace["pasi"].append({"nume": "predictie", "incredere": urmeaza if urmeaza is not None else q,
                              "rezultat": {"metoda": metoda, "element_nou": eid, "vecini": vecini,
                                           "vecini_dedusi": dedusi, "pozitie_dedusa": pozitie_dedusa,
                                           "urmeaza_strada": urmeaza,
                                           "legaturi": info_leg}})
        rez = {"scor_propunere": sp, "factori": factori, "nivel": niv}

        if niv == "de_verificat":
            self._scor_pas(trace, "neaplicat", rez, motive + [txt + f" Sub pragul {w['praguri']['predictie']}: nu se desenează, rămâne în jurnal."], sp)
            return
        for oid in vechi_ids:           # predicția veche e înlocuită de elementul cu ID-ul real
            tip_o = self._curent(oid)["tip_element"]
            self._pune(oid, tip_o, data, retras=True, nivel="predictie",
                       motive=[{"text": f"Înlocuită de elementul {eid} (raportul {event['event_id']} dă ID-ul real).",
                                "efect": 0.0, "eveniment": event["event_id"], "data": data}] + self._curent(oid)["motive"])
            self.retrase[oid] = self.predictii.pop(oid, None)   # geometria rămâne pentru date anterioare
        specs = [(eid, "nod", {"punct": pt, "geometrie": {"type": "Point", "coordinates": [pt[1], pt[0]]}})]
        for (v, puncte, met), u_leg in zip(legaturi, urm):
            tid = f"{eid}-{v}" if eid.startswith("NOU-") else f"NOU-{eid}-{v}"
            specs.append((tid, "tronson", {"puncte": puncte, "metoda": met, "capete": (eid, v), "urmeaza": u_leg,
                                           "geometrie": {"type": "LineString",
                                                         "coordinates": [[o, a] for a, o in puncte]}}))
        if niv == "in_model":
            self._adauga_in_model(specs, event, sp, motive + [txt + f" Peste pragul {w['praguri']['aplicat']}: adăugat în model."], pid)
            dec = "adaugat"
        else:
            for sid, tip_el, sp_ in specs:
                self.predictii[sid] = sp_
                pr = {"metoda": sp_.get("metoda", metoda), "urmeaza_strada": sp_["urmeaza"] if "urmeaza" in sp_ else urmeaza,
                      "propunere": {"proprietate": "element_nou", "valoare": sid}, "scor_propunere": sp}
                if sid in self.istoric:
                    mot = self._motiv(sid, txt + " Sub prag: rămâne predicție.", 0.0, event)
                else:
                    mot = [{"text": txt + f" Sub pragul {w['praguri']['aplicat']}: predicție, neaplicată.",
                            "efect": 0.0, "eveniment": event["event_id"], "data": data}]
                st = self._pune(sid, tip_el, data, nivel="predictie", scor=sp, ultima_verificare=None,
                                motive=mot, predictie=pr)
            dec = "predictie"
            for sid, tip_el, _ in specs:
                trace["modificari"].append(self._publica(sid, self._curent(sid)))
            self._scor_pas(trace, dec, rez, motive + [txt], sp)
            return
        for sid, _, _ in specs:
            trace["modificari"].append(self._publica(sid, self._curent(sid)))
        self._scor_pas(trace, dec, {**rez, "scor_nou": sp, "nivel": "in_model"}, motive + [txt], sp)

    def _adauga_in_model(self, specs, event, sp, motive, pid):
        data = event["data"]
        for sid, tip_el, s in specs:
            if tip_el == "nod":
                self.net["noduri"][sid] = {"id": sid, "tip_element": "nod", "serie": "Nod JT (adăugat din raport)",
                                           "plecare": None, "lat": s["punct"][0], "lon": s["punct"][1]}
            else:
                pts = s["puncte"]
                self.net["tronsoane"][sid] = {
                    "id": sid, "cod_original": None, "tip_element": "tronson",
                    "categorie": "adăugat din raport", "sectiune": None,
                    "lungime_m": round(sum(dist_m(a, b) for a, b in zip(pts, pts[1:])), 1),
                    "puncte": pts, "capete": tuple(s["capete"])}
            self.predictii.pop(sid, None)
            mot = [{"text": " ".join(motive), "efect": 0.0, "eveniment": event["event_id"], "data": data}]
            self._pune(sid, tip_el, data, nivel="in_model", scor=sp, motive=mot, predictie=None,
                       ultima_verificare=data if event["status"] == "executat" else None)

    # ------------------------------------------------------------------ linie planificată
    def _planificata(self, event: dict, m: dict, trace: dict):
        w, data = self.w, event["data"]
        noduri = [n for n in ((event.get("detalii") or {}).get("noduri") or []) if n in self.net["noduri"]]
        trace["pasi"].append({"nume": "predictie", "incredere": None, "rezultat": None})
        if len(noduri) < 2:
            return self._scor_pas(trace, "neaplicat", {"nivel": None},
                                  ["Linie planificată fără două noduri cunoscute în `detalii.noduri`: nu are geometrie."])
        a, b = (self.net["noduri"][n] for n in noduri[:2])
        pts = [(a["lat"], a["lon"]), (b["lat"], b["lon"])]
        q = 1.0 if noduri else 0.7
        sp, factori = S.scor_propunere(event, q, w)
        sid = f"PLAN-{event['event_id']}"
        self.predictii[sid] = {"puncte": pts, "metoda": "linie_dreapta", "capete": tuple(noduri[:2]),
                               "geometrie": {"type": "LineString", "coordinates": [[o, la] for la, o in pts]}}
        txt = (f"Linie planificată între {noduri[0]} și {noduri[1]}, scor {sp}. Ce e doar planificat nu se aplică "
               f"în model până nu e executat, indiferent de scor.")
        st = self._pune(sid, "tronson", data, nivel="predictie" if sp >= w["praguri"]["predictie"] else "de_verificat",
                        scor=sp, ultima_verificare=None,
                        motive=[{"text": txt, "efect": 0.0, "eveniment": event["event_id"], "data": data}],
                        predictie={"metoda": "linie_dreapta", "urmeaza_strada": None,
                                   "propunere": {"proprietate": "linie_planificata", "valoare": sid},
                                   "scor_propunere": sp})
        trace["modificari"].append(self._publica(sid, st))
        self._scor_pas(trace, "predictie", {"scor_propunere": sp, "factori": factori, "nivel": st["nivel"]}, [txt], sp)

    # ------------------------------------------------------------------ ieșiri
    def _publica(self, eid: str, st: dict) -> dict:
        """ElementState (contracts/state.schema.json) pentru StepTrace."""
        return {k: st[k] for k in ("element_id", "tip_element", "nivel", "scor", "valid_de_la",
                                    "ultima_verificare", "motive", "predictie") if k in st}

    def _geometrie(self, eid: str) -> dict | None:
        el = self._elemente().get(eid)
        if el is None:
            p = self.predictii.get(eid) or self.retrase.get(eid)
            return p["geometrie"] if p else None
        if el["tip_element"] == "tronson":
            return {"type": "LineString", "coordinates": [[o, a] for a, o in el["puncte"]]}
        return {"type": "Point", "coordinates": [el["lon"], el["lat"]]}

    def _props_element(self, eid: str) -> dict:
        el = self._elemente().get(eid, {})
        keep = {k: v for k, v in el.items() if k not in ("puncte", "lat", "lon", "id", "tip_element")}
        if "capete" in keep:
            keep["capete"] = list(keep["capete"])
        keep["clasa"] = clasa_element(el) if el else "casa"
        return keep

    def stare_efectiva(self, eid: str, data: str) -> dict | None:
        """Starea unui element la `data`: scor cu scădere în timp, nivel recalculat."""
        st = self._stare_la(eid, data)
        if not st:
            return None
        out = copy.deepcopy(st)
        eff = S.scor_la_data(st["scor"], st["valid_de_la"], data, self.w)
        out["scor"] = round(eff, 3)
        out["valid_de_la"] = st["valid_de_la"]
        if st["nivel"] == "in_model" and eff < self.w["praguri"]["predictie"]:
            out["nivel"] = "de_verificat"
        zile = S.zile(st["ultima_verificare"] or self.start, data)
        if S.zile(st["valid_de_la"], data) > 0 and st["nivel"] in ("in_model", "de_verificat") and eff < st["scor"]:
            out["motive"] = [{"text": f"Neverificat de {zile} zile: scorul scade cu "
                                      f"{abs(self.w['scor']['scadere_per_30_zile'])} la 30 de zile.",
                              "efect": round(eff - st["scor"], 3), "eveniment": None, "data": data}] + out["motive"]
        return out

    def snapshot(self, data: str | None = None) -> dict:
        """GeoJSON FeatureCollection cu starea rețelei la `data` (properties = ElementState + atribute).
        Fără `data`: ultima dată cunoscută (ultimul eveniment aplicat)."""
        data = data or self.ultima_data
        feats = []
        for eid in self.istoric:
            st = self.stare_efectiva(eid, data)
            g = self._geometrie(eid)
            if not st or not g or st.get("retras"):
                continue
            props = self._props_element(eid)
            props.update(st.pop("props", {}))
            props.update({k: st[k] for k in ("element_id", "tip_element", "nivel", "scor", "valid_de_la",
                                             "ultima_verificare", "motive", "predictie")})
            if eid not in self._elemente():      # predicție sau element neaplicat: clasa după tip
                props["clasa"] = clasa_element({"tip_element": st["tip_element"]})
            props.setdefault("confirmat_de", st.get("confirmat_de"))
            feats.append({"type": "Feature", "geometry": g, "properties": props})
        return {"type": "FeatureCollection", "name": f"Rețea JT PTAB 7812 la {data} (date fictive)",
                "features": feats}

    def timeline(self) -> list[dict]:
        out = []
        for j in self.jurnal:
            out.append({"data": j["data"], "event_id": j["event_id"], "decizie": j["decizie"],
                        "rezumat": f"{j['echipa_sursa']}: {j['tip']} -> {j['decizie']}",
                        "elemente_atinse": j["elemente"]})
        return out

    def statistici(self, data: str) -> dict:
        """Procent din rețea pe niveluri și scor mediu la `data` (pentru panoul de statistici)."""
        fs = self.snapshot(data)["features"]
        n = len(fs) or 1
        niv: dict[str, int] = {}
        for f in fs:
            niv[f["properties"]["nivel"]] = niv.get(f["properties"]["nivel"], 0) + 1
        return {"data": data, "elemente": len(fs),
                "procent": {k: round(100 * v / n, 1) for k, v in niv.items()},
                "scor_mediu": round(sum(f["properties"]["scor"] for f in fs) / n, 3),
                "verificat_recent_pct": round(100 * sum(1 for f in fs if f["properties"]["ultima_verificare"]
                                                       and S.zile(f["properties"]["ultima_verificare"], data) <= 30) / n, 1)}

    def export(self, out_dir: Path | None = None) -> None:
        out = Path(out_dir or ROOT / "data" / "model")
        (out / "snapshots").mkdir(parents=True, exist_ok=True)
        zile_ev = sorted({self.start, *(j["data"] for j in self.jurnal)})
        for d in zile_ev:
            (out / "snapshots" / f"{d}.geojson").write_text(
                json.dumps(self.snapshot(d), ensure_ascii=False), encoding="utf-8")
        (out / "timeline.json").write_text(json.dumps(self.timeline(), ensure_ascii=False, indent=2), encoding="utf-8")
        (out / "jurnal.json").write_text(json.dumps(self.jurnal, ensure_ascii=False, indent=2), encoding="utf-8")
