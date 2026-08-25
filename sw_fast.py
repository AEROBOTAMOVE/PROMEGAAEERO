# -*- coding: utf-8 -*-
import sys; sys.argv=["x"]
import live_bot as lb, pandas as pd, numpy as np
# 1 година, решетка от 15 мин (същата крачка, която ползва _търговски_минути)
idx=pd.date_range("2026-01-05","2027-01-05",freq="15min")
otvoren=np.array([not lb._market_closed(t.isoformat()) for t in idx])
pref=np.concatenate([[0],np.cumsum(otvoren*15.0)])          # търговски минути
sof=idx.tz_localize('UTC').tz_convert('Europe/Sofia')
minofday=np.array(sof.hour*60+sof.minute)
N=len(idx)
редове=[]
for h in range(1,97):                 # дупки 1..96 часа
    k=h*4                             # на 15 мин
    a=np.arange(0,N-k); b=a+k
    tm=pref[b]-pref[a]                # ТЪРГОВСКИ минути на дупката
    пали=(tm>=lb.СПАЛ_МИН)&otvoren[b] # същото условие като в бота
    if not пали.any(): continue
    наив=(minofday[b][пали]-minofday[a][пали])%1440   # как се чете 'от..до'
    d=np.abs(tm[пали]-наив)
    редове.append((h,пали.sum(),(d>60).sum(),(d>360).sum(),d.max()))
tot=sum(r[1] for r in редове); b60=sum(r[2] for r in редове); b360=sum(r[3] for r in редове)
print(f"ВСИЧКИ палещи комбинации (1 година, дупки 1-96ч, крачка 15мин): {tot:,}")
print(f"  разминаване заглавие ↔ наивен прочит на 'от..до' > 60 мин : {b60:,} ({100*b60/tot:.1f}%)")
print(f"  > 6 часа                                                  : {b360:,} ({100*b360/tot:.1f}%)")
print("\nпо ГОЛЕМИНА на стенната дупка:")
print(f"{'дупка':>7} {'пали':>9} {'>60мин':>9} {'дял':>7} {'макс разлика':>14}")
for h,n,x,y,mx in редове:
    if h in (2,4,8,12,16,20,23,24,25,28,36,48,60,72,96):
        print(f"{h:>5}ч {n:>9,} {x:>9,} {100*x/n:>6.1f}% {mx/60:>12.1f}ч")
първа=[h for h,n,x,y,mx in редове if x>0]
print(f"\nНАЙ-МАЛКАТА стенна дупка, при която изобщо се появява разминаване >60 мин: {min(първа)}ч")
