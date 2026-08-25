# -*- coding: utf-8 -*-
import sys, io, importlib.util, time, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pandas as pd, numpy as np, yfinance as yf, datetime as dt
sys.path.insert(0,"brain")
def _yf(s,p,i):
    df=yf.download(s,period=p,interval=i,progress=False,auto_adjust=True)
    df.columns=[a if isinstance(a,str) else a[0] for a in df.columns]
    idx=pd.DatetimeIndex(df.index)
    if idx.tz is not None: idx=idx.tz_convert("UTC")
    df.index=idx.tz_localize(None) if idx.tz is not None else idx
    return df.dropna(subset=["Close"])
m5=_yf("GC=F","60d","5m")
_bagg=dict(Open=("Open","first"),High=("High","max"),Low=("Low","min"),Close=("Close","last"),Volume=("Volume","sum"))
d15=m5.resample("15min").agg(**_bagg).dropna()
sp=importlib.util.spec_from_file_location("cb","brain/chart_brain.py"); CB=importlib.util.module_from_spec(sp); sp.loader.exec_module(CB)
SL=CB.SL
d,_=CB._подготви(d15,"15м")
N=int(sys.argv[1]) if len(sys.argv)>1 else 200
t0=time.time()
рез=[]
for k in range(N):
    край=len(d)-N+k+1
    w=d.iloc[max(0,край-CB.ПРОЗОРЕЦ):край]
    if len(w)<CB.МИН_БАРОВЕ: continue
    R,_,гр=CB._прочети(w,"15м")
    карти=SL.f_сливане(w,R,праг_карта=0)
    for c in карти:
        у=c["всички_условия"]
        ж=sum(1 for k2 in ("J1_обем_над","J1b_обем_голям","J2_скок") if у.get(k2))
        рез.append((c["точки"],min(3,ж),c["лонг"]))
dt_=time.time()-t0
print(f"обходени {N} бара за {dt_:.1f}с · карти(повод-барове): {len(рез)}")
if рез:
    tot=[a for a,_,_ in рез]; ж=[b for _,b,_ in рез]
    import statistics
    print(f"точки: медиана {statistics.median(tot)} макс {max(tot)}")
    print(f"Ж принос: среден {sum(ж)/len(ж):.3f} · >0 при {sum(1 for x in ж if x>0)}/{len(ж)} = {sum(1 for x in ж if x>0)/len(ж)*100:.1f}%")
    for T in (11,12,14,16):
        сега=sum(1 for a,b,_ in рез if a>=T)
        безЖ=sum(1 for a,b,_ in рез if (a-b)>=T)
        print(f"праг {T}: с Ж {сега} карти · без Ж {безЖ} карти · загуба {сега-безЖ} ({(сега-безЖ)/max(1,сега)*100:.0f}%)")
