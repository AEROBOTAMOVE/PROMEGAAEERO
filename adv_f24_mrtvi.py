# -*- coding: utf-8 -*-
"""adv · МЪРТВИТЕ БАРОВЕ ПРАВЯТ ЛИ САМИ «ръба» и «епохите»"""
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
d20 = dx.pct_change(20); r20 = rr - rr.shift(20)
mL = ((-d20) > 0) & ((-r20) > 0); mS = (d20 > 0) & (r20 > 0)
стр = lambda x: x.fillna(False).groupby((~x.fillna(False)).cumsum()).cumsum().astype(int)
SL, SS = стр(mL), стр(mS)

ВАР = {}
# СУРОВО — както F24
ВАР["сурово"] = (s["High"].to_numpy(), s["Low"].to_numpy(), s["Close"].to_numpy())
# ПОПРАВЕНО — минималната физически задължителна поправка:
#   барът трябва да покрива поне Open, Close и вчерашното Close (иначе е невъзможен)
pc = s["Close"].shift(1).fillna(s["Close"])
Hf = np.maximum.reduce([s["High"].to_numpy(), s["Open"].to_numpy(), s["Close"].to_numpy(), pc.to_numpy()])
Lf = np.minimum.reduce([s["Low"].to_numpy(), s["Open"].to_numpy(), s["Close"].to_numpy(), pc.to_numpy()])
ВАР["поправено"] = (Hf, Lf, s["Close"].to_numpy())
N = len(s)

мъртъв = (s["High"].to_numpy() - s["Low"].to_numpy()) == 0
невъзм = (s["High"].to_numpy() - s["Low"].to_numpy()) < s["Close"].diff().abs().fillna(0).to_numpy()


def сим(H, L, C, i, лонг):
    зн = 1.0 if лонг else -1.0
    вх = C[i]; tp = [вх + зн * t for t in ТП]; sl = вх - зн * СТОП
    пари = 0.0; взети = 0; бе = False
    крайj = min(i + 1 + ДНИ, N)
    for j in range(i + 1, крайj):
        hi, lo = H[j], L[j]
        тек = вх if бе else sl
        уд = (lo <= тек) if лонг else (hi >= тек)
        нови = [k for k, t in enumerate(tp) if k >= взети and ((hi >= t) if лонг else (lo <= t))]
        if уд:
            return пари + (тек - вх) * зн * (3 - взети) / 3.0, j - i
        for k in нови:
            пари += (tp[k] - вх) * зн / 3.0; взети = k + 1
            if k == 0: бе = True
            if k == 2: return пари, j - i
    return пари + (C[min(i + ДНИ, N - 1)] - вх) * зн * (3 - взети) / 3.0, min(ДНИ, N - 1 - i)


out = {}
for им, (H, L, C) in ВАР.items():
    R = []
    for i in range(60, N - 2):
        for лонг in (True, False):
            п, дни = сим(H, L, C, i, лонг)
            окно = slice(i + 1, min(i + 1 + дни, N))
            R.append((s.index[i], "long" if лонг else "short",
                      int(SL.iloc[i]) if лонг else int(SS.iloc[i]), п,
                      float(мъртъв[окно].mean()) if дни > 0 else 0.0,
                      float(невъзм[окно].mean()) if дни > 0 else 0.0, дни))
    out[им] = pd.DataFrame(R, columns=["ден", "посока", "стрийк", "нето", "дял_мъртви", "дял_невъзм", "дни"])

T = out["сурово"]; F = out["поправено"]
КЛ = {"day1": lambda g: g["стрийк"] == 1, "fresh": lambda g: g["стрийк"].between(2, 3),
      "mixed": lambda g: g["стрийк"] == 0, "stale": lambda g: g["стрийк"] >= 4}

print("=" * 100)
print("A · «РЪБЪТ» РАСТЕ ЛИ С ДЕЛА МЪРТВИ БАРОВЕ В ПРОЗОРЕЦА НА СДЕЛКАТА (LONG, сурово)")
print("=" * 100)
g = T[T["посока"] == "long"].copy()
g["кофа"] = pd.cut(g["дял_мъртви"], [-.001, .0001, .2, .4, .6, 1.001],
                   labels=["0% мъртви", "0-20%", "20-40%", "40-60%", ">60%"])
