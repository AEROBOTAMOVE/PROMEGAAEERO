# -*- coding: utf-8 -*-
import json
rows=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
sig=[]
for i,r in enumerate(rows):
    for s in (r.get("status") or []):
        if str(s).startswith(("signal=","s-signal=")): sig.append((i,r["run_utc"],s))
print("всички signal статуси в 3554 ръна:", len(sig))
from collections import Counter
print(Counter(s.split("=",1)[1][:12] for _,_,s in sig))
print("примери:", sig[:5])
# провери дали дневникът пише пълния statuses (има ли ръна с >3 статуса)
mx=max(rows,key=lambda r:len(r.get("status") or []))
print("най-дълъг statuses:", mx["run_utc"], mx["status"])
