# ИЗПЪЛНЕНИЕ: взимам ИСТИНСКИТЕ редове на блока за дърпане от live_bot.py
# и ги пускам ДВА ПЪТИ - веднъж с пълния TFS, веднъж с "поправения" TFS.
# Броя реалните заявки. Сдвоено: същият код, същите стубове.
import re, textwrap, pandas as pd, numpy as np
src = open('live_bot.py', encoding='utf-8').read().splitlines()
# блокът: от 'frames = {"1ден": gold_d}' до реда с fine =
i0 = next(i for i,l in enumerate(src) if l.strip().startswith('frames = {"1ден"'))
i1 = next(i for i,l in enumerate(src) if l.strip().startswith('fine = frames.get'))
block = textwrap.dedent("\n".join(src[i0:i1+1]))
print("=== ИЗПЪЛНЯВАН БЛОК (редове %d-%d) ===" % (i0+1, i1+1))
print(block)
print("=" * 60)

idx = pd.date_range("2026-08-01", periods=500, freq="1min")
fake = pd.DataFrame({"Open":np.arange(500.0),"High":np.arange(500.0)+1,
                     "Low":np.arange(500.0)-1,"Close":np.arange(500.0)}, index=idx)

def run(tfs, label):
    calls = []
    def _yf(sym, period="2y", interval="1d"):
        calls.append((sym, period, interval)); return fake.copy()
    ns = {"_yf":_yf, "time":__import__("time"), "gold_d":fake.copy(),
          "TFS":tfs, "print":lambda *a,**k:None, "float":float}
    exec(block, ns)
    print(f"[{label}] TFS има {len(tfs)} рамки")
    print(f"[{label}] РЕАЛНИ заявки към Yahoo: {len(calls)} -> {calls}")
    print(f"[{label}] frames ключове: {sorted(ns['frames'].keys())}")
    print(f"[{label}] frames['1мин'] съществува ли: {'1мин' in ns['frames']}")
    return len(calls), ns['frames']

FULL = [("1мин","1m","7d",None),("5м","5m","60d",None),("15м","15m","60d",None),
        ("30м","30m","60d",None),("1час","60m","730d",None),
        ("4час","60m","730d","4h"),("1ден",None,None,None)]
FIXED = FULL[1:]   # тяхната поправка: махнат кортежът на «1мин»

a,_ = run(FULL,  "СТАРО ")
b,_ = run(FIXED, "ПОПРАВЕНО")
print("=" * 60)
print(f"СПЕСТЕНИ ЗАЯВКИ ОТ ПОПРАВКАТА: {a-b}")
