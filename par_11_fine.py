# -*- coding: utf-8 -*-
import sys, io
sys.argv=["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd, numpy as np
import live_bot as lb

print("=== ЕДИНИЦИ: fast_g и _bar_range зависят от РАМКАТА на `fine` ===")
print("код: fine = frames['1мин'] ако има, ИНАЧЕ frames['5м']")
print("     d10 = |Close[-1] - Close[-11]|   → 10 БАРА, не 10 минути")
print("     _fast() печата: 'бърз пазар ±$X/10мин'\n")

for име, стъпка in (("1мин", 1), ("5м", 5)):
    n=60
    idx=pd.date_range("2026-08-18 10:00", periods=n, freq=f"{стъпка}min")
    # цена, която се движи по 1.2$ на бар
    c = 4400 + np.arange(n)*1.2
    df=pd.DataFrame({"Open":c,"High":c+0.6,"Low":c-0.6,"Close":c}, index=idx)
    d10 = abs(float(df["Close"].iloc[-1]) - float(df["Close"].iloc[-11]))
    fast = round(d10,1) if d10>=10 else None
    реални_мин = 10*стъпка
    print("  fine = %-5s : d10=%.1f$ покрива %d МИНУТИ; картата казва: '%s'"
          % (име, d10, реални_мин, (lb._fast(fast) or "").strip()))
    print("       _bar_range(fine,5) = %.2f$ (диапазон на 5 бара = %d мин) → влиза в допуска на _spot_sane"
          % (lb._bar_range(df,5), 5*стъпка))
print()
print("  → При отпаднал 1-мин поток числото покрива 50 мин, а думата казва 10 мин.")
