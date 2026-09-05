# -*- coding: utf-8 -*-
"""sverka.py - my minute engine against gh._one_trade, trade for trade.

Nothing further is believed unless this prints 0 mismatches and max|delta|=0.
gh.TIME_EXIT_DAYS is a module global read inside _one_trade, so the daily
horizon is swept by setting it (READ-ONLY on the file itself).
"""
import sys, time
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import eng
import geom_harness as gh

B = eng.tape()
E = pd.read_parquet(gh.OUT_ENTRIES)
S = E[E.direction == "short"].reset_index(drop=True)
print("[entries] all=%d short=%d long=%d" % (len(E), len(S), (E.direction == "long").sum()))

CASES = [
    ("shipped ladder 7.5/12/20 SL20 BE  5d", eng.G("x", [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)], 20.0, True, days=5), 5),
    ("ladder 7.5/12/20 SL20 no-BE       5d", eng.G("x", [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)], 20.0, False, days=5), 5),
    ("flat TP15 SL15                    5d", eng.G("x", [(1.0, 15.0)], 15.0, False, days=5), 5),
    ("flat TP10 SL30                    5d", eng.G("x", [(1.0, 10.0)], 30.0, False, days=5), 5),
    ("flat TP30 SL10                    5d", eng.G("x", [(1.0, 30.0)], 10.0, False, days=5), 5),
    ("halves 5/10 SL25 BE               1d", eng.G("x", [(0.5, 5.0), (0.5, 10.0)], 25.0, True, days=1), 1),
    ("shipped ladder                    2d", eng.G("x", [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)], 20.0, True, days=2), 2),
    ("flat TP20 SL40                   10d", eng.G("x", [(1.0, 20.0)], 40.0, False, days=10), 10),
]

idxs = S.bar_index.values
pxs = S.entry_px.values
allok = True
for name, g, dd in CASES:
    gh.TIME_EXIT_DAYS = dd
    ghgeom = {"name": name, "tps": g["tps"], "sl": g["sl"], "be_after_tp1": g["be_after_tp1"]}
    t0 = time.time()
    mine = np.full(len(S), np.nan); ref = np.full(len(S), np.nan)
    kmine = []; kref = []
    for p in range(len(S)):
        r1 = eng.one_short(int(idxs[p]), float(pxs[p]), g, B)
        r2 = gh._one_trade(int(idxs[p]), "short", float(pxs[p]), ghgeom, B)
        if r1 is not None:
            mine[p] = r1["net"]; kmine.append(r1["kind"])
        else:
            kmine.append("NONE")
        if r2 is not None:
            ref[p] = r2["net"]; kref.append(r2["kind"])
        else:
            kref.append("NONE")
    both_nan = np.isnan(mine) & np.isnan(ref)
    d = np.where(both_nan, 0.0, np.abs(mine - ref))
    nbad = int(np.nansum(d > 1e-12)) + int((np.isnan(mine) != np.isnan(ref)).sum())
    kbad = sum(1 for x, y in zip(kmine, kref) if x != y)
    allok &= (nbad == 0 and kbad == 0)
    print("  %-38s n=%d  max|dnet|=%.2e  net-mismatch=%d  kind-mismatch=%d  mean=%+.4f  (%.0fs)"
          % (name, int((~np.isnan(ref)).sum()), float(np.nanmax(d)), nbad, kbad,
             float(np.nanmean(ref)), time.time() - t0))

gh.TIME_EXIT_DAYS = 5
print("\nVERDICT:", "PASS - engine reproduces gh._one_trade exactly" if allok else "FAIL")

# --- the fractional-horizon trap, shown rather than quoted -------------------
print("\n### gh.TIME_EXIT_DAYS is a WHOLE day ordinal - fractions do nothing")
g5 = {"name": "s", "tps": [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)], "sl": 20.0, "be_after_tp1": True}
for ted in (0.02, 0.05, 0.15, 0.5, 1, 2):
    gh.TIME_EXIT_DAYS = ted
    v = np.array([gh._one_trade(int(idxs[p]), "short", float(pxs[p]), g5, B)["net"]
                  for p in range(300)])
    print("   TIME_EXIT_DAYS=%-5s  mean net over first 300 shorts = %+.6f" % (ted, v.mean()))
gh.TIME_EXIT_DAYS = 5

print("\n### my minute horizon does move (same 300 shorts, ladder geometry)")
for mn in (60, 120, 240, 480, 1440, 7200):
    gm = eng.G("m", [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)], 20.0, True, minutes=mn)
    v = []
    for p in range(300):
        r = eng.one_short(int(idxs[p]), float(pxs[p]), gm, B)
        if r is not None:
            v.append(r["net"])
    print("   minutes=%-5d n=%d  mean net = %+.6f" % (mn, len(v), float(np.mean(v))))
