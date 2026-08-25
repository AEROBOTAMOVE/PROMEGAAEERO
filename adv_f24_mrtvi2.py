# -*- coding: utf-8 -*-
"""adv · СЪЩОТО, но с мярка за качество, която НЕ зависи от изхода на сделката.

Първият опит бъркаше: делът мъртви барове се мереше в РЕАЛИЗИРАНИЯ прозорец, а той е
дълъг точно когато сделката НЕ се решава → подбор. Тук мярката е (1) ПРЕДИ входа и
(2) във ФИКСИРАН прозорец от 21 дни, независимо кога сделката е свършила.
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

D = "C:/Users/User/Downloads/ЛОЦО/f6_data"
ТП = (0.20, 0.32, 0.54); СТОП = 0.54; ДНИ = 21


def dc(p):
    d = pd.read_csv(p)
    c = [x for x in d.columns if x.lower() in ("date", "datetime", "observation_date")][0]
    d[c] = pd.to_datetime(d[c], errors="coerce")
    return d.dropna(subset=[c]).set_index(c).sort_index()


s = dc(f"{D}/silver_yahoo_full.csv")[["Open", "High", "Low", "Close"]].apply(pd.to_numeric, errors="coerce").dropna()
dx = dc(f"{D}/dxy_yahoo_full.csv")["Close"].reindex(s.index).ffill()
rr = pd.to_numeric(dc(f"{D}/DFII10.csv")["DFII10"], errors="coerce").reindex(s.index).ffill()
mL = ((-dx.pct_change(20)) > 0) & ((-(rr - rr.shift(20))) > 0)
mS = (dx.pct_change(20) > 0) & ((rr - rr.shift(20)) > 0)
стр = lambda x: x.fillna(False).groupby((~x.fillna(False)).cumsum()).cumsum().astype(int)
SL, SS = стр(mL), стр(mS)

H, L, C = s["High"].to_numpy(), s["Low"].to_numpy(), s["Close"].to_numpy()
N = len(s)
мъртъв = (H - L) == 0
# ЕКС-АНТЕ: дял мъртви барове в 60-те дни ПРЕДИ входа (знае се на входа, не гледа напред)
преди60 = pd.Series(мъртъв).rolling(60).mean().to_numpy()
# ФИКСИРАН напред-прозорец 21 дни, независимо от изхода
напред21 = pd.Series(мъртъв).shift(-1).rolling(21).mean().shift(-20).to_numpy()


def сим(i, лонг):
    зн = 1.0 if лонг else -1.0
    вх = C[i]; tp = [вх + зн * t for t in ТП]; sl = вх - зн * СТОП
    пари = 0.0; взети = 0; бе = False
    for j in range(i + 1, min(i + 1 + ДНИ, N)):
        hi, lo = H[j], L[j]
        тек = вх if бе else sl
        уд = (lo <= тек) if лонг else (hi >= тек)
        нови = [k for k, t in enumerate(tp) if k >= взети and ((hi >= t) if лонг else (lo <= t))]
        if уд:
            return пари + (тек - вх) * зн * (3 - взети) / 3.0
        for k in нови:
            пари += (tp[k] - вх) * зн / 3.0; взети = k + 1
            if k == 0: бе = True
            if k == 2: return пари
    return пари + (C[min(i + ДНИ, N - 1)] - вх) * зн * (3 - взети) / 3.0


R = []
for i in range(60, N - 2):
    for лонг in (True, False):
        R.append((s.index[i], "long" if лонг else "short",
                  int(SL.iloc[i]) if лонг else int(SS.iloc[i]), сим(i, лонг),
                  преди60[i], напред21[i]))
T = pd.DataFrame(R, columns=["ден", "посока", "стрийк", "нето", "преди60", "напред21"])
T["ера"] = np.where(T["ден"] < "2013-01-01", "2000-2012", "2013-2026")

for мярка, ет in (("преди60", "ЕКС-АНТЕ · дял мъртви барове в 60 дни ПРЕДИ входа"),
                  ("напред21", "ФИКСИРАН прозорец · дял мъртви барове в дни +1…+21")):
    print("=" * 100)
    print(f"{ет}  (LONG)")
    print("=" * 100)
    g = T[(T["посока"] == "long") & T[мярка].notna()].copy()
    g["кофа"] = pd.cut(g[мярка], [-.001, .05, .2, .4, .6, 1.001],
                       labels=["<5%", "5-20%", "20-40%", "40-60%", ">60%"])
    print(f"  {'кофа':8s} {'n':>6s} {'нето':>9s} {'печели':>8s} ‖ {'2000-2012 n/нето':>22s} ‖ {'2013-2026 n/нето':>22s}")
    for k, v in g.groupby("кофа", observed=True):
        if len(v) == 0: continue
        a = v[v["ера"] == "2000-2012"]; b = v[v["ера"] == "2013-2026"]
        fa = f"{len(a):5,d} {a['нето'].mean():+.4f}" if len(a) >= 30 else f"{len(a):5,d}     ·"
        fb = f"{len(b):5,d} {b['нето'].mean():+.4f}" if len(b) >= 30 else f"{len(b):5,d}     ·"
        print(f"  {str(k):8s} {len(v):6,d} {v['нето'].mean():+9.4f} {(v['нето']>0).mean()*100:7.1f}% ‖ "
              f"{fa:>22s} ‖ {fb:>22s}")
    print()

print("=" * 100)
print("РЕШАВАЩОТО · САМО сделките, чийто 21-дневен прозорец НЯМА НИТО ЕДИН мъртъв бар")
print("=" * 100)
чист = T[(T["напред21"] == 0.0)]
print(f"  общо чисти сделки: {len(чист):,} от {len(T):,} ({len(чист)/len(T)*100:.1f}%)")
КЛ = {"day1": lambda g: g["стрийк"] == 1, "fresh": lambda g: g["стрийк"].between(2, 3),
      "mixed": lambda g: g["стрийк"] == 0, "stale": lambda g: g["стрийк"] >= 4}
print(f"  {'посока':6s} {'клетка':7s} {'ВСИЧКИ n/нето':>20s} {'ЧИСТИ n/нето':>20s} "
      f"{'ЧИСТИ 00-12':>14s} {'ЧИСТИ 13-26':>14s}")
for d in ("long", "short"):
    for им, ф in КЛ.items():
        a = T[(T["посока"] == d) & ф(T)]; b = чист[(чист["посока"] == d) & ф(чист)]
        if len(a) < 30: continue
        b1 = b[b["ера"] == "2000-2012"]["нето"]; b2 = b[b["ера"] == "2013-2026"]["нето"]
        f1 = f"{b1.mean():+.4f}(n{len(b1)})" if len(b1) >= 30 else f"·(n{len(b1)})"
        f2 = f"{b2.mean():+.4f}(n{len(b2)})" if len(b2) >= 30 else f"·(n{len(b2)})"
        print(f"  {d:6s} {им:7s} {len(a):8,d} {a['нето'].mean():+.4f}   {len(b):8,d} "
              f"{b['нето'].mean() if len(b) else float('nan'):+.4f}   {f1:>14s} {f2:>14s}")
print()
л = чист[чист["посока"] == "long"]["нето"]
print(f"  ЦЯЛО LONG само на чисти прозорци: {л.mean():+.4f}$ (n={len(л):,})  "
      f"→ след спред 0.03$: {л.mean()-0.03:+.4f}$")
л2 = T[T["посока"] == "long"]["нето"]
print(f"  ЦЯЛО LONG на всички прозорци:     {л2.mean():+.4f}$ (n={len(л2):,})")
