# -*- coding: utf-8 -*-
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import eng

B = eng.tape()
E = pd.read_parquet(r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----\2674809c-6765-4e6e-873d-82958246267b\scratchpad\geom_entries.parquet")
S = E[E.direction == "short"].reset_index(drop=True)
idxs = S.bar_index.values.astype(np.int64); pxs = S.entry_px.values.astype(float)

geoms = []
for sl in (20.0, 40.0):
    for tp in (5.0, 10.0, 20.0, 40.0):
        geoms.append(eng.G("t%g_s%g" % (tp, sl), [(1.0, tp)], sl, days=5))
t0 = time.time()
out = eng.run_many(idxs[:400], pxs[:400], geoms, B, want=("net",))
dt = time.time() - t0
print("8 geoms x 400 entries, 5d horizon: %.2fs  -> per (geom,entry) %.3f ms" % (dt, 1000*dt/(8*400)))
for gi, g in enumerate(geoms):
    print("  %-12s mean=%+.4f" % (g["name"], np.nanmean(out["net"][gi])))

geoms2 = [eng.G("m%d" % m, [(1.0, 10.0)], 20.0, minutes=m) for m in (60, 240, 1440)]
t0 = time.time()
out2 = eng.run_many(idxs[:400], pxs[:400], geoms2, B, want=("net",))
print("3 minute-geoms x 400: %.2fs" % (time.time()-t0))
