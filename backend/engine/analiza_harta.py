"""Analiza hărții (Sesiunea 4, D4/V3): cel mai plauzibil traseu al unei legături prezise, pe străzi, nu prin case.

Sursa e graful de străzi OSM local (`osm.strazi()`, fără imagini, fără serviciu extern). Funcții pure și
deterministe; parametrii sunt în `weights.yaml` (`analiza_harta`, `plafon_locatie`, `potrivire`,
`mutare_fire_document`, `zona`).

    traseu_pe_strazi((lat, lon), net, cfg) -> dict

Date FICTIVE pentru rețea; străzile sunt reale (© contribuitorii OpenStreetMap, ODbL).
"""
from __future__ import annotations

import heapq
import math

from backend.engine import osm
from backend.engine.network import dist_m
from backend.engine.zona import zona_ok

SNAP_START_MAX_M = osm.SNAP_MAX_M      # un stâlp de plecare mai departe de stradă nu se leagă pe stradă
FACTOR_BRANSAMENT_MIN = 0.5             # branșament foarte lung: factorul scade spre 0,5, nu sub


# ----------------------------------------------------------------------------- graful numit
def _construieste_graf(strazi: list[dict]) -> dict:
    """Adiacență {nod: [(vecin, lungime_m, nume)]} și segmente [(u, v, nume)] din străzile {nume, puncte}."""
    adj: dict[tuple, list] = {}
    seg: list[tuple] = []
    for s in strazi:
        nume = s.get("nume")
        g = [osm._k(p[0], p[1]) for p in s["puncte"]]
        for u, v in zip(g, g[1:]):
            if u == v:
                continue
            L = dist_m(u, v)
            adj.setdefault(u, []).append((v, L, nume))
            adj.setdefault(v, []).append((u, L, nume))
            seg.append((u, v, nume))
    return {"adj": adj, "seg": seg}


_CACHE: dict = {}


def _graf(strazi: list[dict] | None) -> dict:
    """Graful pentru `strazi` dat sau, fără argument, pentru cache-ul OSM local (reținut o singură dată)."""
    if strazi is not None:
        return _construieste_graf(strazi)
    if "osm" not in _CACHE:
        _CACHE["osm"] = _construieste_graf(osm.strazi())
    return _CACHE["osm"]


def _snap(p, segmente):
    """(distanță_m, punct_proiectat, u, v, nume) pentru segmentul cel mai apropiat de p, sau None."""
    best = None
    for u, v, nume in segmente:
        q, d = osm._proiecteaza(p, u, v)
        if best is None or d < best[0]:
            best = (d, q, u, v, nume)
    return best


def _stalpi(n: int) -> str:
    return "1 stâlp nou" if n == 1 else f"{n} stâlpi noi"


def _lungime(pts) -> float:
    return sum(dist_m(a, b) for a, b in zip(pts, pts[1:]))


def _in_cerc(a, b, evita) -> bool:
    """Muchia a-b intră (măcar în parte) în cercul de evitat."""
    if not evita:
        return False
    return osm._proiecteaza(tuple(evita["centru"]), a, b)[1] <= float(evita["raza_m"])


# ----------------------------------------------------------------------------- drum pe graf
def _drum(sp, tp, graf, evita, preferate_cf, cost_pref):
    """Cel mai scurt drum (cost, nu lungime) de la proiecția de start `sp` la proiecția țintei `tp`.

    sp/tp = (d, q, u, v, nume). Muchiile din cercul `evita` nu se folosesc; muchiile străzilor din
    `preferate_cf` costă `cost_pref`×. Întoarce lista de (punct, nume_muchie_spre_el) de la q_start la q_țintă
    sau None dacă nu există drum."""
    adj = graf["adj"]
    S_, T_ = ("S",), ("T",)
    qs, qt = sp[1], tp[1]

    def cost(L, nume):
        return L * (cost_pref if nume and nume.casefold() in preferate_cf else 1.0)

    extra: dict = {S_: [], T_: []}
    for P, (_, q, u, v, nume) in ((S_, sp), (T_, tp)):
        for cap in (u, v):
            if not _in_cerc(q, cap, evita):
                extra[P].append((cap, dist_m(q, cap), nume))
    # proiecțiile devin noduri legate de capetele segmentului lor (și invers)
    legate: dict = {}
    for P, (_, q, u, v, nume) in ((S_, sp), (T_, tp)):
        for cap in (u, v):
            if not _in_cerc(q, cap, evita):
                legate.setdefault(cap, []).append((P, dist_m(q, cap), nume))
    if {sp[2], sp[3]} == {tp[2], tp[3]} and not _in_cerc(qs, qt, evita):
        extra[S_].append((T_, dist_m(qs, qt), sp[4]))     # același segment: drum direct

    def vecini(n):
        if n in extra:
            return extra[n]
        out = [x for x in adj.get(n, []) if not _in_cerc(n, x[0], evita)]
        return out + legate.get(n, [])

    dist, prev, pq, i = {S_: 0.0}, {}, [(0.0, 0, S_)], 0
    while pq:
        d, _, n = heapq.heappop(pq)
        if n == T_:
            break
        if d > dist.get(n, 1e18):
            continue
        for m, L, nume in vecini(n):
            nd = d + cost(L, nume)
            if nd < dist.get(m, 1e18) - 1e-9:
                dist[m], prev[m] = nd, (n, nume)
                i += 1
                heapq.heappush(pq, (nd, i, m))
    if T_ not in dist:
        return None
    cale, n = [], T_
    while n != S_:
        p, nume = prev[n]
        cale.append((qt if n == T_ else n, nume))
        n = p
    cale.append((qs, None))
    cale.reverse()
    return cale


