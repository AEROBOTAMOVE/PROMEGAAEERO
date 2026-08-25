# -*- coding: utf-8 -*-
import json, io
d=json.load(io.open("backtest_stats.json",encoding="utf-8"))
for blk in ("fresh","silver","ma_bounce"):
    print("#"*70); print(blk, type(d.get(blk)))
    b=d.get(blk) or {}
    for k,v in b.items():
        if isinstance(v,dict):
            print("  ",k, json.dumps(v,ensure_ascii=False)[:300])
        else:
            print("  ",k,"=",str(v)[:300])
