# -*- coding: utf-8 -*-
"""eng.py - minute engine for the SHORT geometry search.

Written from scratch (NOT a wrapper around gh._one_trade) so that intraday
horizons are possible: geom_harness.TIME_EXIT_DAYS counts WHOLE day ordinals
(geom_harness.py:294), so every fractional value collapses to the same window.

The engine is checked line by line against gh._one_trade on DAILY windows in
sverka.py - 0 mismatches required before any number here is believed.
"""
from __future__ import annotations
import sys, time
from pathlib import Path
import numpy as np
import pandas as pd

SCRATCH = Path(r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----"
               r"\2674809c-6765-4e6e-873d-82958246267b\scratchpad")
HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
SLIP_PER_TRADE = 0.02


def log(*a):
    print(*a, flush=True)


# --------------------------------------------------------------------- tape
def tape(use_cache=True):
    """Same arrays as gh.load_tape(), cached as .npy so scripts start fast."""
    keys = ("ob", "oa", "ha", "la", "ca", "cb", "hb", "lb", "dord", "tsmin")
    if use_cache and all((CACHE / (k + ".npy")).exists() for k in keys):
        t0 = time.time()
        B = {k: np.load(CACHE / (k + ".npy")) for k in keys}
        log("[tape] cache %s bars (%.1fs)" % (format(len(B["ob"]), ","), time.time() - t0))
        return B
    sys.path.insert(0, str(HERE.parent))
    import geom_harness as gh
    B0 = gh.load_tape()
    CACHE.mkdir(parents=True, exist_ok=True)
    B = {}
    for k in keys:
        B[k] = np.ascontiguousarray(B0[k])
        np.save(CACHE / (k + ".npy"), B[k])
    np.save(CACHE / "ts.npy", B0["ts"])
    return B


def days_index(B):
    """First and last+1 bar index of every trading-day ordinal."""
    d = B["dord"]
    nd = int(d[-1]) + 1
    st = np.searchsorted(d, np.arange(nd), "left")
    en = np.searchsorted(d, np.arange(nd), "right")
    return st, en


# --------------------------------------------------------------------- geometry
def G(name, tps, sl, be_after_tp1=False, be_move=None, trail=None,
      days=5, minutes=None):
    """tps: list of (fraction, distance$) - [] means "no target, trail only".
    sl: initial stop distance $. be_after_tp1: stop -> entry after TP1.
    be_move: stop -> entry once price moved this far in favour.
    trail: trailing distance $ (stop = best price + trail, never worse than sl).
    days: horizon in WHOLE trading days (gh convention). minutes overrides days.
    """
    return {"name": name, "tps": list(tps), "sl": float(sl),
            "be_after_tp1": bool(be_after_tp1),
            "be_move": None if be_move is None else float(be_move),
            "trail": None if trail is None else float(trail),
            "days": int(days), "minutes": None if minutes is None else int(minutes)}


class _Ctx:
    """One trade window. Caches the monotone running extremes so that every
    geometry answers "first bar at/after k with high>=X / low<=Y" with a binary
    search instead of a fresh scan of the window."""
    __slots__ = ("hi", "lo", "op", "m", "_c")

    def __init__(self, hi, lo, op):
        self.hi = hi; self.lo = lo; self.op = op; self.m = len(hi); self._c = {}

    def _acc(self, k0):
        c = self._c.get(k0)
        if c is None:
            cmx = np.maximum.accumulate(self.hi[k0:])
            ncm = -np.minimum.accumulate(self.lo[k0:])
            c = (cmx, ncm)
            self._c[k0] = c
        return c

    def first_ge(self, k0, X):          # first k>=k0 with high[k] >= X
        if k0 >= self.m:
            return -1
        cmx, _ = self._acc(k0)
        i = int(np.searchsorted(cmx, X, "left"))
        return k0 + i if i < len(cmx) else -1

    def first_le(self, k0, Y):          # first k>=k0 with low[k] <= Y
        if k0 >= self.m:
            return -1
        _, ncm = self._acc(k0)
        i = int(np.searchsorted(ncm, -Y, "left"))
        return k0 + i if i < len(ncm) else -1


