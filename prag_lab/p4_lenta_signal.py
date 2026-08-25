# -*- coding: utf-8 -*-
"""P4: разпределението на score-а върху ЛЕНТАТА (15-мин чекпойнти, 2004-2026),
пресметнато с ТОЧНО кода на geom_harness.build_entries, само че ls/ss се ЗАПАЗВАТ."""
import sys, time
import numpy as np, pandas as pd, pyarrow.parquet as pq
sys.path.insert(0,"izmervane")
import geom_harness as gh

t0=time.time()
cols=["timestamp_utc","open_bid","high_bid","low_bid","close_bid","open_ask","high_ask","low_ask","close_ask"]
d=pq.read_table(gh.P15MIN,columns=cols).to_pandas().sort_values("timestamp_utc").reset_index(drop=True)
d["o"]=(d.open_bid+d.open_ask)/2; d["h"]=(d.high_bid+d.high_ask)/2
d["l"]=(d.low_bid+d.low_ask)/2;  d["c"]=(d.close_bid+d.close_ask)/2
ny=d.timestamp_utc.dt.tz_convert("America/New_York")
d["day"]=(ny+pd.Timedelta(hours=7)).dt.normalize().dt.tz_localize(None)
daily=d.groupby("day").agg(Open=("o","first"),High=("h","max"),Low=("l","min"),Close=("c","last"))
idx=daily.index
print(f"[лента] 15-мин барове {len(d):,}   дневни {len(daily)}   {idx[0].date()} .. {idx[-1].date()}")

gdx=pd.read_csv(gh.F_GDX,parse_dates=["Date"]).set_index("Date")["Close"]
dxy=pd.read_csv(gh.F_DXY,parse_dates=["Date"]).set_index("Date")["Close"]
rr=pd.read_csv(gh.F_RR); rr["observation_date"]=pd.to_datetime(rr["observation_date"])
rr["DFII10"]=pd.to_numeric(rr["DFII10"],errors="coerce"); rr=rr.dropna().set_index("observation_date")["DFII10"]
g=daily["Close"]; gd=gdx.reindex(idx).ffill(); dx=dxy.reindex(idx).ffill(); r=rr.reindex(idx).ffill()
raw_min=(gd.pct_change(50)-g.pct_change(50)).shift(1); raw_dol=(-(dx.pct_change(20))).shift(1)
raw_rat=(-(r-r.shift(20))).shift(1)
m_min=(raw_min>0).fillna(False); m_dol=(raw_dol>0).fillna(False); m_rat=(raw_rat>0).fillna(False)
mac_ok=raw_min.notna()&raw_dol.notna()&raw_rat.notna()
R=pd.DataFrame(index=idx)
R["sma50"]=g.rolling(50).mean().shift(1); R["sma20"]=g.rolling(20).mean().shift(1)
R["ago5"]=g.shift(6); R["ago20"]=g.shift(21)
R["low20"]=daily["Low"].rolling(20).min().shift(1); R["high20"]=daily["High"].rolling(20).max().shift(1)
R["n_hist"]=np.arange(len(idx)); R["mac_ok"]=mac_ok.values
R["m_min"]=m_min.values; R["m_dol"]=m_dol.values; R["m_rat"]=m_rat.values
d["run_h"]=d.groupby("day")["h"].cummax(); d["run_l"]=d.groupby("day")["l"].cummin()
X=d.join(R,on="day")
cN,hN,lN=X.c.values,X.run_h.values,X.run_l.values
s50,s20,a5,a20,l20,h20=(X.sma50.values,X.sma20.values,X.ago5.values,X.ago20.values,X.low20.values,X.high20.values)
nn=lambda a:~np.isnan(a)
with np.errstate(invalid="ignore",divide="ignore"):
    lpv=[nn(s50)&(cN>s50), nn(s20)&(cN>s20), nn(a20)&(cN>a20),
         nn(a5)&nn(a20)&(cN/a5-1<0)&(cN/a20-1>0), nn(l20)&(lN<=l20*1.015)]
    spv=[nn(s50)&(cN<s50), nn(s20)&(cN<s20), nn(a20)&(cN<a20),
         nn(a5)&nn(a20)&(cN/a5-1>0)&(cN/a20-1<0), nn(h20)&(hN>=h20*0.985)]
lp=sum(v.astype(np.int8) for v in lpv); sp=sum(v.astype(np.int8) for v in spv)
ml=(X.m_min.values.astype(np.int8)+X.m_dol.values.astype(np.int8)+X.m_rat.values.astype(np.int8))
ls=ml+lp; ss=(3-ml)+sp
ok=(X.n_hist.values>=gh.MIN_HISTORY)&X.mac_ok.values
np.save("prag_lab/_ls.npy",ls); np.save("prag_lab/_ss.npy",ss); np.save("prag_lab/_ml.npy",ml)
np.save("prag_lab/_ok.npy",ok)
X[["timestamp_utc","day"]].to_parquet("prag_lab/_xmeta.parquet",index=False)
np.save("prag_lab/_ts.npy", X.timestamp_utc.values.astype("datetime64[m]").astype(np.int64))

sel=ok
print(f"[лента] чекпойнти с история+живо макро: {sel.sum():,} от {len(X):,}")
tot=ls[sel]+ss[sel]
print()
print("СБОРЪТ ls+ss (структурата, която прави прага 4 недостижим):")
for v in range(0,10):
    n=int((tot==v).sum())
    if n: print(f"   ls+ss={v}: {n:>9,}  {100*n/sel.sum():6.2f}%")
win=np.where(ls[sel]>ss[sel],ls[sel],np.where(ss[sel]>ls[sel],ss[sel],-1))
print()
print("SCORE НА ПОБЕДИТЕЛЯ (dir != wait):")
w=win[win>=0]
for v in range(0,10):
    n=int((w==v).sum())
    if n: print(f"   score={v}: {n:>9,}  {100*n/len(w):6.2f}%  {'#'*int(60*n/len(w))}")
print(f"   МИНИМУМ = {w.min()}   МАКСИМУМ = {w.max()}   N={len(w):,}   равенства(wait)={int((win<0).sum()):,}")
print()
print("Само последните 3 години:")
ts=pd.DatetimeIndex(X.timestamp_utc.values)
m3y=(ts>=pd.Timestamp("2023-01-01",tz="UTC"))&sel
w3=np.where(ls[m3y]>ss[m3y],ls[m3y],np.where(ss[m3y]>ls[m3y],ss[m3y],-1)); w3=w3[w3>=0]
for v in range(0,10):
    n=int((w3==v).sum())
    if n: print(f"   score={v}: {n:>9,}  {100*n/len(w3):6.2f}%")
print(f"   МИНИМУМ = {w3.min()}  МАКСИМУМ = {w3.max()}  N={len(w3):,}")
print(f"({time.time()-t0:.1f}s)")
