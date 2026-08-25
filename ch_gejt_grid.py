# -*- coding: utf-8 -*-
"""Кои карти ИЗОБЩО могат да съществуват — изпълнен гейт по всички стрийкове."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.argv = ["x"]
import live_bot as lb
from pathlib import Path

S = json.loads(Path("backtest_stats.json").read_text(encoding="utf-8"))
lb._сребро_разход(S, None)

print("ЗЛАТО · без щит, без стоп-пазач, жива цена, без бърз пазар, dd20=None")
print("%-6s %-6s %-6s %-6s  %s" % ("стрийк", "посока", "клетка", "вход?", "текст"))
живи = []
for d in ("long", "short"):
    for s_n in (0, 1, 2, 3, 4, 5, 7):
        tr = {}
        txt, ok = lb._advice_entry(d, s_n, S, 0.0, False, 0, sym="XAUUSD", trace=tr)
        cell = lb._cell_name(s_n)
        print("%-6d %-6s %-6s %-6s  %s" % (s_n, d, cell, "ДА" if ok else "не", txt))
        if ok:
            живи.append((d, s_n, cell))
print()
print("ЖИВИ КОМБИНАЦИИ (карта с вход е възможна САМО тук):")
видени = set()
for d, s_n, cell in живи:
    if (d, cell) in видени:
        continue
    видени.add((d, cell))
    seg = S["fresh"][d][cell]
    print("  %-5s %-6s win=%s%%  net=%s$ = %.1f пипса  95%%: %s..%s$  n=%s дни=%s"
          % (d, cell, seg["win"], seg["net"], seg["net"] / lb.PIP,
             seg.get("lo"), seg.get("hi"), seg["n"], seg.get("дни")))
print()
print("СРЕБРО:")
for d in ("long", "short"):
    txt, ok = lb._advice_entry(d, 1, S, 0.0, False, 0, sym="XAGUSD")
    print("  %-5s -> %s | %s" % (d, "ДА" if ok else "не", txt))
