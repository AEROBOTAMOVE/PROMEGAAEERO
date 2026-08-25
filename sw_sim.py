# -*- coding: utf-8 -*-
import sys; sys.argv=["x"]
import live_bot as lb, pandas as pd
SOF="Europe/Sofia"
def наивно(a,b):
    A=pd.Timestamp(a).tz_localize('UTC').tz_convert(SOF); B=pd.Timestamp(b).tz_localize('UTC').tz_convert(SOF)
    return ((B.hour*60+B.minute)-(A.hour*60+A.minute))%1440
старт=pd.Timestamp("2026-01-05T00:00")
пали=[]; 
# всеки старт на 1 час през годината, всяка дупка от 1ч до 72ч на стъпка 1ч
for i in range(0, 24*112, 1):
    a=старт+pd.Timedelta(hours=i)
    for h in range(1,73,2):
        b=a+pd.Timedelta(hours=h)
        tm=lb._търговски_минути(a.isoformat(),b.isoformat())
        if tm>=lb.СПАЛ_МИН and not lb._market_closed(b.isoformat()):
            пали.append((tm,h*60,наивно(a,b)))
import collections
n=len(пали)
def дял(f): 
    k=sum(1 for x in пали if f(x)); return f"{k:,} ({100*k/n:.1f}%)"
print(f"комбинации, при които картата ПАЛИ: {n:,}")
print(f"  разминаване заглавие↔'от..до' > 60 мин : {дял(lambda x: abs(x[0]-x[2])>60)}")
print(f"  разминаване > 120 мин                  : {дял(lambda x: abs(x[0]-x[2])>120)}")
print(f"  разминаване > 6 часа                   : {дял(lambda x: abs(x[0]-x[2])>360)}")
print()
for гр,(lo,hi) in [("стенна дупка <24ч",(0,1440)),("24-48ч",(1440,2880)),(">=48ч",(2880,10**9))]:
    под=[x for x in пали if lo<=x[1]<hi]
    if not под: print(f"{гр}: 0"); continue
    b60=sum(1 for x in под if abs(x[0]-x[2])>60)
    print(f"{гр}: пали {len(под):,} · с разминаване >60мин: {b60:,} ({100*b60/len(под):.1f}%)")
print()
# минималната стенна дупка, при която изобщо има разминаване >60 мин
m=[x[1] for x in пали if abs(x[0]-x[2])>60]
print(f"НАЙ-МАЛКАТА стенна дупка с разминаване >60 мин: {min(m)/60:.0f}ч" if m else "няма")
