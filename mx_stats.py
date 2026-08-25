# -*- coding: utf-8 -*-
import mx_env, json
s = json.load(open("backtest_stats.json", encoding="utf-8"))
def walk(d, p=""):
    if isinstance(d, dict):
        for k,v in d.items():
            walk(v, p+"/"+str(k))
    else:
        print(p, "=", d)
walk(s)
