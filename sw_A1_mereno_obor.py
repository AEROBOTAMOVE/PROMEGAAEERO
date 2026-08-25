# -*- coding: utf-8 -*-
"""Адверсарна проверка на находка 1."""
import sys, json, time, io
sys.stdout.reconfigure(encoding='utf-8')
sys.argv = ["x"]
import live_bot as lb
CB = lb.CB
stats = json.loads(open("backtest_stats.json", encoding="utf-8").read())

print("=== 1) реалната форма на stats (както я чете ботът, ред 2871) ===")
print("ключове на върха:", sorted(stats.keys())[:12])
fr = (stats.get("fresh") or {})
for стр in ("long","short"):
    for к in ("day1","fresh","stale","mixed"):
        s = ((fr.get(стр) or {}).get(к) or {})
        print("  fresh/%s/%-6s n=%s win=%s net=%s" % (стр, к, s.get("n"), s.get("win"), s.get("net")))

print("\n=== 2) колко от 8-те комбинации връщат НЕ-None (живият вход) ===")
жив = 0
for стр in (True, False):
    for к in ("day1","fresh","stale","mixed"):
        м = CB.мерено_от_стата(stats, к, стр)
        print("  лонг=%-5s кофа=%-6s -> %s" % (стр, к, "None" if м is None else "n=%d" % м["n"]))
        жив += (м is not None)
print("  НЕ-None:", жив, "от 8")

print("\n=== 3) цена на «мъртвото смятане» ===")
t=time.perf_counter()
N=20000
for _ in range(N):
    CB.мерено_от_стата(stats, "day1", True)
dt=(time.perf_counter()-t)/N
print("  %.2f микросекунди на карта (%d повторения)" % (dt*1e6, N))
