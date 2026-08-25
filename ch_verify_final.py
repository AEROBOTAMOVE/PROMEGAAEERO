# -*- coding: utf-8 -*-
import sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.argv=["x"]
import live_bot as lb
S=json.load(open("backtest_stats.json",encoding="utf-8"))
f=S["fresh"]
for d in ("long","short"):
    for c in ("day1","fresh","stale","mixed","near_high"):
        seg=f.get(d,{}).get(c)
        if not seg: continue
        print(d,c,{k:seg.get(k) for k in ("n","net","win","lo","hi","дни")})
print("PIP",lb.PIP,"SL_D",lb.SL_D,"SL_PIPS",lb.SL_PIPS,"TPS",lb.TPS)
print("MIN_N",getattr(lb,"MIN_N",None),"MALUK",getattr(lb,"МАЛЪК_РАЗМЕР_W",None))
print("ZONE_W",getattr(lb,"ZONE_W",None))
print("СТОЯЩ_МАКС_Ч",getattr(lb,"СТОЯЩ_МАКС_Ч",None))
print("тишина",S.get("тишина_мерена"))
# gate trace live
tr={}
txt,ok=lb._advice_entry("long",1,S,None,False,0,sym="XAUUSD",stale_price=False,dd20=0.05,trace=tr)
print("TRACE day1:",txt,ok,tr)
tr2={}
txt2,ok2=lb._advice_entry("long",0,S,None,False,0,sym="XAUUSD",stale_price=False,dd20=0.05,trace=tr2)
print("TRACE mixed:",txt2,ok2,tr2)
tr3={}
txt3,ok3=lb._advice_entry("long",7,S,None,False,0,sym="XAUUSD",stale_price=False,dd20=0.05,trace=tr3)
print("TRACE stale:",txt3,ok3,tr3)