def window(i0, g, B):
    """[a,b) bar range, gh convention: strictly after the entry bar, up to (not
    including) the first bar of day dord[i0]+days - or, for a minute horizon,
    the first bar at/after entry+minutes."""
    dord = B["dord"]; n = len(dord)
    a = i0 + 1
    if g["minutes"] is None:
        b = int(np.searchsorted(dord, dord[i0] + g["days"], "left"))
    else:
        b = int(np.searchsorted(B["tsmin"], B["tsmin"][i0] + g["minutes"], "left"))
    return a, min(b, n)


def one_short(i0, entry_px, g, B, ctx=None, ab=None):
    """SHORT only. Exits ride the ASK. Mirrors gh._one_trade's rules: the stop is
    checked BEFORE the targets inside a bar; a gap through a level fills at the
    bar OPEN; break-even arms from the NEXT bar; the entry bar is never used."""
    n = len(B["dord"])
    a, b = ab if ab is not None else window(i0, g, B)
    if a >= b:
        return None
    if ctx is None:
        ctx = _Ctx(B["ha"][a:b], B["la"][a:b], B["oa"][a:b])
    hi, lo, op, m = ctx.hi, ctx.lo, ctx.op, ctx.m

    tps = g["tps"]; sl0 = entry_px + g["sl"]
    lv = [entry_px - d for _f, d in tps]
    gross = 0.0; rem = 1.0; n_tp = 0; n_fills = 0
    exit_k = None; kind = None

    if g["trail"] is None and g["be_move"] is None:
        # ---- fixed stop (optionally -> break-even after TP1): binary searches
        cur = sl0; k0 = 0; ti = 0
        while True:
            ks = ctx.first_ge(k0, cur)
            kt = ctx.first_le(k0, lv[ti]) if ti < len(lv) else -1
            if ks != -1 and (kt == -1 or ks <= kt):
                o = op[ks]
                px = o if o >= cur else cur
                gross += rem * -(px - entry_px)
                rem = 0.0; n_fills += 1; exit_k = ks
                kind = ("stop" if n_tp == 0 else
                        ("be-stop-after-tp%d" % n_tp if g["be_after_tp1"]
                         else "stop-after-tp%d" % n_tp))
                break
            if kt == -1:
                break
            o = op[kt]; l = lo[kt]
            while ti < len(lv) and l <= lv[ti]:
                px = o if o <= lv[ti] else lv[ti]
                gross += tps[ti][0] * -(px - entry_px)
                rem -= tps[ti][0]
                if ti == 0 and g["be_after_tp1"]:
                    cur = entry_px
                ti += 1; n_tp += 1; n_fills += 1
            if rem <= 1e-12:
                exit_k = kt; kind = "tp%d" % len(tps)
                break
            k0 = kt + 1
            if k0 >= m:
                break
    else:
        # ---- per-bar stop level (trailing and/or move-triggered break-even)
        sl_arr = np.full(m, sl0)
        if g["trail"] is not None:
            best = np.minimum.accumulate(lo)
            prev = np.empty(m); prev[0] = np.inf; prev[1:] = best[:-1]
            sl_arr = np.minimum(sl_arr, prev + g["trail"])
        if g["be_move"] is not None:
            kb = ctx.first_le(0, entry_px - g["be_move"])
            if kb != -1 and kb + 1 < m:
                sl_arr[kb + 1:] = np.minimum(sl_arr[kb + 1:], entry_px)
        k0 = 0; ti = 0
        while True:
            sub = hi[k0:] >= sl_arr[k0:]
            ks = k0 + int(np.argmax(sub)) if sub.any() else -1
            kt = ctx.first_le(k0, lv[ti]) if ti < len(lv) else -1
            if ks != -1 and (kt == -1 or ks <= kt):
                cur = sl_arr[ks]; o = op[ks]
                px = o if o >= cur else cur
                gross += rem * -(px - entry_px)
                rem = 0.0; n_fills += 1; exit_k = ks
                kind = "stop" if n_tp == 0 else "stop-after-tp%d" % n_tp
                break
            if kt == -1:
                break
            o = op[kt]; l = lo[kt]
            while ti < len(lv) and l <= lv[ti]:
                px = o if o <= lv[ti] else lv[ti]
                gross += tps[ti][0] * -(px - entry_px)
                rem -= tps[ti][0]
                if ti == 0 and g["be_after_tp1"] and kt + 1 < m:
                    sl_arr[kt + 1:] = np.minimum(sl_arr[kt + 1:], entry_px)
                ti += 1; n_tp += 1; n_fills += 1
            if rem <= 1e-12:
                exit_k = kt; kind = "tp%d" % len(tps)
                break
            k0 = kt + 1
            if k0 >= m:
                break

    if exit_k is None:
        if b < n:
            o_exit = B["oa"][b]; exit_idx = b
        else:
            o_exit = B["ca"][n - 1]; exit_idx = n - 1
        gross += rem * -(o_exit - entry_px)
        n_fills += 1
        kind = "time-after-tp%d" % n_tp if n_tp else "time"
    else:
        exit_idx = a + exit_k
    return {"exit_index": int(exit_idx), "gross": gross,
            "net": gross - SLIP_PER_TRADE,
            "net_per_fill": gross - SLIP_PER_TRADE * n_fills,
            "n_fills": n_fills, "kind": kind, "n_tp": n_tp,
            "hold_min": int(B["tsmin"][exit_idx] - B["tsmin"][i0])}


