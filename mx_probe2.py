# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout=io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
st=json.load(open("backtest_stats.json",encoding="utf-8"))
def walk(o,p=""):
    if isinstance(o,dict):
        for k,v in o.items(): walk(v,p+"/"+str(k))
    else:
        pass
print("TOP:",list(st.keys()))
print("fresh/long/day1 keys:",list(st["fresh"]["long"]["day1"].keys()))
print("_meta keys:",list(st.get("_meta",{}).keys()))
import re
s=json.dumps(st,ensure_ascii=False)
for w in ("tp1","reached","трет","плюс","spread","спред","дни"):
    print(w, s.count(w))
