# -*- coding: utf-8 -*-
"""dvig.py — минутен двигател за ДВЕТЕ ПОСОКИ + базата + бутстрапът по ден.

Написан наново (не обвивка над gh._one_trade), защото gh._one_trade прави
`.tolist()` на целия петдневен прозорец при ВСЯКА сделка — при 6846 реални и
82 152 слепи сделки това е часове. Тук прозорецът се строи ВЕДНЪЖ на вход и
всяка геометрия го пита с двоично търсене.

ЧЕСТНОСТ: sverka.py го сравнява РЕД ПО РЕД с gh._one_trade върху всичките 6846
реални и 8000 слепи входа — 0 разминавания по net, kind и exit_index са условие
преди което и да е число оттук да се вярва.

Знаковият трик: работим в u = s·цена (s=+1 лонг, −1 шорт). Тогава и стопът, и
целите, и правилото «гап пълни на open» имат ЕДНА форма за двете посоки.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
CACHE = TUK / "_cache"
SLIP_PER_TRADE = 0.02
GEOM = {"name": "доставената 7.5/12/20 · стоп 20 · по 1/3 · BE след ТП1",
        "tps": [(1 / 3, 7.5), (1 / 3, 12.0), (1 / 3, 20.0)],
        "sl": 20.0, "be_after_tp1": True, "days": 5}


def лог(*a):
    print(*a, flush=True)


# --------------------------------------------------------------------- лента
def лента(use_cache=True):
    keys = ("ob", "oa", "ha", "la", "ca", "cb", "hb", "lb", "dord", "tsmin")
    if use_cache and all((CACHE / (k + ".npy")).exists() for k in keys):
        t0 = time.time()
        B = {k: np.load(CACHE / (k + ".npy")) for k in keys}
        лог("[лента] кеш %s бара (%.1fs)" % (format(len(B["ob"]), ","), time.time() - t0))
        return B
    sys.path.insert(0, str(IZM))
    import geom_harness as gh
    B0 = gh.load_tape()
    CACHE.mkdir(parents=True, exist_ok=True)
    B = {}
    for k in keys:
        B[k] = np.ascontiguousarray(B0[k])
        np.save(CACHE / (k + ".npy"), B[k])
    return B


def дни_индекс(B):
    d = B["dord"]
    nd = int(d[-1]) + 1
    st = np.searchsorted(d, np.arange(nd), "left")
    en = np.searchsorted(d, np.arange(nd), "right")
    return st, en


# --------------------------------------------------------------------- прозорец
class _Ctx:
    __slots__ = ("F", "A", "O", "m", "_c")

    def __init__(self, F, A, O):
        self.F = F; self.A = A; self.O = O; self.m = len(F); self._c = {}

    def _acc(self, k0):
        c = self._c.get(k0)
        if c is None:
            c = (np.maximum.accumulate(self.F[k0:]), np.minimum.accumulate(self.A[k0:]))
            self._c[k0] = c
        return c

    def first_F_ge(self, k0, X):
        if k0 >= self.m:
            return -1
        cmx, _ = self._acc(k0)
        i = int(np.searchsorted(cmx, X, "left"))
        return k0 + i if i < len(cmx) else -1

    def first_A_le(self, k0, Y):
        if k0 >= self.m:
            return -1
        _, cmn = self._acc(k0)
        i = int(np.searchsorted(-cmn, -Y, "left"))
        return k0 + i if i < len(cmn) else -1


def прозорец(i0, B, days=5):
    dord = B["dord"]; n = len(dord)
    a = i0 + 1
    b = int(np.searchsorted(dord, dord[i0] + days, "left"))
    return a, min(b, n)


def ctx_за(i0, посока, B, ab=None):
    a, b = ab if ab is not None else прозорец(i0, B)
    if a >= b:
        return None, (a, b)
    if посока == "long":            # изходите яздят BID
        F = B["hb"][a:b]; A = B["lb"][a:b]; O = B["ob"][a:b]
        return _Ctx(F, A, O), (a, b)
    F = -B["la"][a:b]; A = -B["ha"][a:b]; O = -B["oa"][a:b]   # шортът — ASK, огледално
    return _Ctx(F, A, O), (a, b)


def една(i0, посока, entry_px, geom, B, ctx=None, ab=None):
    """Огледало на gh._one_trade за двете посоки. Връща dict или None."""
    s = 1.0 if посока == "long" else -1.0
    n = len(B["dord"])
    if ctx is None:
        ctx, ab = ctx_за(i0, посока, B)
    a, b = ab
    if ctx is None or a >= b:
        return None
    F, A, O, m = ctx.F, ctx.A, ctx.O, ctx.m

    tps = geom["tps"]
    e = s * entry_px
    Ls = [e + dist for _f, dist in tps]                 # цели в знаково пространство
    cur = e - geom["sl"]                                # стоп в знаково пространство
    be = geom["be_after_tp1"]

    gross = 0.0; rem = 1.0; n_tp = 0; n_fills = 0
    exit_k = None; kind = None
    k0 = 0; ti = 0
    while True:
        ks = ctx.first_A_le(k0, cur)
        kt = ctx.first_F_ge(k0, Ls[ti]) if ti < len(Ls) else -1
        if ks != -1 and (kt == -1 or ks <= kt):
            o = O[ks]
            px = o if o <= cur else cur                 # гап през нивото пълни на open
            gross += rem * (px - e)
            rem = 0.0; n_fills += 1; exit_k = ks
            kind = ("stop" if n_tp == 0 else
                    ("be-stop-after-tp%d" % n_tp if be else "stop-after-tp%d" % n_tp))
            break
        if kt == -1:
            break
        o = O[kt]; f = F[kt]
        while ti < len(Ls) and f >= Ls[ti]:
            px = o if o >= Ls[ti] else Ls[ti]
            gross += tps[ti][0] * (px - e)
            rem -= tps[ti][0]
            if ti == 0 and be:
                cur = e                                 # BE — важи от СЛЕДВАЩИЯ бар
            ti += 1; n_tp += 1; n_fills += 1
        if rem <= 1e-12:
            exit_k = kt; kind = "tp%d" % len(tps)
            break
        k0 = kt + 1
        if k0 >= m:
            break

    if exit_k is None:
        if b < n:
            o_exit = B["ob"][b] if s == 1 else B["oa"][b]
            exit_idx = b
        else:
            o_exit = B["cb"][n - 1] if s == 1 else B["ca"][n - 1]
            exit_idx = n - 1
        gross += rem * (s * o_exit - e)
        n_fills += 1
        kind = "time-after-tp%d" % n_tp if n_tp else "time"
    else:
        exit_idx = a + exit_k
    return {"exit_index": int(exit_idx), "gross": gross,
            "net": gross - SLIP_PER_TRADE,
            "n_fills": n_fills, "kind": kind, "n_tp": n_tp}


def мнозина(idxs, посоки, pxs, B, geom=GEOM, want=("net",)):
    """Всички входове, една геометрия. Връща dict от вектори."""
    ne = len(idxs)
    out = {w: np.full(ne, np.nan, dtype=object if w == "kind" else float) for w in want}
    for p in range(ne):
        r = една(int(idxs[p]), посоки[p], float(pxs[p]), geom, B)
        if r is None:
            continue
        for w in want:
            out[w][p] = r[w]
    return out


# --------------------------------------------------------------------- базата
def слепи_индекси(idxs, B, ndraw=15, seed=20260902):
    """Случаен момент ВЪТРЕ В СЪЩИЯ търговски ден като всеки реален вход."""
    st, en = дни_индекс(B)
    d = B["dord"][idxs]
    lo = st[d].astype(np.int64); hi = en[d].astype(np.int64)
    rng = np.random.default_rng(seed)
    u = rng.random((ndraw, len(idxs)))
    return (lo + (u * (hi - lo)).astype(np.int64)).astype(np.int64)


def слепи_нета(idxs, посоки, B, ndraw=15, seed=20260902, geom=GEOM):
    """(ndraw, ne) нета на слепите входове: същият ден, същата посока, същата
    геометрия, вход на СЪЩАТА страна на спреда."""
    bidx = слепи_индекси(idxs, B, ndraw=ndraw, seed=seed)
    ne = len(idxs); nd = bidx.shape[0]
    out = np.full((nd, ne), np.nan)
    for p in range(ne):
        dr = посоки[p]
        for q in range(nd):
            i0 = int(bidx[q, p])
            px = B["oa"][i0] if dr == "long" else B["ob"][i0]
            r = една(i0, dr, float(px), geom, B)
            if r is not None:
                out[q, p] = r["net"]
    return out, bidx


# --------------------------------------------------------------------- бутстрап
class Бут:
    """ЕДИН набор преизбрани търговски дни, споделен от всички сравнения —
    само така сдвояването се пази и интервалите са съпоставими."""

    def __init__(self, dayid, reps=4000, seed=424242):
        self.u, self.inv = np.unique(dayid, return_inverse=True)
        self.k = len(self.u)
        rng = np.random.default_rng(seed)
        self.iz = rng.integers(0, self.k, size=(reps, self.k))
        self.reps = reps

    def средно(self, v):
        """Средно на вектор по вход, с 95% интервал (блоков бутстрап по ден)."""
        ok = np.isfinite(v)
        if ok.sum() == 0:
            return np.nan, np.nan, np.nan, 0
        S = np.bincount(self.inv[ok], weights=v[ok], minlength=self.k)
        C = np.bincount(self.inv[ok], minlength=self.k).astype(float)
        bm = S[self.iz].sum(1) / np.maximum(C[self.iz].sum(1), 1)
        return (float(v[ok].mean()), float(np.percentile(bm, 2.5)),
                float(np.percentile(bm, 97.5)), int(ok.sum()))

    def отношение(self, num, den):
        """Средно на num, претеглено с den: sum(num)/sum(den) + интервал.
        Ползва се за «на единица риск»."""
        ok = np.isfinite(num) & np.isfinite(den)
        if ok.sum() == 0:
            return np.nan, np.nan, np.nan, 0
        S = np.bincount(self.inv[ok], weights=num[ok], minlength=self.k)
        D = np.bincount(self.inv[ok], weights=den[ok], minlength=self.k)
        bm = S[self.iz].sum(1) / np.maximum(D[self.iz].sum(1), 1e-12)
        return (float(num[ok].sum() / den[ok].sum()), float(np.percentile(bm, 2.5)),
                float(np.percentile(bm, 97.5)), int(ok.sum()))


def звезда(lo, hi):
    if not np.isfinite(lo) or not np.isfinite(hi):
        return "—"
    if lo > 0:
        return "ДОКАЗАНО+"
    if hi < 0:
        return "ДОКАЗАНО−"
    return "недоказано"
