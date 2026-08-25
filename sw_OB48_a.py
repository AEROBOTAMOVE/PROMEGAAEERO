# -*- coding: utf-8 -*-
import sys, json, collections
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8'); sys.argv=["x"]
import live_bot as lb
from pathlib import Path

rows=[]
for ln in Path("live/live_journal.jsonl").read_text(encoding="utf-8").splitlines():
    ln=ln.strip()
    if not ln: continue
    try: rows.append(json.loads(ln))
    except Exception: pass
print("записи:", len(rows))
print("ключове с weekend:", sum(1 for r in rows if "weekend" in r))
print("weekend=True:", sum(1 for r in rows if r.get("weekend") is True))
print("slot ключ присъства:", sum(1 for r in rows if "slot" in r))
ts=[r.get("run_utc") for r in rows if r.get("run_utc")]
print("първи/последен:", min(ts), max(ts))
# сам смятам market_closed по run_utc
zc=0; ex=[]
for r in rows:
    t=r.get("run_utc")
    if not t: continue
    if lb._market_closed(t):
        zc+=1
        if len(ex)<10: ex.append((t, r.get("weekend"), r.get("slot"), lb._sofia_hour(t)))
print("ръна, при които _market_closed(run_utc)=True:", zc)
print("примери:", ex)
# разпределение по ден от седмицата и час UTC
c=collections.Counter()
for t in ts:
    d=datetime.fromisoformat(t)
    c[(d.weekday(), d.hour)]+=1
пет=sorted([(h,n) for (w,h),n in c.items() if w==4])
print("ПЕТЪК по UTC час:", пет)
съб=sorted([(h,n) for (w,h),n in c.items() if w==5])
нед=sorted([(h,n) for (w,h),n in c.items() if w==6])
print("СЪБОТА по UTC час:", съб)
print("НЕДЕЛЯ по UTC час:", нед)
