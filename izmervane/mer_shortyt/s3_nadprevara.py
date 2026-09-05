# -*- coding: utf-8 -*-
"""s3 - the question UNDER the geometry search, asked without any geometry.

Owner's words: "има страшно много места по над 100 пипса" (100 pips = 10$).
That is a claim about the TAPE, not about the signal.  The RACE separates them:
after a short entry, does price reach -D before it reaches +D?  No targets, no
ladder, no stop, no slippage - so the number cannot be blamed on "wrong
geometry", because every geometry is a bet on exactly this race.
Driftless -> 0.500.  Real entries vs blind ones, paired, 12 blind draws.

Two different denominators, kept apart on purpose:
  'СТИГА ЛИ'   = share of ALL entries where price falls D$ at any time in the window
  'НАДОЛУ 1-ви'= share of the entries where the race was DECIDED (one side reached)
"""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import eng, baza

t0 = time.time()
B = eng.tape()
S = baza.shorts()
ridx, rpx, bidx, bpx = baza.make_sets(B, S)
DS = [2.0, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0, 50.0]
HOR = [("60 мин", dict(minutes=60)), ("1 ден", dict(days=1)), ("5 дни", dict(days=5))]


def race(idxs, pxs, hkw):
    ne = len(idxs)
    reach = np.full((len(DS), ne), np.nan)
    first = np.full((len(DS), ne), np.nan)
    g = eng.G("w", [], 20.0, **hkw)
    for p in range(ne):
        i0 = int(idxs[p]); px = float(pxs[p])
        a, b = eng.window(i0, g, B)
        if a >= b:
            continue
        ctx = eng._Ctx(B["ha"][a:b], B["la"][a:b], B["oa"][a:b])
        for j, D in enumerate(DS):
            kf = ctx.first_le(0, px - D)
            ka = ctx.first_ge(0, px + D)
            reach[j, p] = 1.0 if kf != -1 else 0.0
            first[j, p] = np.nan if (kf == -1 and ka == -1) else \
                (1.0 if (kf != -1 and (ka == -1 or kf <= ka)) else 0.0)
    return reach, first


print("=" * 116)
print("ТАБЛИЦА 4 · НАДПРЕВАРАТА - пада ли цената D$ ПРЕДИ да се вдигне D$ (шорт, БЕЗ никаква геометрия)")
print("=" * 116)
print("%-7s %5s %10s %10s %11s %10s %-21s %7s" %
      ("прозор", "D $", "СТИГА ЛИ", "сляп стига", "НАДОЛУ 1-ви", "сляп 1-ви", "95% инт. на разликата", "решени"))
print("-" * 116)
for hname, hkw in HOR:
    rR, fR = race(ridx, rpx, hkw)
    accR = np.zeros_like(rR); accF = np.zeros_like(fR); cntF = np.zeros_like(fR)
    for j in range(bidx.shape[0]):
        r2, f2 = race(bidx[j], bpx[j], hkw)
        accR += np.nan_to_num(r2)
        accF += np.nan_to_num(f2); cntF += ~np.isnan(f2)
    rB = accR / bidx.shape[0]
    fB = np.where(cntF > 0, accF / np.maximum(cntF, 1), np.nan)
    okA = ~np.isnan(rR[0])
    btA = baza.Boot(B["dord"][ridx][okA], reps=4000)
    mA, _, _, _, _, _ = btA.stats(np.vstack([rR[j][okA] for j in range(len(DS))] +
                                            [rB[j][okA] for j in range(len(DS))]))
    for j, D in enumerate(DS):
        ok = ~np.isnan(fR[j]) & ~np.isnan(fB[j])
        if ok.sum() < 20:
            print("%-7s %5.0f %9.1f%% %9.1f%% %11s %10s  %-21s %7d" %
                  (hname, D, 100 * mA[j], 100 * mA[len(DS) + j], "-", "-",
                   "твърде малко решени", ok.sum()))
            continue
        bt = baza.Boot(B["dord"][ridx][ok], reps=4000)
        m, lo, hi, se, t, _ = bt.stats(np.vstack([fR[j][ok], fB[j][ok], (fR[j] - fB[j])[ok]]))
        print("%-7s %5.0f %9.1f%% %9.1f%% %11.3f %10.3f  [%+.3f, %+.3f] %7d" %
              (hname, D, 100 * mA[j], 100 * mA[len(DS) + j], m[0], m[1], lo[2], hi[2], ok.sum()))
    print("-" * 116)
print("СТИГА ЛИ = дял от ВСИЧКИ %d входа, при които цената пада D$ в прозореца (местата ги ИМА - собственикът е прав)" % len(ridx))
print("НАДОЛУ 1-ви = дял от РЕШЕНИТЕ надпревари; 0.500 = никаква посока. Това е залогът на всяка геометрия.")
print("\n[%.0fs]" % (time.time() - t0))
