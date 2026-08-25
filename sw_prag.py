# -*- coding: utf-8 -*-
import sys; sys.argv=["x"]
import live_bot as lb, pandas as pd, numpy as np
idx=pd.date_range("2026-01-05","2027-01-05",freq="15min")
otv=np.array([not lb._market_closed(t.isoformat()) for t in idx])
pref=np.concatenate([[0],np.cumsum(otv*15.0)])
sof=idx.tz_localize('UTC').tz_convert('Europe/Sofia'); mod=np.array(sof.hour*60+sof.minute)
N=len(idx)
print(f"{'дупка':>6} {'пали':>8} {'ТОЧНИ':>8} {'ЛЪЖЕЩИ':>8}  забележка")
for h in [1,2,4,6,8,12,18,23,23.75,24,24.25,25,30,36]:
    k=int(h*4); a=np.arange(0,N-k); b=a+k
    tm=pref[b]-pref[a]; f=(tm>=lb.СПАЛ_МИН)&otv[b]
    if not f.any(): continue
    d=np.abs(tm[f]-((mod[b][f]-mod[a][f])%1440))
    # раздели: дупки ИЗЦЯЛО в отворен пазар (делнични) срещу пипнали уикенда
    цял=(tm[f]==h*60)
    print(f"{h:>5}ч {f.sum():>8,} {(d==0).sum():>8,} {(d>0).sum():>8,}  "
          f"изцяло-в-отворен-пазар: {цял.sum():,} от тях лъжещи: {(d[цял]>0).sum():,}")
