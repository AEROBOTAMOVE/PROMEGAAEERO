# -*- coding: utf-8 -*-
"""Истинският път: сетъп от СКАНИРАЙ (не ръчен) + мерено от РЕАЛНИЯ backtest_stats."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.argv = ["x"]
import numpy as np, pandas as pd
import live_bot as lb
CB = lb.CB
stats = json.loads(open("backtest_stats.json", encoding="utf-8").read())

rng = np.random.default_rng(7)
n = 1500
c = 2000 + np.cumsum(rng.normal(0, 1.2, n))
D = pd.DataFrame({"open": c, "high": c + 1.5, "low": c - 1.5, "close": c,
                  "volume": rng.uniform(1, 3, n)},
                 index=pd.date_range("2024-01-01", periods=n, freq="15min"))
W = 400
намерен = None
for k in range(W, len(D), 3):
    r = CB.сканирай({"15м": D.iloc[k-W:k]}, сега=None)
    if r:
        намерен = r[0]; break
print("сетъп от сканирай:", намерен is not None,
      "| праща =", намерен and намерен.get("праща"),
      "| точки =", намерен and намерен.get("точки"),
      "| ранг =", намерен and намерен.get("ранг"))

# ТОЧНО както прави ботът на ред 3712-3713
_bcell = lb._cell_name(1)      # day1 — реална кофа от streaks
_m = CB.мерено_от_стата(stats, _bcell, намерен["лонг"])
print("кофа:", _bcell, "| мерено:", _m)

без = CB.карта(намерен, мерено=None, ранг_вход=lb.МОЗЪК_РАНГ_ВХОД)
със_ = CB.карта(намерен, мерено=_m, ранг_вход=lb.МОЗЪК_РАНГ_ВХОД)
print("\n--- КАРТА (истински сетъп, БЕЗ мерено) ---")
print(без)
print("\nБАЙТ-ЕДНАКВИ:", без.encode() == със_.encode(),
      "| дължини:", len(без), len(със_))
for поле in ("n", "win", "net", "ci", "кофа"):
    v = str((_m or {}).get(поле))
    print("   има ли %s=%s в текста: %s" % (поле, v, v in със_))

# всички 8 реални комбинации
разлики = 0
for кофа in ("day1", "fresh", "stale", "mixed"):
    for лонг in (True, False):
        м = CB.мерено_от_стата(stats, кофа, лонг)
        if CB.карта(намерен, мерено=м) != CB.карта(намерен, мерено=None):
            разлики += 1
print("\nразлики в текста при 8-те реални кофи:", разлики, "от 8")
