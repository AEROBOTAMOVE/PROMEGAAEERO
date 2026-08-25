# -*- coding: utf-8 -*-
import json, io, sys
d=json.load(io.open("backtest_stats.json",encoding="utf-8"))
fr=d["fresh"]
for dirn in ("long","short"):
    for cell in ("day1","fresh","stale","mixed","near_high"):
        s=fr.get(dirn,{}).get(cell)
        if isinstance(s,dict):
            print(dirn,cell,{k:s.get(k) for k in ("win","net","n","lo","hi","дни")})
print("---тишина---", d.get("тишина_мерена"))
print("---keys---", list(d.keys()))
