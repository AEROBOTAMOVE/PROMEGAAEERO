# -*- coding: utf-8 -*-
import sys, json, glob, collections
from datetime import datetime
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8'); sys.argv=["x"]
import live_bot as lb
files = ["live/live_journal.jsonl"] + sorted(glob.glob("live/archive/*"))
print("файлове:", files)
rows=[]
for f in files:
    if not f.endswith(".jsonl"): continue
    for ln in Path(f).read_text(encoding="utf-8", errors="replace").splitlines():
        ln=ln.strip()
        if not ln: continue
        try:
            r=json.loads(ln); r["_f"]=f; rows.append(r)
        except Exception: pass
print("общо записи:", len(rows))
ts=sorted(set(r.get("run_utc") for r in rows if r.get("run_utc")))
print("уникални run_utc:", len(ts), ts[0], ts[-1])
zc=[t for t in ts if lb._market_closed(t)]
print("уникални моменти при ЗАТВОРЕН пазар:", len(zc), zc[:20])
print("weekend=True общо:", sum(1 for r in rows if r.get("weekend") is True))
# петък късно
пет=[t for t in ts if datetime.fromisoformat(t).weekday()==4 and datetime.fromisoformat(t).hour>=19]
print("ПЕТЪК >=19 UTC:", пет)
нед=[t for t in ts if datetime.fromisoformat(t).weekday()==6]
print("НЕДЕЛЯ моменти:", нед)
съб=[t for t in ts if datetime.fromisoformat(t).weekday()==5]
print("СЪБОТА моменти:", съб)
