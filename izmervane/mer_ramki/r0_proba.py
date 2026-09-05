# -*- coding: utf-8 -*-
"""r0_proba.py - плумбингът: чете ли се решетката, съвпада ли лентата с нея."""
from __future__ import annotations
import sys, time
from pathlib import Path
import numpy as np

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
REPO = IZM.parent
KONV = IZM / "mer_celiyat-konveyer"
sys.path.insert(0, str(KONV)); sys.path.insert(0, str(IZM / "mer_mnozhitelite"))
sys.path.insert(0, str(IZM)); sys.path.insert(0, str(REPO))
import pq_lite as pl
import dvig

t0 = time.time()
G = pl.read_columns(KONV / "reshetka.parquet")
G.pop("__meta__", None)
print("решетка колони:", sorted(G.keys()))
for k in sorted(G.keys()):
    v = G[k]
    print("   %-12s %-10s %s" % (k, getattr(v, "dtype", "?"), len(v)))
print("редове", len(G["ts"]), "%.1fs" % (time.time() - t0))
B = dvig.лента()
print("лента", len(B["tsmin"]), B["tsmin"][0], B["tsmin"][-1])
cp = G["ts"] // 60_000_000
print("чекпойнти", len(cp), cp[0], cp[-1])
print("cp кратни на 15:", int((cp % 15 == 0).sum()), "от", len(cp))
d15 = np.diff(cp)
print("разлики между чекпойнти: min %d  медиана %d  max %d" % (d15.min(), np.median(d15), d15.max()))
g15 = np.unique(B["tsmin"] // 15)
print("уникални 15-мин групи в лентата:", len(g15))
print("сечение с чекпойнтите:", len(np.intersect1d(g15 * 15, cp)))
