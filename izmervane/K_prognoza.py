# -*- coding: utf-8 -*-
"""КОЛКО ЧЕСТО ПОЗНАВА ПРОСТА ПРОГНОЗА ЗА ДЕНЯ.

Не искам да измислям прогноза. Мери се КАКВО ПОЗНАВА, преди да излезе на карта:
  1 · ОБХВАТ — «днес ще се движи между X и Y». Проверява се на КОЛКО дни
      цената наистина остава вътре, и колко широк трябва да е поясът.
  2 · ПОСОКА — «по-скоро нагоре/надолу». Проверява се срещу монета (50%).
  3 · СЕДМИЧНО — същото, но за понеделник → петък.
"""
import urllib.request, urllib.parse, json
import numpy as np, pandas as pd

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
SEED, REPS = 20260905, 5000


def тегли(т):
    import time as _t
    u = ("https://query1.finance.yahoo.com/v8/finance/chart/%s"
         "?period1=1104537600&period2=%d&interval=1d"
         % (urllib.parse.quote(т, safe=""), int(_t.time())))
    r = urllib.request.Request(u, headers={"User-Agent": UA})
    with urllib.request.urlopen(r, timeout=30) as f:
        d = json.loads(f.read().decode())
    res = d["chart"]["result"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s").normalize()
    q = res["indicators"]["quote"][0]
    D = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=idx).dropna()
    return D[~D.index.duplicated(keep="last")]


G = тегли("GC=F")
X = тегли("DX-Y.NYB").reindex(G.index).ffill()
print("злато:", len(G), "дни ·", G.index[0].date(), "→", G.index[-1].date())

обхват = (G["high"] - G["low"])
ср20 = обхват.rolling(20).median()
c = G["close"]

print()
print("═" * 78)
print("1 · ОБХВАТ · «днес ще е между X и Y» · пояс = k × медианния обхват от 20 дни")
print("═" * 78)
print("   поясът се строи от ВЧЕРАШНОТО затваряне и ВЧЕРАШНИЯ медианен обхват")
for k in (0.5, 0.75, 1.0, 1.25, 1.5):
    гор = c.shift(1) + k * ср20.shift(1)
    дол = c.shift(1) - k * ср20.shift(1)
    вътре = ((G["close"] >= дол) & (G["close"] <= гор))
    м = гор.notna() & дол.notna()
    # и колко е ШИРОК поясът в долари и в проценти
    ш = (гор - дол)[м]
    print("   k=%.2f · затварянето е ВЪТРЕ в %5.1f%% от %d дни · пояс %6.1f$ (%.2f%%)"
          % (k, 100.0 * вътре[м].mean(), int(м.sum()), ш.median(),
             100.0 * (ш / c.shift(1))[м].median()))
    # и дали ЦЕЛИЯТ ден остава вътре (по-строго)
    цял = ((G["low"] >= дол) & (G["high"] <= гор))
    print("            целият ден вътре: %5.1f%%" % (100.0 * цял[м].mean()))

print()
print("═" * 78)
print("2 · ПОСОКА за ДЕНЯ · срещу монета (50%)")
print("═" * 78)


def дял(усл, цел, име):
    m = усл & цел.notna()
    n = int(m.sum())
    if n < 100:
        return "   %-40s малко (%d)" % (име, n)
    v = (цел[m] > 0).astype(float).values
    rng = np.random.default_rng(SEED)
    bm = v[rng.integers(0, n, size=(REPS, n))].mean(1)
    lo, hi = np.percentile(bm, [2.5, 97.5])
    зн = "✅" if lo > 0.5 else ("🛑" if hi < 0.5 else "⚪")
    return "   %-40s n=%-5d %5.1f%%  [%4.1f, %4.1f]  %s" % (име, n, 100 * v.mean(),
                                                            100 * lo, 100 * hi, зн)


Δ = c.diff()
Δутре = Δ.shift(-1)
дx = X["close"].pct_change() * 100
праг = dx_p = dx_pp = None
_п = dx if False else None
пx = np.nanpercentile(np.abs(дx.dropna().values), 85)
print(дял(pd.Series(True, index=c.index), Δутре, "всички дни (базата)"))
print(дял(c > c.rolling(20).mean(), Δутре, "над 20-дневната средна"))
print(дял(c < c.rolling(20).mean(), Δутре, "под 20-дневната средна"))
print(дял((дx <= -пx), Δутре, "вчера доларът СИЛНО надолу"))
print(дял((дx >= pпx if False else (дx >= пx)), Δутре, "вчера доларът СИЛНО нагоре"))
print(дял((Δ > 0), Δутре, "вчера златото се качи"))
print(дял((Δ < 0), Δутре, "вчера златото падна"))

print()
print("═" * 78)
print("3 · СЕДМИЦАТА · понеделник → петък")
print("═" * 78)
W = G["close"].resample("W-FRI").last()
Wo = G["open"].resample("W-FRI").first()
Wh = G["high"].resample("W-FRI").max()
Wl = G["low"].resample("W-FRI").min()
седм_обхват = (Wh - Wl)
ср_с = седм_обхват.rolling(8).median()
for k in (0.5, 0.75, 1.0, 1.25):
    гор = W.shift(1) + k * ср_с.shift(1)
    дол = W.shift(1) - k * ср_с.shift(1)
    м = гор.notna() & дол.notna()
    вътре = ((W >= дол) & (W <= гор))
    ш = (гор - дол)[м]
    print("   k=%.2f · петъчното затваряне е ВЪТРЕ в %5.1f%% от %d седмици · пояс %6.1f$"
          % (k, 100.0 * вътре[м].mean(), int(м.sum()), ш.median()))
Δw = W.diff()
print()
print(дял(pd.Series(True, index=W.index), Δw.shift(-1), "всяка седмица (базата)"))
print(дял(W > W.rolling(8).mean(), Δw.shift(-1), "над 8-седмичната средна"))
print(дял(W < W.rolling(8).mean(), Δw.shift(-1), "под 8-седмичната средна"))
