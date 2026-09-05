# -*- coding: utf-8 -*-
"""baza.py - the paired blind-short baseline, and the day-block bootstrap that
every number in this folder is quoted with.

BLIND SHORT: for every real short entry, ndraw random moments INSIDE THE SAME
trading day, same direction, same geometry, entry price on the same side of the
spread the real entry used (open_bid, geom_harness.py:261).
PAIRED: delta[p] = real[p] - mean(blind draws[p]).  Never two different samples.
BOOTSTRAP: resample TRADING DAYS (multinomial counts), which is exactly a block
bootstrap by day and lets every geometry be resampled on the SAME days - the
only way a max-t multiple-comparison correction is meaningful.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import eng

ENTRIES = Path(r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----"
               r"\2674809c-6765-4e6e-873d-82958246267b\scratchpad\geom_entries.parquet")
NDRAW = 12
SEED_BLIND = 20260901
SEED_BOOT = 424242
REPS = 4000


def shorts():
    E = pd.read_parquet(ENTRIES)
    S = E[E.direction == "short"].reset_index(drop=True)
    return S


def make_sets(B, S, ndraw=NDRAW, seed=SEED_BLIND):
    """Real entries + ndraw blind entries per real entry, all as (idx, px)."""
    ridx = S.bar_index.values.astype(np.int64)
    rpx = S.entry_px.values.astype(float)
    bidx = eng.blind_idx(ridx, B, ndraw=ndraw, seed=seed)      # (ndraw, ne)
    bpx = B["ob"][bidx]                                        # short enters on the BID
    return ridx, rpx, bidx, bpx


def run_grid(B, geoms, ridx, rpx, bidx, bpx, verbose=True):
    """-> real (ng,ne), blind (ng,ndraw,ne) net arrays."""
    ne = len(ridx); nd = bidx.shape[0]; ng = len(geoms)
    allidx = np.concatenate([ridx, bidx.reshape(-1)])
    allpx = np.concatenate([rpx, bpx.reshape(-1)])
    if verbose:
        print("[grid] %d geometries x %d entries (%d real + %d blind) = %s trades"
              % (ng, len(allidx), ne, ne * nd, format(ng * len(allidx), ",")))
    out = eng.run_many(allidx, allpx, geoms, B, want=("net",))["net"]
    return out[:, :ne], out[:, ne:].reshape(ng, nd, ne)


def paired(real, blind):
    """delta per entry; NaN wherever the real trade or every blind draw is missing."""
    with np.errstate(invalid="ignore"):
        bm = np.nanmean(blind, axis=1)
    return real - bm, bm


class Boot:
    """One set of resampled trading days, shared by every geometry."""

    def __init__(self, dayid, reps=REPS, seed=SEED_BOOT):
        self.u, self.inv = np.unique(dayid, return_inverse=True)
        self.k = len(self.u)
        rng = np.random.default_rng(seed)
        self.W = rng.multinomial(self.k, np.full(self.k, 1.0 / self.k),
                                 size=reps).astype(np.float64).T      # (k, reps)
        self.reps = reps

    def stats(self, M):
        """M: (ng, ne) with NaNs allowed but the SAME NaN mask in every row.
        -> mean, lo95, hi95, se, t   (each length ng)"""
        ok = ~np.isnan(M[0])
        for r in M:
            assert np.array_equal(np.isnan(r), np.isnan(M[0])), "ragged NaN mask"
        Mo = np.nan_to_num(M[:, ok])
        inv = self.inv[ok]
        S = np.zeros((M.shape[0], self.k))
        np.add.at(S.T, inv, Mo.T)
        C = np.bincount(inv, minlength=self.k).astype(float)
        num = S @ self.W                       # (ng, reps)
        den = C @ self.W                       # (reps,)
        bm = num / np.maximum(den, 1.0)
        mean = S.sum(1) / C.sum()
        lo = np.percentile(bm, 2.5, axis=1)
        hi = np.percentile(bm, 97.5, axis=1)
        se = bm.std(axis=1, ddof=1)
        t = mean / np.maximum(se, 1e-12)
        return mean, lo, hi, se, t, bm

    def maxt_p(self, mean, se, bm):
        """Westfall-Young style family-wise p: the null is the CENTRED bootstrap,
        the statistic is the MAX studentised mean over the whole family."""
        tnull = (bm - mean[:, None]) / np.maximum(se[:, None], 1e-12)
        M = tnull.max(axis=0)                   # (reps,)
        tobs = mean / np.maximum(se, 1e-12)
        return np.array([(M >= t).mean() for t in tobs]), M