def run_many(idxs, pxs, geoms, B, want=("net",)):
    """All geometries on all entries. The window and its running extremes are
    built ONCE per (entry, horizon) and shared by every geometry with that
    horizon, so the grid costs a binary search per geometry, not a scan."""
    ng, ne = len(geoms), len(idxs)
    out = {w: np.full((ng, ne), np.nan) for w in want}
    horiz = {}
    for gi, g in enumerate(geoms):
        horiz.setdefault((g["days"], g["minutes"]), []).append(gi)
    for p in range(ne):
        i0 = int(idxs[p]); px = float(pxs[p])
        for _key, gis in horiz.items():
            a, b = window(i0, geoms[gis[0]], B)
            if a >= b:
                continue
            ctx = _Ctx(B["ha"][a:b], B["la"][a:b], B["oa"][a:b])
            for gi in gis:
                r = one_short(i0, px, geoms[gi], B, ctx=ctx, ab=(a, b))
                if r is None:
                    continue
                for w in want:
                    out[w][gi, p] = r[w]
    return out


# --------------------------------------------------------------------- baseline
def blind_idx(idxs, B, ndraw=12, seed=20260901):
    """Random moment inside the SAME trading day as each real entry."""
    st, en = days_index(B)
    d = B["dord"][idxs]
    lo = st[d].astype(np.int64); hi = en[d].astype(np.int64)
    rng = np.random.default_rng(seed)
    u = rng.random((ndraw, len(idxs)))
    return (lo + (u * (hi - lo)).astype(np.int64)).astype(np.int64)


# --------------------------------------------------------------------- stats
def boot_day(vals, dayid, reps=4000, seed=7, ret_boot=False):
    """Block bootstrap BY TRADING DAY over a per-entry vector."""
    ok = ~np.isnan(vals)
    v = vals[ok]; dd = dayid[ok]
    if len(v) == 0:
        return (np.nan, np.nan, np.nan)
    u, inv = np.unique(dd, return_inverse=True)
    S = np.bincount(inv, weights=v); C = np.bincount(inv).astype(float)
    k = len(u)
    rng = np.random.default_rng(seed)
    iz = rng.integers(0, k, size=(reps, k))
    bm = S[iz].sum(1) / np.maximum(C[iz].sum(1), 1)
    m = float(v.mean())
    lo = float(np.percentile(bm, 2.5)); hi = float(np.percentile(bm, 97.5))
    if ret_boot:
        return m, lo, hi, bm
    return m, lo, hi
