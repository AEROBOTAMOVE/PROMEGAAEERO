# -*- coding: utf-8 -*-
import sys, json, collections
from datetime import datetime
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
rows=[]
for ln in Path("live/live_journal.jsonl").read_text(encoding="utf-8").splitlines():
    ln=ln.strip()
    if ln:
        try: rows.append(json.loads(ln))
        except Exception: pass
ts=sorted(set(r["run_utc"] for r in rows if r.get("run_utc")))
days=collections.defaultdict(set)
for t in ts: days[datetime.fromisoformat(t).weekday()].add(t[:10])
cnt=collections.Counter()
for t in ts:
    d=datetime.fromisoformat(t); cnt[(d.weekday(),d.hour)]+=1
имена="пон вто сря чет пет съб нед".split()
print("ръна на ЧАС (усреднено по броя такива дни) — реалният часовник")
print("час | " + " | ".join(f"{имена[w]}({len(days[w])}д)" for w in range(7)))
for h in range(24):
    ред=[]
    for w in range(7):
        n=cnt.get((w,h),0); d=len(days[w]) or 1
        ред.append(f"{n/d:5.1f}")
    print(f"{h:02d}  | " + " | ".join(ред))
print()
print("yml казва: 00-04 UTC → */15 = 4.0/час · 05-21 → */5 = 12.0/час · 22-23 → */10 = 6.0/час (пон-пет)")
