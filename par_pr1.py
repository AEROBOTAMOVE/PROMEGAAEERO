# -*- coding: utf-8 -*-
import sys, json, io
sys.argv=["x"]
import live_bot as lb
import numpy as np, pandas as pd

stats = json.load(io.open("backtest_stats.json", encoding="utf-8"))
print("VERSION:", lb.VERSION)

# ---- 1) СРЕБРО_MIXED мени ли изобщо нещо? ----
print("\n=== 1 · СРЕБРО_MIXED ===")
lb.СРЕБРО_ВХОД = True     # без това всичко се реже по-рано
rows=[]
for mv in ("нищо","stale","каквото и да е"):
    lb.СРЕБРО_MIXED = mv
    for d in ("long","short"):
        for sn in (0,1,2,4,7):
            r = lb._advice_entry(d, sn, stats, 0, False, 0, sym="XAGUSD")
            rows.append((mv,d,sn,r))
base = [r for r in rows if r[0]=="нищо"]
for mv in ("stale","каквото и да е"):
    other=[r for r in rows if r[0]==mv]
    diff=[(b[1],b[2],b[3],o[3]) for b,o in zip(base,other) if b[3]!=o[3]]
    print("  '%s' vs 'нищо': разлики = %d" % (mv, len(diff)))
    for x in diff[:5]: print("     ", x)
print("  silver.long има ли клетка mixed:", isinstance(stats["silver"]["long"].get("mixed"), dict))
print("  silver.short има ли клетка mixed:", isinstance(stats["silver"]["short"].get("mixed"), dict))
lb.СРЕБРО_ВХОД = False
lb.СРЕБРО_MIXED = "нищо"

# ---- 2) СРЕБРО_ВХОД=0: изобщо стига ли се до СРЕБРО_MIXED? ----
print("\n=== 2 · при СРЕБРО_ВХОД=0 ===")
tr={}
print("  ", lb._advice_entry("long",0,stats,0,False,0,sym="XAGUSD",trace=tr), tr)

# ---- 3) МОЗЪК_ПРАГ=9 връща ли вчерашното? ----
print("\n=== 3 · МОЗЪК_ПРАГ като път назад ===")
def филтър(setups, праг, прагове_рамка):
    out=[]
    for s in setups:
        s=dict(s)
        s["праща"] = s["точки"] >= праг          # това прави `сканирай`
        нужни = прагове_рамка.get(s["рамка"], праг)
        if s["праща"] and s["точки"] < нужни:
            s["праща"]=False
        out.append(s)
    return [s["точки"] for s in out if s["праща"]]
setups=[{"рамка":f,"точки":t} for f in ("1мин","5м","15м") for t in (8,9,10,11,12,13,14,15,16)]
for праг in (14,9,0):
    print("  МОЗЪК_ПРАГ=%2d → пуснати точки: %s" % (праг, sorted(set(филтър(setups,праг,lb.МОЗЪК_ПРАГ_РАМКА)))))
print("  МОЗЪК_ПРАГ_РАМКА =", lb.МОЗЪК_ПРАГ_РАМКА)
print("  МОЗЪК_РАМКИ =", lb.МОЗЪК_РАМКИ)
print("  всички работни рамки ли са в речника:", all(f in lb.МОЗЪК_ПРАГ_РАМКА for f in lb.МОЗЪК_РАМКИ))

# ---- 4) TF_BASIS_CAP при сребро ----
print("\n=== 4 · TF_BASIS_CAP е ЕДИН за двата метала ===")
idx = pd.date_range("2026-06-01", periods=40, freq="D")
intra = pd.DataFrame({"Close": np.full(40, 65.0)}, index=idx)
for absurd in (1.0, 5.0, 50.0, 119.0, 121.0):
    daily = pd.DataFrame({"Close": np.full(40, 65.0+absurd)}, index=idx)
    st={}; notes=[]
    v = lb._tf_basis(st, "tf_basis_s", intra, daily, notes)
    print("   сребро: истински базис %+7.1f$ (%.0f%% от цената) → приет %+8.3f  бележки=%s"
          % (absurd, absurd/65*100, v, notes))
print("   TF_BASIS_CAP =", lb.TF_BASIS_CAP, " · _basis_update cap: злато 40.0 / сребро 3.0 (реда 2909/3256)")

# ---- 5) CLOCK_SKEW ----
print("\n=== 5 · CLOCK_SKEW срещу СКЮ_ДОПУСК ===")
CS, SD, MA = lb.CLOCK_SKEW, lb.СКЮ_ДОПУСК, lb.SPOT_MAX_AGE
отхв_с, отхв_без = [], []
for age in [x/2 for x in range(-400, 400)]:
    a1 = (age < -CS or age > MA) or (age < -SD)      # както е сега
    a2 = (age > MA) or (age < -SD)                    # без CLOCK_SKEW
    if a1: отхв_с.append(age)
    if a2: отхв_без.append(age)
print("   CLOCK_SKEW=%s СКЮ_ДОПУСК=%s SPOT_MAX_AGE=%s" % (CS,SD,MA))
print("   отхвърлени със и без CLOCK_SKEW еднакви:", отхв_с==отхв_без,
      "· брой", len(отхв_с), len(отхв_без))

# ---- 6) TPS: пипсовете четат ли се? ----
print("\n=== 6 · TPS ===")
print("   TPS =", lb.TPS, " PIP =", lb.PIP, " SL_PIPS =", lb.SL_PIPS, " SL_D =", lb.SL_D)
for име, п, д in lb.TPS:
    print("   %s: %d п × PIP = %.2f$  ·  записано %.2f$  ·  съвпада: %s" % (име, п, п*lb.PIP, д, abs(п*lb.PIP-д)<1e-9))
print("   S_TPS =", lb.S_TPS, "S_SL =", lb.S_SL)
print("   отношения злато ТП/стоп:", [round(d/lb.SL_D,4) for _,_,d in lb.TPS])
print("   отношения сребро ТП/стоп:", [round(d/lb.S_SL,4) for d in lb.S_TPS])