# ----------------------------------------------------------------------------- stâlpi pe drum
def _la_distanta(pts, s):
    """Punctul de la distanța s (m) de începutul polilinie `pts`."""
    for a, b in zip(pts, pts[1:]):
        L = dist_m(a, b)
        if s <= L:
            t = s / L if L else 0.0
            return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        s -= L
    return pts[-1]


def _arc(pts, p):
    """(distanță_m față de polilinie, distanța de-a lungul ei până la proiecția lui p)."""
    best, acc = (1e18, 0.0), 0.0
    for a, b in zip(pts, pts[1:]):
        q, d = osm._proiecteaza(p, a, b)
        if d < best[0]:
            best = (d, acc + dist_m(a, q))
        acc += dist_m(a, b)
    return best


def _taie(pts, s0, s1):
    """Subpolilinia dintre distanțele s0 și s1 de-a lungul lui `pts` (capete incluse)."""
    out, acc = [_la_distanta(pts, s0)], 0.0
    for a, b in zip(pts, pts[1:]):
        acc += dist_m(a, b)
        if s0 < acc < s1:
            out.append(b)
    out.append(_la_distanta(pts, s1))
    return [p for k, p in enumerate(out) if k == 0 or p != out[k - 1]]


def _lant(pts, de_la, pool, cfg, net):
    """Stâlpii de pe polilinia `pts` (de la stâlpul `de_la` spre țintă): existenți refolosiți + stâlpi noi.

    Returnează dict {stalpi_noi: [(lat, lon)], reutilizati: [id], cabluri: [{de_la, la, puncte}], taiat: bool}.
    Ancorele sunt stâlpii existenți la < `reutilizare_stalp_m` de drum; între ancore se pun stâlpi noi la
    cel mult `pas_stalp_m` unul de altul. Stâlpii noi în afara zonei se taie (lanțul se oprește la ultimul bun)."""
    a = cfg["analiza_harta"]
    pas, reut = float(a["pas_stalp_m"]), float(a["reutilizare_stalp_m"])
    dmin = float(cfg["potrivire"]["distanta_max_element_nou_m"])
    total = _lungime(pts)
    ancore = []                                     # (s, id, punct) pentru stâlpii existenți de pe drum
    for nid, p in pool:
        if nid == de_la:
            continue
        d, s = _arc(pts, p)
        if d < max(reut, dmin) and 1.0 < s < total - 1.0:
            ancore.append((s, nid, p))
    ancore.sort(key=lambda x: (x[0], x[1]))
    # două ancore la același punct: rămâne prima
    ancore = [x for k, x in enumerate(ancore) if k == 0 or x[0] - ancore[k - 1][0] > 1.0]
    puncte = [(0.0, de_la, pts[0], False)] + [(s, nid, p, False) for s, nid, p in ancore]
    capete = [x[0] for x in puncte] + [total]
    lant = [puncte[0]]
    for k, (s0, nid, p, _) in enumerate(puncte):
        s1 = capete[k + 1]
        gap = s1 - s0
        n = max(0, math.ceil(gap / pas) - 1) if gap > pas else 0
        for j in range(1, n + 1):
            s = s0 + gap * j / (n + 1)
            lant.append((s, None, _la_distanta(pts, s), True))
        if k + 1 < len(puncte):
            lant.append(puncte[k + 1])
    # zona prototipului: stâlpii noi din afară se taie
    taiat = False
    for k, x in enumerate(lant):
        if x[3] and not zona_ok(x[2][0], x[2][1], net, cfg)["ok"]:
            lant, taiat = lant[:k], True
            break
    # ids și cabluri
    noi, ids, k_nou = [], [], 0
    for s, nid, p, nou in lant:
        if nou:
            k_nou += 1
            noi.append(p)
            ids.append(f"stalp-{k_nou}")
        else:
            ids.append(nid)
    cabluri = []
    lant_s = [x[0] for x in lant] + [total]
    ids_all = ids + ["casa"]
    for k in range(len(lant) - 1 if taiat else len(lant)):     # tăiat: lanțul se oprește la ultimul stâlp din zonă
        cabluri.append({"de_la": ids_all[k], "la": ids_all[k + 1], "puncte": [list(q) for q in _taie(pts, lant_s[k], lant_s[k + 1])]})
    return {"stalpi_noi": noi, "reutilizati": [x[1] for x in lant if not x[3] and x[1] != de_la],
            "cabluri": cabluri, "taiat": taiat, "ids": ids}


