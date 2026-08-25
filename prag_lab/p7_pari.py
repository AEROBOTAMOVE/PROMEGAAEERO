# -*- coding: utf-8 -*-
"""P7: СДВОЕНО ПО ПАРИ. Един и същ симулатор (gh._one_trade, доставената геометрия)
върху ОБЕДИНЕНИЕТО от 10013 чекпойнта. После всяка конфигурация на праговете е
САМО ПОДИЗБОР от този кеш → разликата не може да идва от друга извадка."""
import sys, json, time
import numpy as np, pandas as pd
sys.path.insert(0,"izmervane")
import geom_harness as gh

U=np.array(json.load(open("prag_lab/_union.json")),dtype=np.int64)
ls=np.load("prag_lab/_ls.npy").astype(np.int16); ss=np.load("prag_lab/_ss.npy").astype(np.int16)
tsmin_cp=np.load("prag_lab/_ts.npy").astype(np.int64)
direction=np.where(ls>ss,1,np.where(ss>ls,-1,0)).astype(np.int8)

B=gh.load_tape()
want=tsmin_cp[U]+15
j=np.searchsorted(B["tsmin"],want,side="left")
ok=j<len(B["tsmin"])
gap=np.where(ok,B["tsmin"][np.clip(j,0,len(B["tsmin"])-1)]-want,10**9)
ok&=gap<=120
print(f"[вход] от {len(U):,} чекпойнта изпълними {int(ok.sum()):,}  (отпаднали {int((~ok).sum()):,})")

t0=time.time(); NET={}; NFILL={}; KIND={}; DAY={}
for p in range(len(U)):
    if not ok[p]: continue
    i0=int(j[p]); dr="long" if direction[U[p]]==1 else "short"
    px=float(B["oa"][i0] if dr=="long" else B["ob"][i0])
    r=gh._one_trade(i0,dr,px,gh.GEOM_SHIPPED,B)
    if r is None: continue
    cp=int(U[p]); NET[cp]=r["net"]; NFILL[cp]=r["n_fills"]; KIND[cp]=r["kind"]; DAY[cp]=int(B["dord"][i0])
    if p%1500==0: print(f"   {p}/{len(U)}  {time.time()-t0:.0f}s",flush=True)
print(f"[сделки] пресметнати {len(NET):,}  ({time.time()-t0:.0f}s)")
json.dump({"net":{str(k):v for k,v in NET.items()},
           "day":{str(k):v for k,v in DAY.items()},
           "kind":{str(k):v for k,v in KIND.items()},
           "dir":{str(k):int(direction[k]) for k in NET}},
          open("prag_lab/_trades.json","w"))
print("записано prag_lab/_trades.json")
