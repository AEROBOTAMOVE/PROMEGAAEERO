# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
ls=np.load("prag_lab/_ls.npy"); ss=np.load("prag_lab/_ss.npy"); ok=np.load("prag_lab/_ok.npy")
ts=np.load("prag_lab/_ts.npy")   # минути от епохата
cut=int(pd.Timestamp("2023-07-07").value//10**9//60)   # последни 3 години от лентата
for име,м in (("ЦЯЛАТА ЛЕНТА 2004-2026",ok),("ПОСЛЕДНИТЕ 3 ГОДИНИ 2023-07..2026-07",ok&(ts>=cut))):
    a,b=ls[м],ss[м]
    w=np.where(a>b,a,np.where(b>a,b,-1)); wait=int((w<0).sum()); w=w[w>=0]
    print(f"\n{име}   чекпойнти={int(м.sum()):,}  с посока={len(w):,}  равни(wait)={wait:,}")
    print("   сбор ls+ss:", {int(v):int(((a+b)==v).sum()) for v in np.unique(a+b)})
    for v in range(0,10):
        n=int((w==v).sum())
        if n: print(f"     score={v}: {n:>9,}  {100*n/len(w):6.2f}%  {'#'*int(50*n/len(w))}")
    print(f"     МИН={w.min()}  МАКС={w.max()}")
    # какво реже всеки праг
    for T in (3,4,5,6,7,8):
        print(f"     праг >={T} би отрязал {int((w<T).sum()):>9,} ({100*(w<T).mean():6.2f}%) от клетките с посока")
