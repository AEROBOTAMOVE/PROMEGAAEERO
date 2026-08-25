# -*- coding: utf-8 -*-
import json, numpy as np, pandas as pd
T=json.load(open("prag_lab/_trades.json")); P=json.load(open("prag_lab/_picked_all.json"))
NET={int(k):v for k,v in T["net"].items()}; DAY={int(k):v for k,v in T["day"].items()}
tsmin=np.load("prag_lab/_ts.npy")
cps=[c for c in P["4/6"] if c in NET]
t=pd.to_datetime(np.array([tsmin[c] for c in cps])*60,unit="s")
години=(t.max()-t.min()).days/365.25
print(f"обхват на входовете: {t.min().date()} .. {t.max().date()}   = {години:.2f} години")
print(f"{'прагове':>9} {'сделки':>7} {'сделки/год':>11} {'$/сделка':>9} {'$/година (точка)':>17} {'$/година 95%':>26}")
rng=np.random.default_rng(7); ALLD=sorted({DAY[c] for c in NET}); DI={d:i for i,d in enumerate(ALLD)}
for cfg in ["4/6","3/6","3/5","4/5","4/7","5/6","5/7","6/6","6/7","4/4"]:
    cc=[c for c in P[cfg] if c in NET]; net=np.array([NET[c] for c in cc])
    s=np.zeros(len(ALLD)); n=np.zeros(len(ALLD))
    for c in cc: s[DI[DAY[c]]]+=NET[c]; n[DI[DAY[c]]]+=1
    bs=np.empty(4000)
    for r in range(4000):
        p=rng.integers(0,len(ALLD),len(ALLD)); nn=n[p].sum()
        bs[r]=s[p].sum()/nn if nn else np.nan
    lo,hi=np.nanpercentile(bs,[2.5,97.5]); spg=len(net)/години
    print(f"{cfg:>9} {len(net):>7,} {spg:>11.0f} {net.mean():>+9.4f} {net.mean()*spg:>+17.0f} "
          f"[{lo*spg:>+10.0f} .. {hi*spg:>+9.0f}]"+("   <== ЖИВОТО" if cfg=="4/6" else ""))
