# -*- coding: utf-8 -*-
import sys, json, glob; sys.argv=["x"]
import live_bot as lb
ts=[]
for p in ["live/archive/live_journal-2026-07.jsonl","live/live_journal.jsonl"]:
    for ln in open(p, encoding="utf-8"):
        ln=ln.strip()
        if not ln: continue
        try: r=json.loads(ln)
        except: continue
        for k in ("run_utc","ts","now_utc"):
            if k in r: ts.append(str(r[k])); break
ts=sorted(set(ts))
print("записи:", len(ts), "от", ts[0], "до", ts[-1])
import pandas as pd
res=[]
for a,b in zip(ts, ts[1:]):
    tm=lb._търговски_минути(a,b)
    wall=(pd.Timestamp(b)-pd.Timestamp(a)).total_seconds()/60
    res.append((tm,wall,a,b))
res.sort(reverse=True)
пали=[r for r in res if r[0]>=lb.СПАЛ_МИН and not lb._market_closed(r[3])]
print(f"дупки общо: {len(res)} · палещи картата 'СПАЛ': {len(пали)}")
print("\nНАЙ-ГОЛЕМИТЕ 12 палещи дупки (търг.мин | стенно мин | от -> до):")
for tm,wall,a,b in пали[:12]:
    ч,м=int(tm//60),int(tm%60)
    print(f"  {tm:7.0f} ({ч}ч{м:02d}) | стенно {wall:7.0f} ({wall/60:5.1f}ч) | {a} -> {b}   " 
          f"надпис: 'от {lb._sofia(a)} до {lb._sofia(b)}'")
над24=[r for r in пали if r[0]>=24*60]
преминава=[r for r in пали if lb._sofia(r[2])>lb._sofia(r[3])] 
print(f"\nпалещи с ТЪРГОВСКИ >= 24ч: {len(над24)}")
print(f"палещи, при които стенното време минава през полунощ (надписът лъже посоката): "
      f"{sum(1 for r in пали if pd.Timestamp(r[2]).date()!=pd.Timestamp(r[3]).date())}")
# колко от палещите имат разминаване >60 мин между заглавие и наивния прочит на 'от..до'
лоши=0
for tm,wall,a,b in пали:
    A=pd.Timestamp(a).tz_localize('UTC').tz_convert('Europe/Sofia')
    B=pd.Timestamp(b).tz_localize('UTC').tz_convert('Europe/Sofia')
    наивно=((B.hour*60+B.minute)-(A.hour*60+A.minute))%(24*60)
    if abs(наивно-tm)>60: лоши+=1
print(f"палещи, където наивният прочит на 'от..до' се разминава с заглавието >60 мин: {лоши} от {len(пали)}")
