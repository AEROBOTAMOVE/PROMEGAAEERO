# -*- coding: utf-8 -*-
import sys, json, io
sys.argv=["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import numpy as np, pandas as pd
import live_bot as lb

N=400
idx = pd.date_range("2025-01-01", periods=N, freq="D")
# ЗЛАТО: бавен ъптренд
gold = 4000 + np.cumsum(np.full(N, 1.0))
gold_d = pd.DataFrame({"Open":gold-1,"High":gold+5,"Low":gold-5,"Close":gold}, index=idx)
# МИНЬОРИ
gdx = 40 + np.cumsum(np.full(N,0.02))
gdx_d = pd.DataFrame({"Open":gdx,"High":gdx,"Low":gdx,"Close":gdx}, index=idx)
# ДОЛАР: пада ПОСЛЕДНИЯ ЕДИН ден спрямо преди 20 (за streak=1 трябва днес True, вчера False)
dxy = np.full(N, 100.0)
# правим: за последните 21 дни dxy расте, а САМО последният ден пада рязко
dxy[-25:] = 100 + np.arange(25)*0.5
dxy[-1] = dxy[-2] - 20.0   # рязък спад днес
dxy_d = pd.DataFrame({"Close":dxy}, index=idx)
# ЛИХВИ: същото
rv = np.full(N, 2.0)
rv[-25:] = 2.0 + np.arange(25)*0.02
rv[-1] = rv[-2] - 1.0
rr = pd.Series(rv, index=idx)

print("=== СТЪПКА 1: _macro ===")
health={}
macro = lb._macro(gold_d, gdx_d, dxy_d, rr, health=health)
print("  ВХОД: gold_d/gdx_d/dxy_d/rr, N=",N)
print("  ИЗХОД macro =", macro)
print("  health =", health)

print("=== СТЪПКА 2: _streaks ===")
sk = lb._streaks(gold_d, gdx_d, dxy_d, rr)
print("  ИЗХОД streaks =", sk)

print("=== СТЪПКА 3: _refs / _regime / _scores / _resolve ===")
refs = lb._refs(gold_d)
print("  refs =", {k:round(v,2) for k,v in refs.items()})
regime = lb._regime(gold_d, gold_today=gold_d)
regime["streaks"]=sk
ls, ss, cN = lb._scores(gold_d, refs, macro, price_adj=0.0)
print("  _scores -> ls=%s ss=%s cN=%.2f"%(ls,ss,cN))
res = lb._resolve(ls, ss, macro)
print("  _resolve ->", res)
res2 = lb._demote_if_dead(res, health)
print("  _demote_if_dead ->", res2)
new_dir = res2[0]
streak_n = regime["streaks"].get(new_dir, 0)
print("  new_dir=%s  streak_n=%s"%(new_dir, streak_n))
print("  _cell_name(streak_n) =", lb._cell_name(streak_n))

print("=== СТЪПКА 4: _advice_entry ===")
stats=json.load(open("backtest_stats.json",encoding="utf-8"))
trace={}
txt, ok = lb._advice_entry(new_dir, streak_n, stats, None, False, 0, sym="XAUUSD",
                           stale_price=False, dd20=0.05, trace=trace)
print("  ВХОД: dir=%s streak=%s guard=0 shield=False stale=False"%(new_dir,streak_n))
print("  ИЗХОД txt =", txt)
print("  ИЗХОД ok  =", ok)
print("  trace =", trace)

print("=== СТЪПКА 5: _levels ===")
spot = {"bid":4399.50,"ask":4400.10,"mid":4399.80,"src":"swq","age_sec":1.0}
entry_user = lb._entry_side(spot, new_dir)
print("  _entry_side(spot, %s) = %s   (long->ask, short->bid)"%(new_dir, entry_user))
lv = lb._levels(round(entry_user,2), new_dir)
print("  _levels ->", lv)
for k,tp in zip(("tp1","tp2","tp3"), lb.TPS):
    d = abs(lv[k]-round(entry_user,2))
    print("    %s: разстояние %.2f$ = %.0f пипса ; таблицата казва %s пипса / %s$"%(k,d,d/lb.PIP,tp[1],tp[2]))
d=abs(lv["sl"]-round(entry_user,2))
print("    sl : разстояние %.2f$ = %.0f пипса ; SL_PIPS=%s SL_D=%s"%(d,d/lb.PIP,lb.SL_PIPS,lb.SL_D))