def departe_de_tronsoane(p: tuple[float, float], net: dict, prag_m: float) -> bool:
    """True dacă p e la mai mult de `prag_m` de orice tronson al rețelei (nod nou izolat, fără legătură aproape)."""
    for t in net["tronsoane"].values():
        pts = [tuple(q) for q in t["puncte"]]
        if any(osm._proiecteaza(p, u, v)[1] <= prag_m for u, v in zip(pts, pts[1:])):
            return False
    return True


NOD_DEPARTE_M = 80.0        # nod lipsă la mai mult de atât de orice tronson: legăturile lui se fac pe străzi
LEGATURA_LUNGA_M = 80.0     # o legătură în linie dreaptă mai lungă decât atât devine drum pe străzi


# ----------------------------------------------------------------------------- funcția publică
def traseu_pe_strazi(tinta: tuple[float, float], net: dict, cfg: dict, evita: dict | None = None,
                     preferate: list[str] | None = None, exclus: set | None = None, *,
                     sursa: str | None = None, de_la: str | None = None, strazi: list[dict] | None = None) -> dict:
    """Cel mai plauzibil traseu pe străzi de la un stâlp existent la `tinta` (lat, lon). Pură, deterministă.

    Pași: (1) ținta se proiectează pe cel mai apropiat segment de stradă (`bransament_m`); (2) puncte de plecare =
    primii `analiza_harta.candidati` stâlpi existenți din `net["noduri"]` (fără cei care se termină în „-casa”, fără
    `exclus`) aflați în `raza_cautare_m` în linie dreaptă, proiectați pe stradă (la cel mult 40 m de ea); (3) pentru
    fiecare, drumul cel mai scurt pe graful de străzi; se alege cel mai scurt (drum + branșamente); (4) pe drum se
    pun stâlpi noi la cel mult `pas_stalp_m`, refolosind stâlpii existenți la < `reutilizare_stalp_m` de drum;
    stâlpii noi în afara zonei de 3 km se taie; (5) acuratețea e calculată ca mai jos.

    Parametri:
      tinta     (lat, lon) al casei/nodului de legat.
      net       dict-ul motorului {noduri, tronsoane, ...} (stâlpii existenți = `net["noduri"]`; predicțiile NU sunt în el).
      cfg       weights.yaml încărcat (`analiza_harta`, `plafon_locatie`, `potrivire`, `mutare_fire_document`, `zona`).
      evita     {"centru": (lat, lon), "raza_m": r}: muchiile care intră în cerc nu se folosesc (V4, mutare fire).
      preferate nume de străzi: muchiile lor costă `mutare_fire_document.cost_strada_noua`× (V4); costul schimbă alegerea,
                nu lungimea raportată.
      exclus    set de ID-uri de stâlpi care nu pot fi puncte de plecare sau refolosite (ex. predicții, nodul însuși).
      sursa     sursa locației ținței (cheie din `plafon_locatie`); implicit `analiza_harta`.
      de_la     doar acest stâlp ca punct de plecare (legătura unui nod lipsă spre un vecin declarat).
      strazi    listă {nume, puncte} în locul cache-ului OSM (teste).

    Acuratețea: `acuratete` = `plafon_locatie[sursa]` × `factor`, unde `factor` = max(`factor_min`,
    exp(−L/`lungime_referinta_m`)) × factor_branșament; L = lungimea drumului în m; factor_branșament = 1 până la
    `max_bransament_m`, apoi `max_bransament_m`/bransament_m (nu sub 0,5). `acuratete_stalpi` = min(acuratete,
    `plafon_locatie.analiza_harta`) pentru stâlpii intermediari. Fără drum: `acuratete` = min(plafon, `fara_drum`).

    Întoarce {tinta{lat,lon}, bransament_m, ales{de_la, lungime_m, strazi[], stalpi_noi[[lat,lon]], stalpi_reutilizati[id],
    traseu[[lat,lon]], cabluri[{de_la, la, puncte}] ("stalp-k" = al k-lea stâlp nou, „casa” = ținta), taiat}|None,
    alternative[{de_la, lungime_m, motiv, traseu}], acuratete, acuratete_stalpi, factor, fara_drum, explicatie[3 fraze]}.
    `ales` e None doar când nu există niciun stâlp existent în `raza_cautare_m` (și `fara_drum` e True)."""
    a = cfg["analiza_harta"]
    graf = _graf(strazi)
    tinta = (float(tinta[0]), float(tinta[1]))
    plaf_s = float((cfg.get("plafon_locatie") or {}).get(sursa or "analiza_harta", 1.0))
    plaf_a = float((cfg.get("plafon_locatie") or {}).get("analiza_harta", 1.0))
    exclus = set(exclus or ())
    pref_cf = {s.casefold() for s in (preferate or [])}
    cost_pref = float((cfg.get("mutare_fire_document") or {}).get("cost_strada_noua", 1.0))
    out = {"tinta": {"lat": tinta[0], "lon": tinta[1]}, "bransament_m": None, "ales": None, "alternative": [],
           "acuratete": 0.0, "acuratete_stalpi": 0.0, "factor": 0.0, "fara_drum": True, "explicatie": []}

    pool = sorted(((n["id"], (n["lat"], n["lon"])) for n in net["noduri"].values()
                   if not str(n["id"]).endswith("-casa") and n["id"] not in exclus), key=lambda x: x[0])
    if de_la is not None:
        cand = [x for x in pool if x[0] == de_la] or [(de_la, (net["noduri"][de_la]["lat"], net["noduri"][de_la]["lon"]))]
        pool = [x for x in pool if x[0] != de_la]
        n_raza = 1
    else:
        cand_all = sorted(((dist_m(tinta, p), nid, p) for nid, p in pool if dist_m(tinta, p) <= a["raza_cautare_m"]))
        n_raza = len(cand_all)
        cand = [(nid, p) for _, nid, p in cand_all[: int(a["candidati"])]]
    st = _snap(tinta, graf["seg"])
    if st:
        out["bransament_m"] = round(st[0], 1)
    f_bran = 1.0
    if st and st[0] > a["max_bransament_m"]:
        f_bran = max(FACTOR_BRANSAMENT_MIN, a["max_bransament_m"] / st[0])

    def factor(L):
        return round(max(a["factor_min"], math.exp(-L / a["lungime_referinta_m"])) * f_bran, 4)

    if not cand:
        out["acuratete"] = out["acuratete_stalpi"] = round(min(plaf_s, a["fara_drum"]), 3)
        out["factor"] = a["fara_drum"]
        out["explicatie"] = [f"Nu am găsit niciun stâlp existent în {a['raza_cautare_m']:g} m.",
                             "Nu există drum pe străzi; linie dreaptă, de verificat.",
                             "Nu am pus niciun stâlp nou."]
        return out

    # drumuri candidate
    rezultate = []     # (lungime, de_la, traseu, nume_strazi, motiv_none) pentru cele cu drum
    fara = []          # candidații fără drum pe străzi
    for nid, p in cand:
        sp = _snap(p, graf["seg"])
        if not st or not sp or sp[0] > SNAP_START_MAX_M:
            fara.append((nid, p, f"stâlpul e la {sp[0]:.0f} m de cea mai apropiată stradă (peste {SNAP_START_MAX_M:g} m): nu se leagă pe stradă"
                         if sp else "nu există străzi"))
            continue
        cale = _drum(sp, st, graf, evita, pref_cf, cost_pref)
        if not cale:
            fara.append((nid, p, "nu există legătură pe străzi"))
            continue
        traseu = [p] + [q for q, _ in cale] + [tinta]
        traseu = [q for k, q in enumerate(traseu) if k == 0 or q != traseu[k - 1]]
        nume, vazute = [], set()
        for k, (_, nm) in enumerate(cale):
            if k and dist_m(cale[k - 1][0], cale[k][0]) < 1.0:
                continue            # muchii virtuale de lungime ~0 (capătul coincide cu nodul) nu dau nume de stradă
            if nm and nm not in vazute:
                vazute.add(nm)
                nume.append(nm)
        cost = sum(dist_m(cale[k - 1][0], cale[k][0]) * (cost_pref if cale[k][1] and cale[k][1].casefold() in pref_cf else 1.0)
                   for k in range(1, len(cale)))
        # cost total = drum ponderat + branșamentele (stâlp și țintă) ca să fie comparabile
        cost += sp[0] + st[0]
        rezultate.append((round(cost, 3), nid, round(_lungime(traseu), 1), traseu, nume))
    rezultate.sort(key=lambda x: (x[0], x[1]))

    if not rezultate:
        nid, p, _ = sorted(fara, key=lambda x: (dist_m(tinta, x[1]), x[0]))[0]
        traseu = [p, tinta]
        L = round(dist_m(p, tinta), 1)
        lant = _lant(traseu, nid, pool, cfg, net)
        out["ales"] = {"de_la": nid, "lungime_m": L, "strazi": [], "stalpi_noi": lant["stalpi_noi"],
                       "stalpi_reutilizati": lant["reutilizati"], "traseu": [list(q) for q in traseu],
                       "cabluri": lant["cabluri"], "taiat": lant["taiat"]}
        out["alternative"] = [{"de_la": n2, "lungime_m": round(dist_m(tinta, p2), 1), "motiv": m, "traseu": [list(p2), list(tinta)]}
                              for n2, p2, m in fara if n2 != nid]
        out["acuratete"] = out["acuratete_stalpi"] = round(min(plaf_s, a["fara_drum"]), 3)
        out["factor"] = a["fara_drum"]
        out["explicatie"] = [f"Am găsit {n_raza} stâlpi în {a['raza_cautare_m']:g} m și am verificat {len(cand)}.",
                             "Nu există drum pe străzi; linie dreaptă, de verificat.",
                             f"Am pus {_stalpi(len(lant['stalpi_noi']))} pe linia dreaptă de {L:g} m spre {nid}."
                             + (" Lanțul a fost tăiat la limita zonei prototipului." if lant["taiat"] else "")]
        return out

    cost0, nid, L, traseu, nume = rezultate[0]
    lant = _lant(traseu, nid, pool, cfg, net)
    out["fara_drum"] = False
    out["ales"] = {"de_la": nid, "lungime_m": L, "strazi": nume, "stalpi_noi": [list(q) for q in lant["stalpi_noi"]],
                   "stalpi_reutilizati": lant["reutilizati"], "traseu": [list(q) for q in traseu],
                   "cabluri": lant["cabluri"], "taiat": lant["taiat"]}
    alt = [{"de_la": n2, "lungime_m": l2, "motiv": f"mai lung cu {l2 - L:.0f} m" if l2 > L + 0.5 else "la fel de lung, dar cu cost mai mare",
            "traseu": [list(q) for q in t2]} for c2, n2, l2, t2, _ in rezultate[1:]]
    alt += [{"de_la": n2, "lungime_m": round(dist_m(tinta, p2), 1), "motiv": m, "traseu": [list(p2), list(tinta)]} for n2, p2, m in fara]
    out["alternative"] = alt
    f = factor(L)
    out["factor"] = f
    out["acuratete"] = round(plaf_s * f, 3)
    out["acuratete_stalpi"] = round(min(out["acuratete"], plaf_a), 3)
    n_noi, reut = len(lant["stalpi_noi"]), lant["reutilizati"]
    out["explicatie"] = [
        f"Am găsit {n_raza} stâlpi în {a['raza_cautare_m']:g} m și am verificat cei mai apropiați {len(cand)}.",
        (f"Drumul pe {' și '.join(nume) if len(nume) < 3 else ', '.join(nume[:-1]) + ' și ' + nume[-1]} e cel mai scurt ({L:g} m)."
         if nume else f"Drumul pe străzi fără nume în OSM e cel mai scurt ({L:g} m)."),
        f"Am pus {_stalpi(n_noi)} la cel mult {a['pas_stalp_m']:g} m"
        + (f"; am refolosit {', '.join(reut)}." if reut else "; nu am refolosit niciun stâlp existent.")
        + (" Lanțul a fost tăiat la limita zonei prototipului." if lant["taiat"] else "")]
    return out
