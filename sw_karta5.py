# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.argv=["x"]
import live_bot as lb
import numpy as np, pandas as pd
CB = lb.CB
stats = json.load(open("backtest_stats.json", encoding="utf-8"))

# ── РЕАЛНИЯТ ПРОИЗВОДИТЕЛ: сканирай() на бота, не ръчен речник ──
найдени = []
for seed in range(60):
    rng = np.random.default_rng(seed)
    n = 900
    c = 2000 + np.cumsum(rng.normal(0, 1.5, n))
    df = pd.DataFrame({"open": c, "high": c + rng.uniform(0.5,3,n),
                       "low": c - rng.uniform(0.5,3,n), "close": c,
                       "volume": rng.uniform(1, 5, n)},
                      index=pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC"))
    s = CB.сканирай({"15м": df})
    for x in s:
        найдени.append((seed, x))
    if len(найдени) >= 40:
        break
print("сетъпи от РЕАЛНИЯ сканирай():", len(найдени))
рангове = sorted({int(x.get("ранг",0)) for _,x in найдени})
print("рангове:", рангове, " точки:", sorted({x["точки"] for _,x in найдени})[:12])

def оцени(txt):
    return dict(ред=len(txt.split("\n")),
                има_кръстче="✗" in txt,
                има_мерено=("n=" in txt or "мерено" in txt.lower()),
                има_НОВО=("НОВО" in txt or "ново · " in txt),
                степен_първа=None)

# вземи най-силния
найдени.sort(key=lambda t: -t[1]["точки"])
for seed, s in найдени[:1]:
    _m = CB.мерено_от_стата(stats, "stale", s.get("лонг", s.get("посока")=="ДЪЛГО"))
    print("\nподадено мерено:", _m)
    for ранг_вход, етикет in ((3,"както е в бота (МОЗЪК_РАНГ_ВХОД=%s)"%lb.МОЗЪК_РАНГ_ВХОД),):
        pass
    # А) точно както live_bot вика — с лот
    for лот in (None, "📏 нивото иска 45 пипса (4.50$) място"):
        for ранг in (0, 5):
            s2 = dict(s); s2["ранг"]=ранг
            s2["_карта_вход"]=dict(s["_карта_вход"]); s2["_карта_вход"]["ранг"]=ранг
            t = CB.карта(s2, мерено=_m, изместване=0.0, час_сега="21:30",
                         лот=лот, ранг_вход=lb.МОЗЪК_РАНГ_ВХОД)
            print("\n--- ранг=%d лот=%s ---" % (ранг, bool(лот)))
            print(t)
            print("   >> ✗:%s  мерено(n=):%s  НОВО:%s  съотношение(×):%s" % (
                "✗" in t, "n=" in t, "НОВО" in t, "×" in t))
print("\nМОЗЪК_РАНГ_ВХОД =", lb.МОЗЪК_РАНГ_ВХОД)
