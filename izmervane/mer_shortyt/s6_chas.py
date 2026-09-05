# -*- coding: utf-8 -*-
"""s6 - the baseline's own weak spot, measured instead of assumed.

The real short entries are NOT spread evenly over the day: 12-15 UTC and 21-23
UTC carry far more than their share (measured: total variation distance 0.186
against a uniform-in-day blind draw, 11.0% of real entries at 22 UTC vs 3.3% of
blind ones).  Gold's volatility and spread are hour-dependent, so a blind draw
that is uniform in the day is NOT the same trade as the real one - and if that
made the blind easier, the whole "nothing beats blind" verdict would be an
artefact of the control, not a fact about shorts.

So: a SECOND blind, drawn in the same trading day but with the hour-of-day drawn
from the REAL entries' own hour distribution.  Same 152 geometries, same paired
comparison, same max-t correction.  If the verdict moves, the first one was wrong.
"""
import sys, time, json
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import eng, baza, mreja

t0 = time.time()
B = eng.tape()
S = baza.shorts()
G = mreja.family(); ng = len(G)
ridx = S.bar_index.values.astype(np.int64)
rpx = S.entry_px.values.astype(float)

hr = ((B["tsmin"] // 60) % 24).astype(np.int8)
st, en = eng.days_index(B)
d = B["dord"][ridx]
p_hour = np.bincount(hr[ridx], minlength=24).astype(float); p_hour /= p_hour.sum()

rng = np.random.default_rng(31415926)
ND = baza.NDRAW
bidx = np.empty((ND, len(ridx)), dtype=np.int64)
for j in range(ND):
    for p in range(len(ridx)):
        a, b = int(st[d[p]]), int(en[d[p]])
        for _try in range(40):
            h = rng.choice(24, p=p_hour)
            cand = np.nonzero(hr[a:b] == h)[0]
            if len(cand):
                bidx[j, p] = a + int(cand[rng.integers(len(cand))]); break
        else:
            bidx[j, p] = a + int(rng.integers(b - a))
bpx = B["ob"][bidx]
hb = np.bincount(hr[bidx.reshape(-1)], minlength=24) / bidx.size
print("[час] обща вариационна дистанция реални vs нов сляп: %.3f  (старият сляп беше 0.186)"
      % (0.5 * np.abs(p_hour - hb).sum()))

real, blind = baza.run_grid(B, G, ridx, rpx, bidx, bpx)
dd, bm = baza.paired(real, blind)
ok = ~np.isnan(real).any(0) & ~np.isnan(bm).any(0)
bt = baza.Boot(B["dord"][ridx][ok])
mD, loD, hiD, seD, tD, bmD = bt.stats(dd[:, ok])
mR, loR, hiR, _, _, _ = bt.stats(real[:, ok])
mB, _, _, _, _, _ = bt.stats(bm[:, ok])
pfw, _ = bt.maxt_p(mD, seD, bmD)

old = json.load(open(HERE / "rez_mreja.json"))
oldD = np.array(old["delta"])
o = np.argsort(-mD)
print("\n" + "=" * 118)
print("ТАБЛИЦА 8 · СЪЩИТЕ 152 срещу СЛЯП С ИЗРАВНЕН ЧАС (%d входа, %d дни)" % (ok.sum(), bt.k))
print("=" * 118)
print("%-32s %9s %9s %9s %-20s %8s %10s" %
      ("геометрия", "реален$", "сляп$", "РАЗЛИКА", "95% интервал", "p_сем", "стар сляп"))
print("-" * 118)
for i in o[:10]:
    print("%-32s %+9.4f %+9.4f %+9.4f  [%+.3f, %+.3f] %8.3f %+10.4f"
          % (G[i]["name"], mR[i], mB[i], mD[i], loD[i], hiD[i], pfw[i], oldD[i]))
print("-" * 118)
print("интервал над нулата без поправка: %d от 152 · с max-t поправка p<0.05: %d · реален нет > 0: %d"
      % (int((loD > 0).sum()), int((pfw < 0.05).sum()), int((mR > 0).sum())))
print("корелация на 152-те разлики между двата слепи баланса: %.3f" % float(np.corrcoef(mD, oldD)[0, 1]))
print("средно изместване на разликата (нов сляп - стар сляп): %+.4f$" % float((mD - oldD).mean()))
print("\n[%.0fs]" % (time.time() - t0))
