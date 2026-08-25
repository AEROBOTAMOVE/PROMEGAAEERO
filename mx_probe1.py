# -*- coding: utf-8 -*-
import sys, json, io
sys.argv=["x"]; sys.stdout=io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import live_bot as lb
st=json.load(open("backtest_stats.json",encoding="utf-8"))
print("PIP",lb.PIP,"SL_PIPS",lb.SL_PIPS,"SL_D",lb.SL_D)
print("TPS",lb.TPS)
print("S_TPS",lb.S_TPS)
print("ZONE_W",lb.ZONE_W,"МАЛЪК",getattr(lb,"МАЛЪК_РАЗМЕР_W",None),"MIN_N",lb.MIN_N)
print("СТОЯЩ_МАКС_Ч",lb.СТОЯЩ_МАКС_Ч,"REOFFER_MAX_AGE_H",lb.REOFFER_MAX_AGE_H,"REOFFER_H",lb.REOFFER_H)
m=st.get("_meta",{})
print("тишина:",json.dumps(m.get("тишина_мерена"),ensure_ascii=False))
for k in ("fresh",):
    for d in ("long","short"):
        for b,v in st.get(k,{}).get(d,{}).items():
            if isinstance(v,dict):
                print(k,d,b,{x:v.get(x) for x in ("win","net","n","lo","hi","дни")})
