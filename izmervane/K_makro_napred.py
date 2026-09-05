# -*- coding: utf-8 -*-
"""ДОКАЗВАТ ЛИ ТРИТЕ МАКРО-КРАЧЕТА ПОСОКА НАПРЕД.

Армията твърди: «нито едно от трите макро-крачета не доказва посока напред —
на 1, 5, 20 или 30 дни, в 22 години». Не съм го проверил сам. Проверявам.

ВАЖНО КАКВО СЕ МЕРИ: гейтът на бота съди по СТРИЙКА (колко дни подред
подреждането е в дадена посока), а стрийкът се смята от 20-ДНЕВНАТА промяна
на долара и лихвите — точно както `_streaks` в live_bot.py.
"""
import urllib.request, urllib.parse, json
import numpy as np, pandas as pd

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0"
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
    s = pd.Series(res["indicators"]["quote"][0]["close"], index=idx, dtype="float64").dropna()
    return s[~s.index.duplicated(keep="last")]


G = тегли("GC=F")
X = тегли("DX-Y.NYB").reindex(G.index).ffill()
T = тегли("^TNX").reindex(G.index).ffill()
M = тегли("GDX").reindex(G.index).ffill()
print("общи дни:", int(pd.concat([G, X, T, M], axis=1).dropna().shape[0]))

# ДОСЛОВНО правилото на бота: макро крак = ДОБРО за златото
крака = {
    "долар (20д)": -(X.pct_change(20)) > 0,       # доларът пада → добро
    "лихви (20д)": -(T.diff(20)) > 0,             # лихвите падат → добро
    "миньори (20д)": (M.pct_change(20)) > 0,      # миньорите растат → добро
}
# и подреждането 3/3 и 0/3
ml = sum(v.astype(int) for v in крака.values())
крака["подредено 3/3"] = ml == 3
крака["подредено 0/3"] = ml == 0

c = G


def напред(дни):
    return (c.shift(-дни) / c - 1.0) * 100.0


def съди(усл, цел, име):
    m = усл.reindex(c.index).fillna(False).values & np.isfinite(цел.values)
    n = int(m.sum())
    if n < 100:
        return "  %-16s n=%-5d малко" % (име, n)
    v = цел.values[m]
    rng = np.random.default_rng(SEED)
    bm = v[rng.integers(0, n, size=(REPS, n))].mean(1)
    lo, hi = np.percentile(bm, [2.5, 97.5])
    зн = "✅" if lo > 0 else ("🛑" if hi < 0 else "⚪")
    return "  %-16s n=%-5d %+6.3f%%  [%+6.3f, %+6.3f]  %s" % (име, n, v.mean(), lo, hi, зн)


for хор in (1, 5, 20, 30):
    ц = напред(хор)
    _база = ц.dropna()
    rng = np.random.default_rng(SEED)
    _bm = _база.values[rng.integers(0, len(_база), size=(REPS, len(_база)))].mean(1)
    _lo, _hi = np.percentile(_bm, [2.5, 97.5])
    print()
    print("═" * 74)
    print("ЗЛАТОТО СЛЕД %d ДНИ · базата (всички дни): %+.3f%% [%+.3f, %+.3f] %s"
          % (хор, _база.mean(), _lo, _hi, "✅" if _lo > 0 else "⚪"))
    print("═" * 74)
    for име, у in крака.items():
        print(съди(у, ц, име))
    # и РАЗЛИКАТА спрямо базата — това е истинският въпрос
    for име in ("подредено 3/3", "подредено 0/3"):
        m = крака[име].reindex(c.index).fillna(False).values & np.isfinite(ц.values)
        if m.sum() < 100:
            continue
        v = ц.values[m]
        о = ц.values[np.isfinite(ц.values) & ~m]
        rng = np.random.default_rng(SEED)
        d = (v[rng.integers(0, len(v), size=(REPS, len(v)))].mean(1)
             - о[rng.integers(0, len(о), size=(REPS, len(о)))].mean(1))
        lo, hi = np.percentile(d, [2.5, 97.5])
        зн = "✅" if lo > 0 else ("🛑" if hi < 0 else "⚪")
        print("  %-16s РАЗЛИКА спрямо останалите дни: %+6.3f%% [%+6.3f, %+6.3f] %s"
              % (име, v.mean() - о.mean(), lo, hi, зн))
