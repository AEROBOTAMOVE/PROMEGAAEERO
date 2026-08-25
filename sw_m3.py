# -*- coding: utf-8 -*-
import json, glob
from collections import Counter
tot=0; c=Counter(); nonsent=[]
for f in ["live/archive/live_journal-2026-07.jsonl","live/live_journal.jsonl"]:
    for l in open(f,encoding="utf-8"):
        l=l.strip()
        if not l: continue
        try: r=json.loads(l)
        except: continue
        tot+=1
        for s in (r.get("status") or []):
            s=str(s)
            if s.startswith(("signal=","s-signal=")):
                res=s.split("=",1)[1]; c[res[:14]]+=1
                if not res.startswith("SENT"): nonsent.append((r.get("run_utc"),s))
            if "дедуп" in s or "преля" in s or "ОТРОВНО" in s or "DRY (" in s or "повредени" in s:
                nonsent.append((r.get("run_utc"),"ДРУГ ОТРЕЗ: "+s))
print("ОБЩО ръна (юли+август):", tot)
print("signal/s-signal резултати:", dict(c))
print("НЕуспешни/отрязани:", nonsent if nonsent else "НУЛА")
