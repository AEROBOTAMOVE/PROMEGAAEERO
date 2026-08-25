# -*- coding: utf-8 -*-
import sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.argv=["x"]
import live_bot as lb
CB = lb.CB
print("CB module:", CB.__file__)
stats = json.load(open("backtest_stats.json", encoding="utf-8"))
for cell in ("day1","fresh","stale","mixed"):
    for lo in (True, False):
        m = CB.мерено_от_стата(stats, cell, lo)
        print(cell, "long" if lo else "short", "->", m)
