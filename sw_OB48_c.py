# -*- coding: utf-8 -*-
import sys, json, collections
from datetime import datetime
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8'); sys.argv=["x"]
import live_bot as lb
rows=[]
for f in ["live/archive/live_journal-2026-07.jsonl","live/live_journal.jsonl"]:
    for ln in Path(f).read_text(encoding="utf-8", errors="replace").splitlines():
        ln=ln.strip()
        if not ln: continue
        try: rows.append(json.loads(ln))
        except Exception: pass
sob=[r for r in rows if r.get("run_utc") and datetime.fromisoformat(r["run_utc"]).weekday()==5]
print("съботни записи:", len(sob))
if sob:
    ex=sob[len(sob)//2]
    print("ПРИМЕР съботен запис (ключове):", sorted(ex.keys()))
    print(json.dumps({k:ex[k] for k in list(ex)[:20]}, ensure_ascii=False)[:1500])
    print("версии в съботните:", collections.Counter(r.get("v") for r in sob))
# версии по дата
byday=collections.defaultdict(set)
for r in rows:
    t=r.get("run_utc")
    if t: byday[t[:10]].add(r.get("v"))
for d in sorted(byday): print(d, sorted(x for x in byday[d] if x))
