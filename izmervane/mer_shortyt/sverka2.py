# -*- coding: utf-8 -*-
"""sverka2.py - the SECOND branch of eng.one_short (per-bar stop: trailing and
move-triggered break-even) has no counterpart in gh._one_trade, so sverka.py
never touched it.  Two ways to reach it anyway:

  (a) DEGENERATE: trail = 1e9 and be_move = 1e9 make the per-bar stop identical
      to the fixed stop, so the branch must reproduce gh._one_trade EXACTLY on
      all 3321 shorts.  If it does not, the branch is wrong.
  (b) SYNTHETIC: a 6-bar hand-computable tape where I know the answer by hand.
"""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import eng, baza
import geom_harness as gh

B = eng.tape()
S = baza.shorts()
idxs = S.bar_index.values.astype(np.int64); pxs = S.entry_px.values.astype(float)
HUGE = 1e9

print("### (a) ДЕГЕНЕРАТ: per-bar клонът срещу gh._one_trade, 3321 шорта")
CASES = [
    ("ladder 7.5/12/20 SL20 BE  · trail=1e9", eng.G("x", [(1/3,7.5),(1/3,12.0),(1/3,20.0)], 20.0, True,  trail=HUGE, days=5), 5),
    ("flat TP10 SL30            · trail=1e9", eng.G("x", [(1.0,10.0)], 30.0, False, trail=HUGE, days=5), 5),
    ("flat TP10 SL30          · be_move=1e9", eng.G("x", [(1.0,10.0)], 30.0, False, be_move=HUGE, days=5), 5),
    ("no target SL20 · trail=1e9 (само стоп)", eng.G("x", [], 20.0, False, trail=HUGE, days=5), 5),
]
allok = True
for name, g, dd in CASES:
    gh.TIME_EXIT_DAYS = dd
    ghg = {"name": name, "tps": g["tps"], "sl": g["sl"], "be_after_tp1": g["be_after_tp1"]}
    mine = np.full(len(S), np.nan); ref = np.full(len(S), np.nan); kb = 0
    for p in range(len(S)):
        r1 = eng.one_short(int(idxs[p]), float(pxs[p]), g, B)
        r2 = gh._one_trade(int(idxs[p]), "short", float(pxs[p]), ghg, B)
        if r1: mine[p] = r1["net"]
        if r2: ref[p] = r2["net"]
        if (r1 is None) != (r2 is None): kb += 1
        elif r1 and r1["kind"].replace("be-", "") != r2["kind"].replace("be-", ""): kb += 1
    d = np.abs(mine - ref); bad = int(np.nansum(d > 1e-12))
    allok &= (bad == 0 and kb == 0)
    print("  %-40s max|dnet|=%.2e  mismatch=%d  kind=%d  mean=%+.4f"
          % (name, float(np.nanmax(d)), bad, kb, float(np.nanmean(ref))))
gh.TIME_EXIT_DAYS = 5

print("\n### (b) СИНТЕТИЧНА ЛЕНТА - трал, смятан на ръка")
# entry short at 100.  ask bars after entry (bid==ask, no spread, so I can add it by hand)
#   k: open  high  low
#   0: 99    99.5  97      -> best low 97
#   1: 97.5  98    95      -> stop was min(120, inf+3)=120 ; best low 95
#   2: 95.5  98.5  95      -> stop = min(120, 95+3)=98  -> high 98.5 >= 98 -> STOP at 98
n = 40
F = {k: np.zeros(n) for k in ("ob","oa","hb","ha","lb","la","cb","ca")}
for k in ("ob","oa"): F[k][:] = 100.0
for k in ("hb","ha"): F[k][:] = 100.0
for k in ("lb","la"): F[k][:] = 100.0
rows = [(99.0, 99.5, 97.0), (97.5, 98.0, 95.0), (95.5, 98.5, 95.0)]
for j,(o,h,l) in enumerate(rows):
    k = j+1
    F["oa"][k]=o; F["ha"][k]=h; F["la"][k]=l
    F["ob"][k]=o; F["hb"][k]=h; F["lb"][k]=l
F["dord"] = np.zeros(n, dtype=np.int32); F["dord"][20:] = 1
F["tsmin"] = np.arange(n, dtype=np.int64)
g = eng.G("trail3", [], 20.0, trail=3.0, days=1)
r = eng.one_short(0, 100.0, g, F)
exp_gross = -(98.0 - 100.0)
print("  трал 3$: изход %s на бар %d, gross=%+.2f (на ръка: стоп 95+3=98 -> %+.2f)  %s"
      % (r["kind"], r["exit_index"], r["gross"], exp_gross,
         "OK" if abs(r["gross"]-exp_gross) < 1e-9 else "ГРЕШКА"))
ok_b1 = abs(r["gross"]-exp_gross) < 1e-9

# be_move: stop -> entry once price has moved 3$ in favour (low <= 97 at bar 1)
#   bar1 low 97 -> armed from bar 2 -> bar 2 high 98.5 >= 100? no. add bar 3 high 100.2
F2 = {k: v.copy() for k, v in F.items()}
F2["ha"][4] = 100.2; F2["hb"][4] = 100.2; F2["oa"][4] = 99.0; F2["ob"][4] = 99.0
F2["la"][4] = 99.0; F2["lb"][4] = 99.0
g2 = eng.G("bem3", [(1.0, 25.0)], 20.0, be_move=3.0, days=1)
r2 = eng.one_short(0, 100.0, g2, F2)
print("  be_move 3$: изход %s на бар %d, gross=%+.2f (на ръка: стоп става 100, бар 4 стига 100.2 -> 0.00)  %s"
      % (r2["kind"], r2["exit_index"], r2["gross"], "OK" if abs(r2["gross"]) < 1e-9 else "ГРЕШКА"))
ok_b2 = abs(r2["gross"]) < 1e-9
# and NOT armed before the move: same tape, be_move 9$ (never reached) -> rides to TP 75
g3 = eng.G("bem9", [(1.0, 25.0)], 20.0, be_move=9.0, days=1)
r3 = eng.one_short(0, 100.0, g3, F2)
print("  be_move 9$ (не се стига): изход %s gross=%+.2f (на ръка: без BE, до времето при 100.0 -> 0.00)  %s"
      % (r3["kind"], r3["gross"], "OK" if r3["kind"].startswith("time") else "ГРЕШКА"))
ok_b3 = r3["kind"].startswith("time")

print("\nVERDICT:", "PASS" if (allok and ok_b1 and ok_b2 and ok_b3) else "FAIL")
