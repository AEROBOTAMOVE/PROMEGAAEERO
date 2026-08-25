# -*- coding: utf-8 -*-
"""СКЕПТИК · ЖИВИ ДАННИ. Дърпа GC=F точно както live_bot и мери:
1) какъв е ИСТИНСКИЯТ tf_basis сега;
2) какво прави v13.7 срещу v14.0, ако вътре гръмне изключение;
3) КОЛКО ЗНАЧИ замразена стойност — бордът при истинския tf_adj срещу замразения от 02.08.
"""
import sys, os, ast, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, BASE)
os.environ.setdefault("TG_TOKEN", "")

spec = importlib.util.spec_from_file_location("lb", os.path.join(BASE, "live_bot.py"))
lb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lb)
print("внесен live_bot", lb.VERSION)

gold_d = lb._yf("GC=F", "3y", "1d")
m5 = lb._yf("GC=F", "60d", "5m")
print("дневни %d реда · 5м %d реда · последна дневна цена %.2f"
      % (len(gold_d), len(m5), gold_d["Close"].iloc[-1]))

# --- 1) истинският tf_basis сега, през ЖИВАТА функция ---
st = {}; nt = []
истина = lb._tf_basis(st, "tf_basis_g", m5, gold_d, nt)
print("\n1) ЖИВАТА функция върху ЖИВИ данни → tf_basis = %s · бележки=%s" % (истина, nt))

# --- 2) v13.7 срещу v14.0 при изключение вътре, ЖИВИ данни ---
v137_txt = open(os.path.join(HERE, "_v137.py"), encoding="utf-8").read()
NS = {}; exec(compile(v137_txt, "<v13.7>", "exec"), NS)
tf137 = NS["_tf_basis"]
m5_bad = m5.rename(columns={"Close": "close"})     # доставчикът смени името
print("\n2) 60 ръна с изключение вътре, ЖИВИ данни, пазено -3.851 (стойността от 02.08)")
for име, f in (("v13.7", tf137), ("v14.0", lb._tf_basis)):
    s = {"tf_basis_g": -3.851}; n = []
    for _ in range(60):
        v = f(s, "tf_basis_g", m5_bad, gold_d, n)
    print("   %s → стойност %s · бележки %d · state %s" % (име, v, len(n), s))

# --- 3) КОЛКО ЗНАЧИ: бордът при истината срещу замразеното от 02.08 ---
print("\n3) БОРДЪТ: истински tf_adj=%.3f  срещу  ЗАМРАЗЕН от 02.08 = -3.851" % истина)
frames = {"1ден": gold_d, "5м": m5}
for lbl, rule in (("15м", "15min"), ("30м", "30min"), ("1час", "60min"), ("4час", "4h")):
    frames[lbl] = m5.resample(rule).agg(Open=("Open", "first"), High=("High", "max"),
                                        Low=("Low", "min"), Close=("Close", "last")).dropna()
refs = lb._refs(gold_d)
macro = {"миньори": True, "долар": True, "лихви": True}
print("   %-6s | %-22s | %-22s" % ("рамка", "ИСТИНА (tf_adj=%.1f)" % истина, "ЗАМРАЗЕНО (-3.9)"))
разлики = 0
for lbl in ("5м", "15м", "30м", "1час", "4час"):
    fr = frames[lbl]
    a = lb._scores(fr, refs, macro, price_adj=истина)
    b = lb._scores(fr, refs, macro, price_adj=-3.851)
    ра = lb._resolve(a[0], a[1], macro); рб = lb._resolve(b[0], b[1], macro)
    разлика = "РАЗЛИКА" if ра[:3] != рб[:3] else ""
    if разлика: разлики += 1
    print("   %-6s | %-30s | %-30s %s" % (lbl, str(ра[:3]), str(рб[:3]), разлика))
print("   рамки с различен резултат: %d от 5" % разлики)
