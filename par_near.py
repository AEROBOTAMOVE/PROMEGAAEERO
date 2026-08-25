# -*- coding: utf-8 -*-
import json, io
d=json.load(io.open("backtest_stats.json",encoding="utf-8"))
fr=d["fresh"]
for dirn in ("long","short"):
    print(dirn, list(fr[dirn].keys()))
    print("  near_high:", json.dumps(fr[dirn].get("near_high"),ensure_ascii=False))
    print("  mixed:", json.dumps(fr[dirn].get("mixed"),ensure_ascii=False))
sv=d["silver"]
for dirn in ("long","short"):
    print("silver",dirn, list(sv[dirn].keys()))
    for k in ("fresh","day1","stale","mixed"):
        print("   ",k, json.dumps(sv[dirn].get(k),ensure_ascii=False)[:250])
