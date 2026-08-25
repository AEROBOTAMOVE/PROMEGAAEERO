# -*- coding: utf-8 -*-
import sys, json, warnings
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore"); sys.path.insert(0,".")
import brain.b_сливане as SL
r=json.load(open("sw_full.json",encoding="utf-8"))
раз=[]
for x in r:
    d={}
    for к,в in x["всички"].items():
        if в:
            т,г,_=SL.ТАБЛИЦА[к]; d[г]=d.get(г,0)+т
    с_таван=sum(min(с,SL.ТАВАН_ГРУПА[г]) for г,с in d.items())
    без=sum(d.values())
    assert с_таван==x["точки"]
    if с_таван!=без:
        раз.append((x["t"],x["лонг"],с_таван,без,SL.f_степен(с_таван),SL.f_степен(без),d))
print("кандидати, при които ЦЕЛИЯТ механизъм на таваните променя нещо:",len(раз),"от",len(r))
for t,л,а,б,са,сб,d in раз:
    print(f"  {t} лонг={л}: с таван {а} т. ({са[0]}) · без таван {б} т. ({сб[0]}) · групи={d}")
    print(f"    праг 9: {а>=9} → {б>=9}   праг 14 (живият): {а>=14} → {б>=14}   смяна на степен: {са[1]!=сб[1]}")
