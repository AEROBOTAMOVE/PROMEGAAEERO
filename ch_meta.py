# -*- coding: utf-8 -*-
import json, io
d=json.load(io.open("backtest_stats.json",encoding="utf-8"))
m=d["_meta"]
for k,v in m.items():
    s=repr(v)
    print(k,"=",s[:300])
