# -*- coding: utf-8 -*-
"""
AERO ВЕРОЯТНОСТ · тестът на близнака за бота.   python test_twin.py   (изход 0 = всичко минава)

 1. ВЕКТОРИТЕ — всичките от test_vectors.json (търси се до този файл и в папката над него),
    всяко поле с |разлика| ≤ 1e-6. ЕДНО обявено правило, не списък: условната средна на изход по
    време (izhodi.*.poziciya / zakon на cel*_vreme и vreme_*) е E[m_T; U]/P(U) — отношение на две
    разлики на вероятности O(1). Абсолютният шум на E[m_T; U] е ~1e-13 (мерено в т. 3: ≤ 6e-13 в 160
    случайни стълби), значи точността на средната е 1e-13/p. Затова допускът ѝ е max(1e-6, 1e-11/p)
    (×17 запас) — при p ≥ 1e-5 това е пак 1e-6. Нужно е само при вектор 39 (T = 1440, маса ~1e-10):
    самият еталон мърда там с ~1e-3, щом erfc му се смени с math.erfc (разлика < 2e-15) — т. 1б.
    В очакването такова поле влиза като p·стойност (< 1e-8 пипса), тоест не мести нищо.
 2. ТЕОРЕМИТЕ — позицията губи точно s (всяко T, всяко правило за входа), сборът на изходите е 1,
    образи = Фурие, затворените числа от SPEC §4, E[τ] = p·E|цел + (1−p)·E|стоп, erfc_prenosim.
 3. СВЕРКАТА С ЕТАЛОНА (ако aero_veroyatnost_ref.py е наблизо) — случайни случаи, ≤ 1e-9
    (условните средни — по същото правило: max(1e-9, 1e-11/p)).
 4. ОБВИВКАТА — veroyatnost() върху свещи във формата на `_yf("GC=F", "7d", "1m")` на бота
    (наивно UTC, Open/High/Low/Close/Volume, паузата на CME, уикенд, гапове, NaN, плоски свещи,
    счупен ред, незавършена последна свещ, MultiIndex на yfinance, tz-aware индекс, масив),
    петте състояния, БЕЗ_ДАННИ без гърмене, JSON, профилите, бързината.
 5. МУТАЦИИТЕ — 7 умишлени повреди в близнака; всяка трябва да бъде хваната от векторите.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys
import time
from datetime import datetime, timezone

import numpy as np

try:  # конзолата на Windows е cp1252 — кирилицата иска utf-8
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

TUK = os.path.dirname(os.path.abspath(__file__))
INF = math.inf


def _zaredi(ime, pat):
    spec = importlib.util.spec_from_file_location(ime, pat)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


TW = _zaredi("aero_veroyatnost", os.path.join(TUK, "aero_veroyatnost.py"))


def _nameri(ime):
    for p in (os.path.join(TUK, ime), os.path.join(os.path.dirname(TUK), ime)):
        if os.path.exists(p):
            return p
    return None


# ── броячът ────────────────────────────────────────────────────────────
class Broi:
    def __init__(self):
        self.ok = 0
        self.zle = []

    def ck(self, ime, uslovie, podrobno=""):
        if uslovie:
            self.ok += 1
        else:
            self.zle.append("%s %s" % (ime, podrobno))
            print("  ✗ %s %s" % (ime, podrobno))
        return bool(uslovie)


B = Broi()


# ══════════════════════════════════════════════════════════════════════
# 1 · ВЕКТОРИТЕ
# ══════════════════════════════════════════════════════════════════════
def _vh(x):
    return INF if x == "inf" else (-INF if x == "-inf" else x)


def _izpalni(M, v):
    """Изпълнява вектора v с модула M → изходът във формата на вектора."""
    fn, I = v["fn"], {k: _vh(x) for k, x in v["in"].items()}
    if fn == "erfc_prenosim":
        return {"erfc": M.erfc_prenosim(I["x"])}
    if fn == "p_first":
        return {"p": M.p_first(I["X"], I["Y"], I["s"])}
    if fn == "p_within":
        a = (I["X"], I["Y"], I["s"], I["sigma"], I["T"])
        return {"p_first_within": M.p_first_within(*a), "p_stop_within": M.p_stop_within(*a),
                "p_none_within": M.p_none_within(*a)}
    if fn == "exp_time":
        g, d = M.exp_time_cond(I["X"], I["Y"], I["s"], I["sigma"])
        return {"exp_time": M.exp_time(I["X"], I["Y"], I["s"], I["sigma"]), "ako_cel": g, "ako_stop": d}
    if fn == "ladder":
        L = M.ladder(I["tp1"], I["tp2"], I["tp3"], I["sl"], s=I["s"], sigma=I["sigma"], T=I["T"],
                     be_at=I["be_at"])
        o = {k: L[k] for k in ("p", "po_zakona", "E_zakon", "E_poziciya", "uspevaemost", "nuzhna_zakon",
                               "nuzhna_poziciya", "vremena_bez_tavan")}
        o["izhodi"] = {i["kod"]: {"p": i["p"], "zakon": i["zakon"], "poziciya": i["poziciya"]}
                       for i in L["izhodi"]}
        return o
    if fn == "sigma_per_min":
        oh = [[float("nan") if x is None else x for x in red] for red in I["ohlc"]]
        r = M.sigma_per_min(oh, minuti=I["minuti"], polu_zhivot=I["polu_zhivot"], metod=I["metod"])
        return {k: r[k] for k in v["out"]}
    if fn == "verdict":
        r = M.verdict(**I)
        return {k: r[k] for k in v["out"]}
    raise KeyError(fn)


def _plosko(x, put=""):
    if isinstance(x, dict):
        for k, w in x.items():
            yield from _plosko(w, put + "." + str(k))
    elif isinstance(x, list) and not all(isinstance(e, str) for e in x):
        for i, w in enumerate(x):
            yield from _plosko(w, "%s[%d]" % (put, i))
    else:
        yield put, x


PRAG = 1e-6
SHUM_ABS = 1e-11          # шумът на E[m_T; U]: мерено ≤ 6e-13 (т. 3, 160 стълби) → ×17 запас


def _dopusk(put, izhod):
    """(допуск, условна ли е): 1e-6; условната средна на изход по време — max(1e-6, 1e-11/p)."""
    chasti = put.split(".")
    if len(chasti) == 4 and chasti[1] == "izhodi" and chasti[3] in ("poziciya", "zakon"):
        kod = chasti[2]
        if kod.endswith("_vreme") or kod.startswith("vreme_"):
            p = izhod.get("izhodi", {}).get(kod, {}).get("p")
            if isinstance(p, float) and p > 0.0:
                return max(PRAG, SHUM_ABS / p), True
    return PRAG, False


def sravni_vektor(v, izhod):
    """→ (брой полета, лоши [(поле, очаквано, получено, допуск)], най-голяма разлика, ползвани изключения)."""
    E = dict(_plosko(v["out"]))
    G = dict(_plosko(izhod))
    losh, mx, izkl = [], 0.0, []
    if set(E) != set(G):
        return len(E), [("ключове", sorted(set(E) ^ set(G)), None, None)], INF, izkl
    for put, e in E.items():
        g = G[put]
        e = _vh(e) if isinstance(e, str) else e
        if isinstance(e, bool) or isinstance(g, bool):
            if e != g:
                losh.append((put, e, g, 0))
            continue
        if isinstance(e, (int, float)) and isinstance(g, (int, float)):
            if math.isinf(e) or math.isinf(g):
                if e != g:
                    losh.append((put, e, g, 0))
                continue
            d = abs(float(e) - float(g))
            dop, e_usl = _dopusk(put, izhod)
            if e_usl and d > PRAG:
                izkl.append((put, e, g, dop))         # правилото е потрябвало
            else:
                mx = max(mx, d)
            if d > dop:
                losh.append((put, e, g, dop))
        elif e != g:
            losh.append((put, e, g, None))
    return len(E), losh, mx, izkl


def proveri_vektori(M, tiho=False):
    pat = _nameri("test_vectors.json")
    if pat is None:
        raise SystemExit("test_vectors.json не е намерен (до теста или папката над него)")
    with open(pat, encoding="utf-8") as fh:
        dok = json.load(fh)
    n_v = n_pol = 0
    losh_v, mx, izkl_vs = [], 0.0, []
    for v in dok["vektori"]:
        try:
            izh = _izpalni(M, v)
            n, losh, m, izkl = sravni_vektor(v, izh)
        except Exception as e:
            n, losh, m, izkl = 1, [("гръмна", type(e).__name__, str(e)[:80], None)], INF, []
        n_v += 1
        n_pol += n
        mx = max(mx, m)
        izkl_vs += [(v["id"],) + x for x in izkl]
        if losh:
            losh_v.append((v["id"], v["fn"], losh))
            if not tiho:
                for x in losh[:4]:
                    print("  ✗ вектор %d (%s) %s: очаквано %r, получено %r, допуск %r" % ((v["id"], v["fn"]) + x))
    return {"n": n_v, "n_poleta": n_pol, "losh": losh_v, "max": mx, "izkl": izkl_vs, "pat": pat,
            "broy_v_faila": dok.get("broy")}


def shum_na_etalona(R):
    """1б · мери колко мърда самият еталон по полетата с изключението при смяна на erfc с math.erfc."""
    orig = R._erfc_np

    def stalba(erfc):
        R._erfc_np = erfc
        try:
            return {i["kod"]: i for i in R.ladder(50, 100, 130, 130, s=5.04, sigma=10.0, T=1440.0)["izhodi"]}
        finally:
            R._erfc_np = orig
    i0 = stalba(orig)
    i1 = stalba(lambda x: np.array([math.erfc(t) for t in np.asarray(x, dtype=float).ravel()]).reshape(np.shape(x)))
    i2 = stalba(lambda x: orig(x) * (1.0 + 1e-15))
    izh = {}
    for kod in ("cel2_vreme", "cel1_vreme", "vreme_predi_cel"):
        a, b, c = i0[kod]["poziciya"], i1[kod]["poziciya"], i2[kod]["poziciya"]
        izh[kod] = (i0[kod]["p"], a, b, c, max(abs(a - b), abs(a - c)))
    return izh


def chast1(R):
    print("\n1 · ВЕКТОРИТЕ")
    r = proveri_vektori(TW)
    print("  файл: %s · %d вектора (в заглавието: %s) · %d полета" % (r["pat"], r["n"], r["broy_v_faila"],
                                                                      r["n_poleta"]))
    B.ck("1 всички вектори се изпълняват и съвпадат", not r["losh"], "(лоши: %s)" % [x[0] for x in r["losh"]])
    B.ck("1 броят е 53", r["n"] == 53 and r["broy_v_faila"] == 53, str(r["n"]))
    print("  най-голяма разлика (строгите полета, допуск 1e-6): %.2e" % r["max"])
    B.ck("1 строгите полета ≤ 1e-6", r["max"] <= PRAG, "%.3e" % r["max"])
    for vid, put, e, g, dop in r["izkl"]:
        print("  ⚠ вектор %d %s: еталон %.6f · близнак %.6f · |разлика| %.2e ≤ допуск %.2e (условна средна)"
              % (vid, put, e, g, abs(e - g), dop))
    B.ck("1 правилото за условните средни е потрябвало за ≤ 2 полета", len(r["izkl"]) <= 2,
         str(len(r["izkl"])))
    if R is not None:
        print("  1б · шумът на САМИЯ еталон, T = 1440, σ = 10, s = 5,04 (erfc → math.erfc · erfc × (1 + 1e-15)):")
        sh = shum_na_etalona(R)
        for kod, (p, a, b, c, d) in sh.items():
            print("     %-16s маса %.3e · %.6f → %.6f · %.6f · мърда с до %.2e" % (kod, p, a, b, c, d))
        B.ck("1б еталонът сам мърда условните средни с > 1e-6 (правилото е оправдано)",
             sh["cel2_vreme"][4] > 1e-6 and sh["cel1_vreme"][4] > 1e-6,
             "%.2e / %.2e" % (sh["cel2_vreme"][4], sh["cel1_vreme"][4]))
        for vid, put, e, g, dop in r["izkl"]:
            kod = put.split(".")[2]
            B.ck("1б разликата близнак–еталон (%s) е от реда на шума на еталона" % kod,
                 abs(e - g) <= 3.0 * sh.get(kod, (0, 0, 0, 0, 0))[4] + PRAG, "%.2e" % abs(e - g))
    return r


# ══════════════════════════════════════════════════════════════════════
# 2 · ТЕОРЕМИТЕ
# ══════════════════════════════════════════════════════════════════════
def chast2():
    print("\n2 · ТЕОРЕМИТЕ")
    mx_m = mx_s = 0.0
    for s in (0.0, 4.56, 5.04, 7.21):
        for sig in (4.0, 10.0, 25.0):
            for T in (15.0, 60.0, 240.0, INF):
                for be in (None, 40.0):
                    L = TW.ladder(50, 100, 130, 130, s=s, sigma=sig, T=T, be_at=be)
                    mx_m = max(mx_m, abs(L["E_poziciya"] + s))
                    mx_s = max(mx_s, abs(1.0 - math.fsum(L["po_zakona"].values())))
    print("  позицията = −s: max |E_poz + s| = %.2e (96 случая) · сборът на изходите: max |1 − Σ| = %.2e"
          % (mx_m, mx_s))
    B.ck("2 позицията губи точно s", mx_m < 1e-9, "%.2e" % mx_m)
    B.ck("2 сборът на изходите е 1", mx_s < 1e-9, "%.2e" % mx_s)

    mx_f = 0.0
    for tau in (0.02, 0.05, 0.1, 0.3, 0.5, 1.0, 2.0, 3.0):
        for a, b in ((55.04, 124.96), (30.0, 100.0), (50.0, 50.0), (135.04, 124.96)):
            sig = 10.0
            T = tau * (a + b) ** 2 / sig ** 2
            o = TW._dve_bariery(a, b, sig, T, "obrazi")
            f = TW._dve_bariery(a, b, sig, T, "furie")
            mx_f = max(mx_f, max(abs(x - y) for x, y in zip(o, f)))
    print("  образи срещу Фурие (τ 0,02…3): max разлика %.2e" % mx_f)
    B.ck("2 образи = Фурие", mx_f < 1e-12, "%.2e" % mx_f)

    # SPEC §4 (T = ∞): P(ТП1) = (130 − s)/180 · P(ТП3) = P(ТП1)·50/130 · E_закон = P(ТП1)·c − 130·P(стоп)
    c_zakon = 3 * 50 - 50 ** 2 / 100 - 50 * 100 / 130
    tabl = {0.0: 26.389, 4.56: 20.903, 5.04: 20.326, 6.58: 18.473, 6.90: 18.088, 7.21: 17.715}
    mx_z = 0.0
    for s, Ez in tabl.items():
        L = TW.ladder(50, 100, 130, 130, s=s, sigma=10.0, T=INF)
        p1 = (130 - s) / 180
        mx_z = max(mx_z, abs(L["p"]["tp1"] - p1), abs(L["p"]["tp3"] - p1 * 50 / 130),
                   abs(L["E_zakon"] - (p1 * c_zakon - 130 * (1 - p1))), abs(round(L["E_zakon"], 3) - Ez))
    print("  SPEC §4 (6 реда на таблицата): max разлика %.2e · c_закон = %.3f" % (mx_z, c_zakon))
    B.ck("2 таблицата на SPEC §4", mx_z < 1e-9, "%.2e" % mx_z)
    L = TW.ladder(50, 100, 130, 130, s=5.04, sigma=10.0, T=INF, be_at=40.0)
    B.ck("2 «+40 → вход» при s = 5,04: E закон +16,446", abs(L["E_zakon"] - 16.446) < 5e-4, str(L["E_zakon"]))
    B.ck("2 нужната успеваемост 0,6004 / 0,7222",
         abs(TW.ladder(s=0.0, sigma=10.0)["nuzhna_zakon"] - 130 / (130 + c_zakon)) < 1e-12
         and abs(TW.ladder(s=5.04, sigma=10.0)["nuzhna_poziciya"] - 130 / 180) < 1e-12)

    mx_t = 0.0
    for s, sig in ((5.04, 10.0), (7.21, 6.0), (0.0, 20.0)):
        p = TW.p_first(50, 130, s)
        g, d = TW.exp_time_cond(50, 130, s, sig)
        mx_t = max(mx_t, abs(p * g + (1 - p) * d - TW.exp_time(50, 130, s, sig)))
    B.ck("2 E[τ] = p·E|цел + (1−p)·E|стоп", mx_t < 1e-9, "%.2e" % mx_t)

    xs = np.concatenate([np.linspace(0, 9, 3001), np.linspace(2.95, 3.05, 201), [-0.3, -1.7, -4.0, 26.5, 30.0]])
    mx_e = max(abs(TW.erfc_prenosim(x) - math.erfc(x)) for x in xs)
    print("  erfc_prenosim срещу math.erfc: %.2e" % mx_e)
    B.ck("2 erfc_prenosim < 2e-15", mx_e < 2e-15, "%.2e" % mx_e)
    B.ck("2 lošo: s ≥ Y → ValueError", _grymi(lambda: TW.p_first(50, 130, 130)))
    B.ck("2 lošo: s < 0 → ValueError", _grymi(lambda: TW.p_first(50, 130, -1)))


def _grymi(f):
    try:
        f()
    except ValueError:
        return True
    return False


# ══════════════════════════════════════════════════════════════════════
# 3 · СВЕРКАТА С ЕТАЛОНА (случайни случаи)
# ══════════════════════════════════════════════════════════════════════
def chast3(R):
    print("\n3 · СВЕРКАТА С ЕТАЛОНА")
    if R is None:
        print("  еталонът не е наблизо — пропускам (в репото на бота това е нормално)")
        return
    rng = np.random.default_rng(20261022)
    mx = {"p_within": 0.0, "ladder": 0.0, "sigma": 0.0, "verdict": 0.0}
    n = {k: 0 for k in mx}
    ne_sapada = []
    shum_mx = [0.0]
    for _ in range(400):
        X, Y = rng.uniform(10, 150), rng.uniform(20, 200)
        s = rng.uniform(0, min(10.0, Y - 1))
        sig = rng.uniform(0.5, 40.0)
        T = INF if rng.random() < 0.1 else rng.uniform(0.5, 600.0)
        for f in ("p_first_within", "p_stop_within", "p_none_within"):
            d = abs(getattr(TW, f)(X, Y, s, sig, T) - getattr(R, f)(X, Y, s, sig, T))
            mx["p_within"] = max(mx["p_within"], d)
        n["p_within"] += 1
    for _ in range(160):
        s = rng.uniform(0, 8.0)
        sig = rng.uniform(2.0, 35.0)
        T = INF if rng.random() < 0.2 else rng.uniform(5.0, 600.0)
        be = None if rng.random() < 0.6 else rng.uniform(10.0, 49.0)
        a = TW.ladder(50, 100, 130, 130, s=s, sigma=sig, T=T, be_at=be)
        b = R.ladder(50, 100, 130, 130, s=s, sigma=sig, T=T, be_at=be)
        for k in ("p", "po_zakona", "vremena_bez_tavan"):
            for kk in b[k]:
                mx["ladder"] = max(mx["ladder"], abs(a[k][kk] - b[k][kk]))
        for k in ("E_zakon", "E_poziciya", "uspevaemost", "nuzhna_zakon", "nuzhna_poziciya"):
            if b[k] is None or a[k] is None:
                if a[k] != b[k]:
                    ne_sapada.append(("ladder", k, a[k], b[k]))
                continue
            mx["ladder"] = max(mx["ladder"], abs(a[k] - b[k]))
        ia = {i["kod"]: i for i in a["izhodi"]}
        for i in b["izhodi"]:
            j = ia[i["kod"]]
            mx["ladder"] = max(mx["ladder"], abs(i["p"] - j["p"]))
            for k in ("zakon", "poziciya"):
                if i[k] is None or j[k] is None:
                    if (i[k] is None) != (j[k] is None) and max(i["p"], j["p"]) > 1e-13:
                        ne_sapada.append(("ladder", i["kod"], k, i[k], j[k], i["p"]))
                    continue
                usl = i["kod"].endswith("_vreme") or i["kod"].startswith("vreme_")
                dop = max(1e-9, SHUM_ABS / i["p"]) if (usl and i["p"] > 0) else 1e-9
                if abs(i[k] - j[k]) > dop:
                    ne_sapada.append(("ladder", i["kod"], k, i[k], j[k], i["p"]))
                if usl and i["p"] > 0:
                    shum_mx[0] = max(shum_mx[0], abs(i[k] - j[k]) * i["p"])
                else:
                    mx["ladder"] = max(mx["ladder"], abs(i[k] - j[k]))
        n["ladder"] += 1
    for _ in range(200):
        m = int(rng.integers(2, 120))
        c0 = 4130.0 + np.cumsum(rng.normal(0, 1.0, m))
        o = c0 + rng.normal(0, 0.3, m)
        c = c0 + rng.normal(0, 0.3, m)
        h = np.maximum(o, c) + np.abs(rng.normal(0, 0.4, m))
        l = np.minimum(o, c) - np.abs(rng.normal(0, 0.4, m))
        oh = np.column_stack([o, h, l, c])
        for j in rng.integers(0, m, size=int(rng.integers(0, 4))):     # капаните
            vid = rng.integers(0, 4)
            if vid == 0:
                oh[j, rng.integers(0, 4)] = np.nan
            elif vid == 1:
                oh[j] = oh[j, 3]
            elif vid == 2:
                oh[j, 1], oh[j, 2] = oh[j, 2] - 0.5, oh[j, 1] + 0.5
            else:
                oh[j, 0] = -1.0
        mn = float(rng.choice([1.0, 5.0]))
        hz = float(rng.uniform(1.0, 40.0))
        met = str(rng.choice(["gk", "parkinson"]))
        a = TW.sigma_per_min(oh, minuti=mn, polu_zhivot=hz, metod=met)
        b = R.sigma_per_min(oh, minuti=mn, polu_zhivot=hz, metod=met)
        for k in b:
            if b[k] is None or a[k] is None:
                if a[k] != b[k]:
                    ne_sapada.append(("sigma", k, a[k], b[k]))
                continue
            mx["sigma"] = max(mx["sigma"], abs(a[k] - b[k]))
        n["sigma"] += 1
    for _ in range(300):
        s = rng.uniform(0, 9.0)
        sig = rng.uniform(1.0, 40.0)
        shok = None if rng.random() < 0.3 else rng.uniform(0, 5)
        rab = None if rng.random() < 0.5 else rng.uniform(0, 10)
        a = TW.verdict(s, sig, shok=shok, rab_mid=rab)
        b = R.verdict(s, sig, shok=shok, rab_mid=rab)
        for k in b:
            if isinstance(b[k], float):
                mx["verdict"] = max(mx["verdict"], abs(a[k] - b[k]) if math.isfinite(b[k]) else
                                    (0.0 if a[k] == b[k] else INF))
            elif a[k] != b[k]:
                ne_sapada.append(("verdict", k, a[k], b[k]))
        n["verdict"] += 1
    for k in mx:
        print("  %-9s %4d случая · max разлика %.2e" % (k, n[k], mx[k]))
    print("  условните средни: шумът |разлика|·p ≤ %.2e (правилото допуска 1e-11)" % shum_mx[0])
    B.ck("3 шумът на условните средни < 1e-11", shum_mx[0] < SHUM_ABS, "%.2e" % shum_mx[0])
    for x in ne_sapada[:6]:
        print("  ✗ не съвпада:", x)
    B.ck("3 случайните случаи ≤ 1e-9", max(mx.values()) <= 1e-9 and not ne_sapada,
         "%.2e · %d несъвпадения" % (max(mx.values()), len(ne_sapada)))


# ══════════════════════════════════════════════════════════════════════
# 4 · ОБВИВКАТА — свещи във формата на бота
# ══════════════════════════════════════════════════════════════════════
def yahoo_1m(dni=7, sigma=10.0, krai="2026-10-22T09:50", seed=7, pod=8, profil=True, cena=4130.0):
    """1-минутни свещи като `_yf("GC=F", "7d", "1m")` в live_bot.py: DatetimeIndex наивно UTC (началото на
    свещта), колони Open High Low Close Volume, цена в $ с тик 0,10. Няма свещи в паузата на CME
    (21:00–21:59 UTC) и в уикенда (пт 21:00 → нд 22:00 UTC); след паузата — гап. σ (пипса/√мин) по
    часа: f(ч) = 1 + 0,5·cos(2π(ч − 13)/24) — 13 UTC е 3 пъти 01 UTC (SPEC §7). Капаните на Yahoo:
    ~1,5 % плоски свещи (H = L, обем 0), ~0,2 % NaN в Open, един счупен ред (H < L).
    Върнатото «истинско σ» е целта на EWMA: √(Σ w_k·(σ·f_k)²) с теглата на полуживот 30 свещи."""
    import pandas as pd
    rng = np.random.default_rng(seed)
    kr = pd.Timestamp(krai)
    vsichki = pd.date_range(kr - pd.Timedelta(days=dni), kr, freq="1min")
    ch = vsichki.hour
    dn = vsichki.dayofweek                               # пн = 0 … нд = 6
    zatv = (ch == 21) | (dn == 5) | ((dn == 4) & (ch >= 21)) | ((dn == 6) & (ch < 22))
    t = vsichki[~zatv]
    f = 1.0 + 0.5 * np.cos(2 * np.pi * (t.hour.values + t.minute.values / 60.0 - 13.0) / 24.0) if profil \
        else np.ones(len(t))
    sig_t = sigma * f * PIP_D                           # $ на √мин
    n = len(t)
    dt_sig = sig_t[:, None] / math.sqrt(pod)                   # σ√dt на под-стъпка ($)
    stapki = rng.normal(0.0, 1.0, (n, pod)) * dt_sig
    put = np.cumsum(stapki, axis=1)
    pred = np.concatenate([np.zeros((n, 1)), put[:, :-1]], axis=1)
    # връх/дъно на брауновия мост между под-стъпките (точни, както в mc_proverka.py — сделките на CME
    # са гъсти, значи H/L на Yahoo са почти непрекъснати): (x0 + x1 ± √((x1 − x0)² − 2σ²dt·ln U))/2
    shir = lambda: np.sqrt(stapki ** 2 - 2.0 * dt_sig ** 2 * np.log(rng.random((n, pod))))
    vrah = (pred + put + shir()) / 2.0
    dano = (pred + put - shir()) / 2.0
    nachalo = np.empty(n)
    p = cena
    gap = np.zeros(n, dtype=bool)
    gap[1:] = np.diff(t.values).astype("timedelta64[m]").astype(int) > 1
    for i in range(n):
        if gap[i]:
            p += rng.normal(0.0, 3.0)                    # гап след паузата (~30 пипса)
        nachalo[i] = p
        p = p + put[i, -1]
    o = nachalo
    c = nachalo + put[:, -1]
    h = np.maximum(nachalo + vrah.max(axis=1), np.maximum(o, c))
    l = np.minimum(nachalo + dano.min(axis=1), np.minimum(o, c))
    tik = lambda x: np.round(x, 1)                      # тик 0,10 $
    df = pd.DataFrame({"Open": tik(o), "High": tik(h), "Low": tik(l), "Close": tik(c),
                       "Volume": rng.integers(5, 400, n)}, index=pd.DatetimeIndex(t, name="Datetime"))
    plo = rng.random(n) < 0.015
    df.loc[plo, ["Open", "High", "Low"]] = np.repeat(df.loc[plo, "Close"].values[:, None], 3, axis=1)
    df.loc[plo, "Volume"] = 0
    nan = rng.random(n) < 0.002
    df.loc[nan, "Open"] = np.nan
    j = n // 3
    df.iloc[j, 1], df.iloc[j, 2] = df.iloc[j, 2] - 0.5, df.iloc[j, 1] + 0.5     # счупен ред
    lam = 0.5 ** (1.0 / 30.0)
    w = lam ** np.arange(600)[::-1]
    return df, float(np.sqrt(np.sum(w * (sigma * f[-600:]) ** 2) / np.sum(w)))


PIP_D = 0.10


def chast4():
    print("\n4 · ОБВИВКАТА (свещи във формата на бота)")
    import pandas as pd
    df, sig_ist = yahoo_1m()
    sega = "2026-10-22T10:00:20"                         # Yahoo GC=F закъснява ~10 мин (паметта, 07.10)
    rez = TW.veroyatnost(df, 5.04, None, now_utc=sega, strogo=True)
    sg = rez["sigma"]
    print("  %d свещи (7 дни, без паузите) · истинско σ (целта на EWMA) %.3f · оценено %.3f (%+.1f%%) · шок %.2f · "
          "възраст %.1f мин" % (len(df), sig_ist, sg["sigma"], 100 * (sg["sigma"] / sig_ist - 1), sg["shok"],
                                sg["vazrast_min"]))
    B.ck("4 σ в рамките на 10% от истинското", abs(sg["sigma"] / sig_ist - 1) < 0.10,
         "%.3f срещу %.3f" % (sg["sigma"], sig_ist))
    B.ck("4 прозорецът е 600 свещи", sg["n_v_prozoreca"] == 600, str(sg["n_v_prozoreca"]))
    B.ck("4 възрастта ≈ 9,3 мин, не е старо", abs(sg["vazrast_min"] - 560.0 / 60.0) < 1e-9
         and sg["staro"] is False, str(sg["vazrast_min"]))
    print("  присъда: %s %s · P(ТП1 до 60) %.4f · P(стоп до 5) %.6f · E закон %+.3f · E бот %+.3f · E поз %+.3f · "
          "%.1f мс" % (rez["sastoyanie"], rez["vsichki"], rez["do_T"]["60"]["tp1"], rez["do_T"]["5"]["stop"],
                       rez["stalba"]["inf"]["E_zakon"], rez["stalba_bot"]["inf"]["E_zakon"],
                       rez["stalba"]["inf"]["E_poziciya"], rez["ms"]))
    B.ck("4 при σ≈10 и s=5,04 → ЧИСТО", rez["sastoyanie"] == "ЧИСТО", str(rez["vsichki"]))
    B.ck("4 математиката без ръб е «срещу», net = −s", rez["matematika"] == "срещу" and rez["net"] == -5.04)

    # числата на обвивката = функциите
    sig = sg["sigma"]
    sver = [abs(rez["do_T"]["60"]["tp1"] - TW.p_first_within(50, 130, 5.04, sig, 60)),
            abs(rez["do_T"]["5"]["stop"] - TW.p_stop_within(50, 130, 5.04, sig, 5)),
            abs(rez["stalba"]["240"]["E_zakon"] - TW.ladder(s=5.04, sigma=sig, T=240)["E_zakon"]),
            abs(rez["stalba_bot"]["inf"]["E_zakon"] - TW.ladder(s=2.52, sigma=sig)["E_zakon"]),
            abs(rez["prisada"]["p_tp1_do_T"] - TW.verdict(5.04, sig, shok=sg["shok"])["p_tp1_do_T"])]
    B.ck("4 числата на обвивката = функциите", max(sver) == 0.0, str(max(sver)))
    mx_m = max(abs(v["E_poziciya"] + 5.04) for v in rez["stalba"].values())
    B.ck("4 теоремата и в обвивката (∞, 60, 240): E_поз = −s", mx_m < 1e-9, "%.2e" % mx_m)
    B.ck("4 броенето на бота (s/2): E_поз = −2,52", abs(rez["stalba_bot"]["inf"]["E_poziciya"] + 2.52) < 1e-9)

    # JSON и редът за дневника
    t = json.dumps(rez, ensure_ascii=False, allow_nan=False)
    red = TW.red_za_dnevnik(rez)
    tr = json.dumps(red, ensure_ascii=False, allow_nan=False)
    print("  JSON: пълният %d байта · редът за дневника %d байта, %d полета" % (len(t.encode()), len(tr.encode()),
                                                                              len(red)))
    B.ck("4 пълният резултат е строг JSON", t.startswith("{"))
    B.ck("4 редът е под 1,5 KB", len(tr.encode()) < 1500, str(len(tr.encode())))
    kr = TW.red_za_dnevnik(rez, kratko=True)
    tk = json.dumps(kr, ensure_ascii=False, allow_nan=False)
    print("  краткият ред («fon») %d байта, %d полета" % (len(tk.encode()), len(kr)))
    B.ck("4 краткият ред е под 400 байта и носи състоянието и свежестта", len(tk.encode()) < 400
         and kr["sastoyanie"] == rez["sastoyanie"] and kr["staro"] is False and kr["p_tp1_60"] == red["p_tp1_60"])
    B.ck("4 ред от празен резултат → БЕЗ_ДАННИ, без гърмене", TW.red_za_dnevnik(None)["sastoyanie"] == "БЕЗ_ДАННИ"
         and TW.red_za_dnevnik({}, kratko=True)["sastoyanie"] == "БЕЗ_ДАННИ")
    B.ck("4 редът носи присъдата и вероятностите",
         all(k in red for k in ("sastoyanie", "s", "sigma", "shok", "p_tp1_60", "p_stop_5", "E_zakon", "E_zakon_bot",
                                "E_poziciya", "E_zakon_240", "staro", "matematika")))

    # формите на данните — един и същ резултат
    df_mi = df.copy()
    df_mi.columns = pd.MultiIndex.from_product([list(df.columns), ["GC=F"]], names=["Price", "Ticker"])
    df_lc = df.rename(columns=str.lower)
    df_tz = df.tz_localize("UTC")
    vid = {"MultiIndex на yfinance": TW.veroyatnost(df_mi, 5.04, now_utc=sega),
           "малки букви": TW.veroyatnost(df_lc, 5.04, now_utc=sega),
           "tz-aware индекс": TW.veroyatnost(df_tz, 5.04, now_utc=sega),
           "now като datetime": TW.veroyatnost(df, 5.04, now_utc=datetime(2026, 10, 22, 13, 0, 20, tzinfo=timezone(
               __import__("datetime").timedelta(hours=3)))),
           "now като pd.Timestamp": TW.veroyatnost(df, 5.04, now_utc=pd.Timestamp(sega))}
    for ime, r in vid.items():
        B.ck("4 форма: %s → същото σ" % ime, r["sigma"]["sigma"] == sg["sigma"] and r["sastoyanie"] == rez["sastoyanie"],
             "%r срещу %r" % (r["sigma"]["sigma"], sg["sigma"]))
    r_m = TW.veroyatnost(df[["Open", "High", "Low", "Close"]].values[-700:], 5.04)
    B.ck("4 форма: масив (n, 4) без часове → същото σ", r_m["sigma"]["sigma"] == sg["sigma"]
         and r_m["sigma"]["vazrast_min"] is None, str(r_m["sigma"]["sigma"]))

    # незавършената свещ и старите данни
    r_n = TW.veroyatnost(df, 5.04, now_utc="2026-10-22T09:50:40")
    B.ck("4 незавършената последна свещ се маха", r_n["sigma"]["nezavarshena_mahnata"] is True
         and r_n["sigma"]["posledna_t"] == "2026-10-22T09:49", str(r_n["sigma"]["posledna_t"]))
    r_s = TW.veroyatnost(df, 5.04, now_utc="2026-10-22T12:00:00")
    B.ck("4 данни на 2 ч → staro", r_s["sigma"]["staro"] is True, str(r_s["sigma"]["vazrast_min"]))

    # петте състояния
    df_t, _ = yahoo_1m(sigma=4.0, profil=False, seed=11)
    r_t = TW.veroyatnost(df_t, 5.04, now_utc=sega)
    B.ck("4 σ≈4 → МЪРТВО", r_t["sastoyanie"] == "МЪРТВО", "%s σ=%.2f" % (r_t["vsichki"], r_t["sigma"]["sigma"]))
    r_k = TW.veroyatnost(df, 7.21, now_utc=sega)
    B.ck("4 s = 7,21 → СКЪПО (14,4% > 12%)", r_k["sastoyanie"] == "СКЪПО", str(r_k["vsichki"]))
    df_v = df.copy()
    posl = df_v.index[-1] + pd.Timedelta(minutes=1)
    c = float(df_v["Close"].iloc[-1])
    df_v.loc[posl] = [c, c + 10.0, c - 0.5, c + 9.0, 900]          # свещ от 105 пипса
    r_v = TW.veroyatnost(df_v, 5.04, now_utc="2026-10-22T10:01:30")
    B.ck("4 свещ от 105 пипса → ВЗРИВ (шок ≥ 3)", r_v["sastoyanie"] == "ВЗРИВ",
         "%s шок %.2f" % (r_v["vsichki"], r_v["sigma"]["shok"] or -1))
    df_b, _ = yahoo_1m(sigma=34.0, profil=False, seed=12)
    r_b = TW.veroyatnost(df_b, 5.04, now_utc=sega)
    B.ck("4 σ≈34 → ВЗРИВ от стопа (P(стоп до 5) ≥ 0,05)", r_b["sastoyanie"] == "ВЗРИВ"
         and r_b["do_T"]["5"]["stop"] >= 0.05, "%s %.4f" % (r_b["vsichki"], r_b["do_T"]["5"]["stop"]))
    print("  състояния: σ≈4 %s · s=7,21 %s · свещ 105 п %s (шок %.1f) · σ≈34 %s (P(стоп до 5) %.3f)"
          % (r_t["sastoyanie"], r_k["sastoyanie"], r_v["sastoyanie"], r_v["sigma"]["shok"], r_b["sastoyanie"],
             r_b["do_T"]["5"]["stop"]))

    # БЕЗ_ДАННИ — без гърмене
    lo = {"None": TW.veroyatnost(None, 5.04), "празен": TW.veroyatnost(pd.DataFrame(), 5.04),
          "без колони": TW.veroyatnost(pd.DataFrame({"x": [1, 2]}), 5.04),
          "всичко NaN": TW.veroyatnost(df.iloc[-50:] * np.nan, 5.04),
          "всичко плоско": TW.veroyatnost(pd.DataFrame({"Open": [4130.0] * 40, "High": [4130.0] * 40,
                                                        "Low": [4130.0] * 40, "Close": [4130.0] * 40}), 5.04),
          "спред None": TW.veroyatnost(df, None, now_utc=sega),
          "спред NaN": TW.veroyatnost(df, float("nan"), now_utc=sega),
          "спред ≥ СЛ": TW.veroyatnost(df, 150.0, now_utc=sega),
          "лош план": TW.veroyatnost(df, 5.04, {"tp1": 120, "tp2": 100}, now_utc=sega)}
    for ime, r in lo.items():
        B.ck("4 БЕЗ_ДАННИ: %s" % ime, r["sastoyanie"] == "БЕЗ_ДАННИ" and (r["prichini"] or r["greshka"]),
             "%s %s %s" % (r["sastoyanie"], r["prichini"], r["greshka"]))
        json.dumps(r, allow_nan=False)
        json.dumps(TW.red_za_dnevnik(r), allow_nan=False)
    print("  БЕЗ_ДАННИ (9 вида): %s" % "; ".join("%s → %s" % (k, (v["prichini"] or [v["greshka"]])[0][:48])
                                                 for k, v in list(lo.items())[:4]))
    r_r = TW.veroyatnost(df, None, {"spred_rezerva": 5.04}, now_utc=sega)
    B.ck("4 спредът липсва + резерва 5,04 → смята, s_izvor «rezerva»", r_r["s_izvor"] == "rezerva"
         and r_r["sastoyanie"] == rez["sastoyanie"] and r_r["s"] == 5.04)
    try:
        TW.veroyatnost(df, 150.0, now_utc=sega, strogo=True)
        strogo_ok = True                                  # спред ≥ СЛ е причина, не изключение
    except Exception:
        strogo_ok = False
    B.ck("4 strogo=True не гърми на причина (само на изключение)", strogo_ok)
    B.ck("4 strogo=True гърми на изключение", _grymi_vse(lambda: TW.veroyatnost(None, 5.04, strogo=True)))

    # планът: старото «+40 → вход» и ръбът
    r_40 = TW.veroyatnost(df, 5.04, {"be_at": 40.0}, now_utc=sega)
    B.ck("4 планът be_at = 40 стига до стълбата", r_40["stalba"]["inf"]["po_zakona"]["0"] > 0.1
         and r_40["plan"]["be_at"] == 40.0)
    r_rb = TW.veroyatnost(df, 4.56, {"rab_mid": 6.0}, now_utc=sega)
    B.ck("4 ръб 6,0 > s 4,56 → математиката «за»", r_rb["matematika"] == "за" and abs(r_rb["net"] - 1.44) < 1e-12)

    # профилите на Swissquote (форматът на `_цена_профили`)
    pr = TW.prisada_po_profili(rez, {"elite": [4129.748, 4130.252], "premium": [4129.671, 4130.329],
                                     "prime": [4129.700, 4130.300], "standard": [4129.655, 4130.345]})
    print("  профили: %s" % ", ".join("%s %.2f → %s" % (k, v["s"], v["sastoyanie"]) for k, v in pr.items()))
    B.ck("4 профилите: elite 5,04 ЧИСТО · premium 6,58 СКЪПО", pr["elite"]["sastoyanie"] == "ЧИСТО"
         and pr["premium"]["sastoyanie"] == "СКЪПО" and abs(pr["premium"]["s"] - 6.58) < 1e-9)
    B.ck("4 prime 6,00 = точно 12% → НЕ е СКЪПО (прагът е «>», без плаваща грешка)",
         pr["prime"]["sastoyanie"] == "ЧИСТО", str(pr["prime"]))
    r_6 = TW.veroyatnost(df, (4130.300 - 4129.700) / 0.1, now_utc=sega)
    B.ck("4 спред 6,000000000002 от bid/ask → s = 6,0 и ЧИСТО", r_6["s"] == 6.0 and r_6["sastoyanie"] == "ЧИСТО",
         "%r %s" % (r_6["s"], r_6["sastoyanie"]))
    r_mn = TW.veroyatnost(df, 5.04, now_utc="2026-10-22T10:00")       # `now_utc` на main(): isoformat до минутата
    B.ck("4 now_utc във формата на бота («2026-10-22T10:00») → възраст 9,0 мин",
         abs(r_mn["sigma"]["vazrast_min"] - 9.0) < 1e-9 and r_mn["sigma"]["sigma"] == sg["sigma"],
         str(r_mn["sigma"]["vazrast_min"]))
    B.ck("4 профили без σ → None", TW.prisada_po_profili(lo["None"], {"elite": [1, 2]}) is None)

    # бързината (рънът е всяка минута)
    ts = []
    for _ in range(25):
        t0 = time.perf_counter()
        TW.veroyatnost(df, 5.04, now_utc=sega)
        ts.append((time.perf_counter() - t0) * 1000)
    ts_b = []
    for sgm in (6.0, 10.0, 15.0, 20.0):
        d_s, _ = yahoo_1m(sigma=sgm, profil=False, seed=int(sgm))
        t0 = time.perf_counter()
        TW.veroyatnost(d_s, 5.04, now_utc=sega)
        ts_b.append((time.perf_counter() - t0) * 1000)
    print("  бързина: медиана %.1f мс (σ≈10, 25 пъти) · σ 6/10/15/20: %s мс"
          % (float(np.median(ts)), " / ".join("%.0f" % x for x in ts_b)))
    B.ck("4 под 250 мс на извикване (най-тежкото σ)", max(ts_b) < 250 and np.median(ts) < 250,
         "%.0f" % max(ts_b))
    return rez


def _grymi_vse(f):
    try:
        f()
    except Exception:
        return True
    return False


# ══════════════════════════════════════════════════════════════════════
# 5 · МУТАЦИИТЕ — пробата мери ли себе си
# ══════════════════════════════════════════════════════════════════════
def chast5():
    print("\n5 · МУТАЦИИТЕ (всяка повреда трябва да бъде хваната от векторите)")
    orig = {k: getattr(TW, k) for k in ("_bariery", "_obrazi", "_GRANICA_BEZKRAI", "ladder", "_K_GK", "_erfc_v",
                                        "verdict")}

    def m_spred():
        TW._bariery = lambda X, Y, s: (float(X), float(Y))

    def m_obraz():
        o = orig["_obrazi"]

        def samo_parvi(a, b, pos, Dmax):
            d, z = o(a, b, pos, Dmax)
            return d[:1], z[:1]
        TW._obrazi = samo_parvi

    def m_bez_tavan():
        TW._GRANICA_BEZKRAI = 1e9

    def m_poz():
        lf = orig["ladder"]

        def l2(*a, **k):
            r = lf(*a, **k)
            r["E_poziciya"] += 0.01
            return r
        TW.ladder = l2

    def m_gk():
        TW._K_GK = orig["_K_GK"] * 1.01

    def m_erfc():
        ef = orig["_erfc_v"]
        TW._erfc_v = lambda x: ef(x) * (1 + 1e-5)

    def m_skapo():
        vf = orig["verdict"]
        TW.verdict = lambda *a, **k: vf(*a, **dict(k, prag_skapo=k.get("prag_skapo", 0.10)))

    mutacii = (("забравен спред", m_spred), ("само първият образ", m_obraz), ("верига без таван", m_bez_tavan),
               ("позицията +0,01", m_poz), ("константата на GK ×1,01", m_gk), ("erfc × (1 + 1e-5)", m_erfc),
               ("прагът СКЪПО 10%", m_skapo))
    for ime, f in mutacii:
        try:
            f()
            r = proveri_vektori(TW, tiho=True)
            hv = len(r["losh"])
        finally:
            for k, v in orig.items():
                setattr(TW, k, v)
        print("  %-26s → хваната от %d вектора" % (ime, hv))
        B.ck("5 мутация «%s» е хваната" % ime, hv >= 1)
    r = proveri_vektori(TW, tiho=True)
    B.ck("5 след мутациите близнакът е пак чист", not r["losh"])


# ══════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description="тестът на близнака AERO ВЕРОЯТНОСТ")
    ap.add_argument("--bez-etalon", action="store_true", help="не търси aero_veroyatnost_ref.py")
    args = ap.parse_args()
    t0 = time.perf_counter()
    pat_ref = None if args.bez_etalon else _nameri("aero_veroyatnost_ref.py")
    R = _zaredi("aero_veroyatnost_ref", pat_ref) if pat_ref else None
    print("AERO ВЕРОЯТНОСТ · близнакът v%s (%s) · numpy %s · еталон: %s"
          % (TW.VERSIYA, TW.BLIZNAK, np.__version__, pat_ref or "няма"))
    chast1(R)
    chast2()
    chast3(R)
    chast4()
    chast5()
    print("\nИТОГ: %d проверки минават, %d не · %.1f с" % (B.ok, len(B.zle), time.perf_counter() - t0))
    for z in B.zle:
        print("  ✗", z)
    return 0 if not B.zle else 1


if __name__ == "__main__":
    sys.exit(main())
