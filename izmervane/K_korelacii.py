# -*- coding: utf-8 -*-
"""ЗЛАТОТО СРЕЩУ ДОЛАРА, ЛИХВИТЕ, АКЦИИТЕ, СТРАХА И МИНЬОРИТЕ.

Собственикът: «никога не сме проверявали каква е връзката и на ценните книжа
със златото — DXY и там ценни книжа и долар, всичко е свързано със златото.
Пример бяха вчерашните новини, които движат само тези неща в дадена посока».

ДВА РАЗЛИЧНИ ВЪПРОСА, които обикновено се бъркат:
  А · СЪЩИЯ ДЕН — движат ли се заедно. Това е ОПИСАНИЕ, не предсказание.
  Б · УТРЕ — движението ДНЕС казва ли нещо за златото УТРЕ. САМО това е ръб.
Мерим и двете, отделно, и казваме кое какво е.
"""
import urllib.request, urllib.parse, json, sys
import numpy as np, pandas as pd

ТИК = {"злато": "GC=F", "долар": "DX-Y.NYB", "лихва10г": "^TNX",
       "акции": "^GSPC", "технологии": "^IXIC", "страх": "^VIX", "миньори": "GDX"}
SEED = 20260905
REPS = 5000


def тегли(т, обхват="max"):
    # 🔴 range=max връща МЕСЕЧНИ барове (Yahoo ги прорежда) — 268 реда за 26
    # години. Явните period1/period2 дават ИСТИНСКИ дневни.
    import time as _t
    u = ("https://query1.finance.yahoo.com/v8/finance/chart/%s"
         "?period1=1104537600&period2=%d&interval=1d"
         % (urllib.parse.quote(т, safe=""), int(_t.time())))
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(r, timeout=30) as f:
        d = json.loads(f.read().decode())
    res = d["chart"]["result"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s").normalize()
    c = res["indicators"]["quote"][0]["close"]
    s = pd.Series(c, index=idx, dtype="float64").dropna()
    return s[~s.index.duplicated(keep="last")]


редове = {}
for име, т in ТИК.items():
    try:
        s = тегли(т)
        редове[име] = s
        print("  %-12s %5d дни · %s → %s" % (име, len(s), s.index[0].date(), s.index[-1].date()))
    except Exception as e:
        print("  %-12s 🔴 %s" % (име, type(e).__name__))

D = pd.DataFrame(редове).dropna(how="all")
D = D[D.index >= "2006-01-01"]
Р = D.pct_change() * 100.0          # дневна промяна В ПРОЦЕНТИ
Р = Р.replace([np.inf, -np.inf], np.nan)
print()
print("общи дни с всички редове:", int(Р.dropna().shape[0]))


def бут(x, y, reps=REPS, seed=SEED):
    """Интервал за корелацията, преизбиране ПО ДНИ (всеки ден е един блок)."""
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 60:
        return np.nan, np.nan, np.nan, len(x)
    rng = np.random.default_rng(seed)
    n = len(x)
    iz = rng.integers(0, n, size=(reps, n))
    xs, ys = x[iz], y[iz]
    xs = xs - xs.mean(1, keepdims=True); ys = ys - ys.mean(1, keepdims=True)
    r = (xs * ys).sum(1) / np.sqrt((xs ** 2).sum(1) * (ys ** 2).sum(1))
    return (float(np.corrcoef(x, y)[0, 1]), float(np.percentile(r, 2.5)),
            float(np.percentile(r, 97.5)), n)


def ред(име, x, y):
    c, lo, hi, n = бут(np.asarray(x, float), np.asarray(y, float))
    if not np.isfinite(c):
        return "  %-14s малко данни" % име
    зн = "✅" if lo > 0 else ("🛑" if hi < 0 else "⚪")
    return "  %-14s n=%-5d  %+6.3f  [%+6.3f, %+6.3f]  %s" % (име, n, c, lo, hi, зн)


З = Р["злато"].values
print()
print("═" * 74)
print("А · СЪЩИЯ ДЕН · движат ли се ЗАЕДНО (описание, НЕ предсказание)")
print("═" * 74)
for име in ТИК:
    if име == "злато" or име not in Р:
        continue
    print(ред(име, Р[име].values, З))

print()
print("═" * 74)
print("Б · УТРЕ · движението ДНЕС казва ли нещо за ЗЛАТОТО УТРЕ (това е ръб)")
print("═" * 74)
З_утре = Р["злато"].shift(-1).values
for име in ТИК:
    if име == "злато" or име not in Р:
        continue
    print(ред(име, Р[име].values, З_утре))
print(ред("самото злато", З, З_утре))

print()
print("═" * 74)
print("В · СЪЩИЯ ДЕН, ПО ЕПОХИ · сменя ли се знакът")
print("═" * 74)
ЕП = [(2006, 2010), (2011, 2015), (2016, 2020), (2021, 2026)]
for име in ("долар", "лихва10г", "акции", "страх", "миньори"):
    if име not in Р:
        continue
    _р = ["  %-10s" % име]
    for a, b in ЕП:
        m = (Р.index.year >= a) & (Р.index.year <= b)
        c, lo, hi, n = бут(Р[име].values[m], З[m])
        _р.append("%s%+.2f" % ("✅" if lo > 0 else ("🛑" if hi < 0 else "⚪"), c)
                  if np.isfinite(c) else "  —  ")
    print("  ".join(_р) + "     (" + " · ".join("%d-%d" % e for e in ЕП) + ")")

print()
print("═" * 74)
print("Г · ГОЛЕМИТЕ ДНИ · когато ДОЛАРЪТ мръдне силно, какво прави ЗЛАТОТО СЛЕД ТОВА")
print("═" * 74)
for име in ("долар", "лихва10г", "акции"):
    if име not in Р:
        continue
    x = Р[име].values
    m = np.isfinite(x) & np.isfinite(З_утре)
    if m.sum() < 200:
        continue
    п = np.nanpercentile(np.abs(x[m]), 85)
    for знак, етикет in ((1, "силно НАГОРЕ"), (-1, "силно НАДОЛУ")):
        sel = m & (np.sign(x) == знак) & (np.abs(x) >= п)
        v = З_утре[sel]
        v = v[np.isfinite(v)]
        if len(v) < 40:
            continue
        rng = np.random.default_rng(SEED)
        bm = v[rng.integers(0, len(v), size=(REPS, len(v)))].mean(1)
        lo, hi = np.percentile(bm, [2.5, 97.5])
        зн = "✅" if lo > 0 else ("🛑" if hi < 0 else "⚪")
        print("  %-10s %-14s n=%-4d злато УТРЕ %+6.3f%%  [%+6.3f, %+6.3f]  %s"
              % (име, етикет, len(v), v.mean(), lo, hi, зн))