print(f"  {'кофа':12s} {'n':>6s} {'нето':>9s} {'печели':>8s} {'дни':>6s} {'дял 2000-2012':>14s}")
for k, v in g.groupby("кофа"):
    if len(v) == 0: continue
    print(f"  {str(k):12s} {len(v):6,d} {v['нето'].mean():+9.4f} {(v['нето']>0).mean()*100:7.1f}% "
          f"{v['дни'].mean():6.1f} {(v['ден'] < '2013-01-01').mean()*100:13.1f}%")
print()
print("  → ако нето расте с дела мъртви барове, «ръбът» е НЕВИДИМИ СТОПОВЕ, не пазар.")
print()

print("=" * 100)
print("B · СЪЩОТО, но САМО В РАННАТА ЕПОХА (2000-2012) — за да не бърка епоха с качество")
print("=" * 100)
e = g[g["ден"] < "2013-01-01"]
print(f"  {'кофа':12s} {'n':>6s} {'нето':>9s}   |   късна епоха 2013-2026")
l = g[g["ден"] >= "2013-01-01"]
for k in ["0% мъртви", "0-20%", "20-40%", "40-60%", ">60%"]:
    a = e[e["кофа"] == k]; b = l[l["кофа"] == k]
    print(f"  {k:12s} {len(a):6,d} {a['нето'].mean() if len(a) else float('nan'):+9.4f}   |   "
          f"n={len(b):5,d} нето {b['нето'].mean() if len(b) else float('nan'):+.4f}")
print()

print("=" * 100)
print("C · СЪЩИТЕ КЛЕТКИ ВЪРХУ ФИЗИЧЕСКИ ВЪЗМОЖНИ БАРОВЕ (H≥max(O,C,C₋₁), L≤min(O,C,C₋₁))")
print("=" * 100)
print(f"  {'посока':6s} {'клетка':7s} {'n':>6s} {'СУРОВО нето':>12s} {'ПОПРАВЕНО нето':>15s} {'промяна':>9s}")
for d in ("long", "short"):
    for им, ф in КЛ.items():
        a = T[(T["посока"] == d) & ф(T)]; b = F[(F["посока"] == d) & ф(F)]
        if len(a) < 30: continue
        print(f"  {d:6s} {им:7s} {len(a):6,d} {a['нето'].mean():+12.4f} {b['нето'].mean():+15.4f} "
              f"{b['нето'].mean()-a['нето'].mean():+9.4f}")
print()
print("=" * 100)
print("D · ЕПОХИТЕ ВЪРХУ ПОПРАВЕНИ БАРОВЕ · LONG, СУРОВО нето (без спред)")
print("=" * 100)
print(f"  {'клетка':7s} {'СУРОВИ БАРОВЕ 00-12 / 13-26':>32s} {'ПОПРАВЕНИ БАРОВЕ 00-12 / 13-26':>34s}")
for им, ф in КЛ.items():
    a = T[(T["посока"] == "long") & ф(T)]; b = F[(F["посока"] == "long") & ф(F)]
    a1 = a[a["ден"] < "2013-01-01"]["нето"].mean(); a2 = a[a["ден"] >= "2013-01-01"]["нето"].mean()
    b1 = b[b["ден"] < "2013-01-01"]["нето"].mean(); b2 = b[b["ден"] >= "2013-01-01"]["нето"].mean()
    print(f"  {им:7s} {a1:+15.4f} / {a2:+14.4f} {b1:+16.4f} / {b2:+16.4f}")
print()
print("=" * 100)
print("E · ЕПОХАТА В ЕДНОРОДНО КАЧЕСТВО · само 2011-2026 (мъртви барове 5-28%, не 38-54%),")
print("    разделено 2011-2018 / 2019-2026 — сменя ли се пак знакът?")
print("=" * 100)
for им, ф in КЛ.items():
    for наб, ет in ((T, "сурово"), (F, "поправено")):
        x = наб[(наб["посока"] == "long") & ф(наб) & (наб["ден"] >= "2011-01-01")]
        p = x[x["ден"] < "2019-01-01"]["нето"]; q = x[x["ден"] >= "2019-01-01"]["нето"]
        if len(p) < 30 or len(q) < 30:
            print(f"  {им:7s} {ет:10s} малко"); continue
        зн = "🔴 РАЗЛИЧЕН" if np.sign(p.mean()) != np.sign(q.mean()) else "⚖️ еднакъв"
        print(f"  {им:7s} {ет:10s} 2011-2018 {p.mean():+.4f} (n={len(p):4d}) · "
              f"2019-2026 {q.mean():+.4f} (n={len(q):4d})  {зн}")
