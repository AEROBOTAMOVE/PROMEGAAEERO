# -*- coding: utf-8 -*-
"""s1_baza.py - (1) reproduce the stated baseline, (2) prove the pipeline does
NOT invent a winner out of noise before it is allowed to judge 150 geometries."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import eng, baza

t0 = time.time()
B = eng.tape()
S = baza.shorts()
L = baza.shorts.__doc__
E = pd.read_parquet(baza.ENTRIES)
LO = E[E.direction == "long"].reset_index(drop=True)
print("[entries] short=%d  long=%d  days=%d" % (len(S), len(LO), len(np.unique(B["dord"][S.bar_index.values]))))

SHIP = eng.G("shipped ladder 7.5/12/20 SL20 BE 5d",
             [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)], 20.0, True, days=5)

ridx, rpx, bidx, bpx = baza.make_sets(B, S)
real, blind = baza.run_grid(B, [SHIP], ridx, rpx, bidx, bpx)
d, bm = baza.paired(real, blind)

dayid = B["dord"][ridx]
ok = ~np.isnan(real[0]) & ~np.isnan(bm[0])
print("[valid] %d of %d short entries usable (%d dropped: no window)" % (ok.sum(), len(ok), (~ok).sum()))

bt = baza.Boot(dayid[ok])
M = np.vstack([real[0][ok], bm[0][ok], d[0][ok]])
mean, lo, hi, se, t, bmb = bt.stats(M)
lab = ["РЕАЛЕН ШОРТ (доставената геом.)", "СЛЯП ШОРТ (същите дни, 12 тегления)", "РАЗЛИКА реален - сляп"]
print("\n### БАЗАТА - доставената геометрия, 5 дни, %d шорт входа" % ok.sum())
print("  %-38s %10s  %-22s" % ("", "$/сделка", "95% интервал (блок по ден)"))
for i in range(3):
    print("  %-38s %+10.4f  [%+.3f, %+.3f]" % (lab[i], mean[i], lo[i], hi[i]))

# --- same thing for LONG, as a control that the machinery can see a positive ---
ridxL = LO.bar_index.values.astype(np.int64); rpxL = LO.entry_px.values.astype(float)
bidxL = eng.blind_idx(ridxL, B, ndraw=baza.NDRAW, seed=baza.SEED_BLIND)
bpxL = B["oa"][bidxL]
import eng as _e
def long_run(idxs, pxs, g):
    v = np.full(len(idxs), np.nan)
    for p in range(len(idxs)):
        r = _one(int(idxs[p]), float(pxs[p]), g)
        if r is not None: v[p] = r["net"]
    return v
sys.path.insert(0, str(HERE.parent))
import geom_harness as gh
gh.TIME_EXIT_DAYS = 5
ghg = {"name": "s", "tps": SHIP["tps"], "sl": SHIP["sl"], "be_after_tp1": True}
def _one(i, px, g):
    return gh._one_trade(i, "long", px, ghg, B)
rl = long_run(ridxL, rpxL, None)
bl = np.vstack([long_run(bidxL[j], bpxL[j], None) for j in range(bidxL.shape[0])])
blm = np.nanmean(bl, axis=0)
okL = ~np.isnan(rl) & ~np.isnan(blm)
btL = baza.Boot(B["dord"][ridxL][okL])
mL, loL, hiL, seL, tL, _ = btL.stats(np.vstack([rl[okL], blm[okL], (rl-blm)[okL]]))
print("\n### КОНТРОЛ ЛОНГ - същата машина, същата геометрия, %d лонг входа" % okL.sum())
for i, nm in enumerate(["РЕАЛЕН ЛОНГ", "СЛЯП ЛОНГ", "РАЗЛИКА реален - сляп"]):
    print("  %-38s %+10.4f  [%+.3f, %+.3f]" % (nm, mL[i], loL[i], hiL[i]))

print("\n[%.0fs]" % (time.time() - t0))
