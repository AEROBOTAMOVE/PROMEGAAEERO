# -*- coding: utf-8 -*-
import json, io
d=json.load(io.open("backtest_stats.json",encoding="utf-8"))
def walk(o,p=""):
    if isinstance(o,dict):
        for k,v in o.items():
            walk(v,p+"/"+str(k))
    elif isinstance(o,list):
        print(p,"= list len",len(o), str(o)[:200])
    else:
        print(p,"=",o)
print("TOP KEYS:", list(d.keys()))
print("="*60)
if "_meta" in d: walk(d["_meta"],"_meta")
