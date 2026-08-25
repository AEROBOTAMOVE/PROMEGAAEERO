# -*- coding: utf-8 -*-
"""P5: анти-спам огледалото на geom_harness, параметризирано. Целочислен ключ = dir*10+tier
(еквивалент на низа 'long:strong' — сверявам го срещу низовата версия по-долу)."""
import numpy as np, json, time
ls=np.load("prag_lab/_ls.npy").astype(np.int16); ss=np.load("prag_lab/_ss.npy").astype(np.int16)
ml=np.load("prag_lab/_ml.npy").astype(np.int16); ok=np.load("prag_lab/_ok.npy")
tsmin=np.load("prag_lab/_ts.npy").astype(np.int64)
COOL_MIN=45; COOL_FLIP_MIN=15
direction=np.where(ls>ss,1,np.where(ss>ls,-1,0)).astype(np.int8)
score=np.where(ls>ss,ls,np.where(ss>ls,ss,np.maximum(ls,ss))).astype(np.int16)
m3l=(ml==3); m3s=(ml==0)

def izbor(TM,TS):
    tl=np.where(m3l,3,np.where(ls>=TS,2,np.where(ls>=TM,1,0)))
    tsh=np.where(m3s,3,np.where(ss>=TS,2,np.where(ss>=TM,1,0)))
    tk=np.where(direction==1,tl,np.where(direction==-1,tsh,0)).astype(np.int8)
    act=((direction!=0)&(tk>0)&ok)
    key=(direction.astype(np.int32)*10+tk)          # уникален за (посока,клас)
    idxs=np.flatnonzero(act)
    lk=-999; ld=-9; lt=0; lts=None; picked=[]
    K=key; D=direction; T=tk; TSm=tsmin
    prev=-1
    for i in idxs:
        if prev>=0 and i!=prev+1:
            # между prev и i е имало НЕактивен чекпойнт -> ключът се нулира (live_bot:1439)
            lk=-999
        prev=i
        k=int(K[i]); dr=int(D[i]); tr=int(T[i])
        mins=None if lts is None else (TSm[i]-lts)
        tier_up=(tr>lt) and (dr==ld)
        cool=(mins is None or mins>=COOL_MIN or (dr!=ld and mins>=COOL_FLIP_MIN) or tier_up)
        if (k!=lk or tier_up) and cool:
            picked.append(int(i)); lk,ld,lt,lts=k,dr,tr,TSm[i]
    return np.array(picked,dtype=np.int64), int(act.sum()), tk, act

GRID=[(4,6),(3,5),(5,7),(0,6),(1,6),(2,6),(3,6),(5,6),(6,6),(4,4),(4,5),(4,7),(4,8),(5,8),(6,7),(7,8)]
out={}
print(f"{'TM':>3}{'TS':>4}  {'активни чекп.':>14} {'избрани карти':>14}  {'дълги':>7} {'къси':>7}   {'време':>6}")
for TM,TS in GRID:
    t0=time.time()
    p,na,tk,act=izbor(TM,TS)
    nl=int((direction[p]==1).sum()); ns=int((direction[p]==-1).sum())
    out[f"{TM}/{TS}"]=p.tolist()
    mark="  <== ЖИВОТО" if (TM,TS)==(4,6) else ""
    print(f"{TM:>3}{TS:>4}  {na:>14,} {len(p):>14,}  {nl:>7,} {ns:>7,}   {time.time()-t0:5.1f}s{mark}")
json.dump(out,open("prag_lab/_picked_all.json","w"))
print("записано.")
