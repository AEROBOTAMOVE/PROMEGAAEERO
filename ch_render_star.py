# -*- coding: utf-8 -*-
import sys, json, io, re, html
sys.argv = ["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import live_bot as lb

stats = json.load(open("backtest_stats.json", encoding="utf-8"))
print("PIP", lb.PIP, "SL_PIPS", lb.SL_PIPS, "SL_D", lb.SL_D)
print("TPS", lb.TPS, "S_TPS", lb.S_TPS)
print("ZONE_W", lb.ZONE_W, "МАЛЪК_РАЗМЕР_W", lb.МАЛЪК_РАЗМЕР_W, "MIN_N", lb.MIN_N)
print("СТОЯЩ_МАКС_Ч", lb.СТОЯЩ_МАКС_Ч, "REOFFER_MAX_AGE_H", lb.REOFFER_MAX_AGE_H, "REOFFER_H", lb.REOFFER_H)
for d in ("long","short"):
    for c in ("day1","fresh","stale","mixed"):
        seg = (stats.get("fresh",{}).get(d) or {}).get(c)
        if seg: print(" ", d, c, {k:seg.get(k) for k in ("win","net","n","lo","hi","дни")})
print("_meta тишина:", json.dumps(stats.get("_meta",{}).get("тишина_мерена"), ensure_ascii=False))
