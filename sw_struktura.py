# -*- coding: utf-8 -*-
import sys,io,importlib.util
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
import pandas as pd,numpy as np,yfinance as yf
sys.path.insert(0,"brain")
def _yf(s,p,i):
    df=yf.download(s,period=p,interval=i,progress=False,auto_adjust=True)
    df.columns=[a if isinstance(a,str) else a[0] for a in df.columns]
    idx=pd.DatetimeIndex(df.index)
    if idx.tz is not None: idx=idx.tz_convert("UTC")
    df.index=idx.tz_localize(None) if idx.tz is not None else idx
    return df.dropna(subset=["Close"])
m1=_yf("GC=F","7d","1m"); m5=_yf("GC=F","60d","5m")
_bagg=dict(Open=("Open","first"),High=("High","max"),Low=("Low","min"),Close=("Close","last"),Volume=("Volume","sum"))
d15=m5.resample("15min").agg(**_bagg).dropna()
d1h=m5.resample("60min").agg(**_bagg).dropna()
sp=importlib.util.spec_from_file_location("b6","brain/b_обеми.py"); B6=importlib.util.module_from_spec(sp); sp.loader.exec_module(B6)
W=1200
print(f"{'рамка':6s} {'бара':>6s} {'слот/ден':>8s} {'МАКС появявания на слот в 1200-бар прозорец':>10s}   нужни>=6?   мин.прозорец")
for име,df in (("1мин",m1),("5м",m5),("15м",d15),("1час",d1h)):
    t=pd.DatetimeIndex(df.index)
    ст=B6._стъпка_минути(t); k=B6._ключове(t,ст)
    маx=0; позиции_готови=0; общо=0
    for i in range(W,len(k)):
        окно=k[i-W:i]          # СТРОГО предишните 1199 + текущия слой
        c=int((окно==k[i]).sum())
        маx=max(маx,c); общо+=1
        if c>=6: позиции_готови+=1
    слотове_ден=len(set(k[:len(k)]))  # груба
    # минимален прозорец = 6 * (брой различни слота в едно денонощие)
    ден=t.normalize()
    слот_в_ден=int(pd.Series(k).groupby(pd.Series(ден)).nunique().median())
    print(f"{име:6s} {len(df):6d} {слот_в_ден:8d} {маx:10d}            "
          f"{позиции_готови}/{общо}      {6*слот_в_ден}")
