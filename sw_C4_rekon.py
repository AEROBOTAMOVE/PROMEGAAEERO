# -*- coding: utf-8 -*-
import json, pathlib, collections
p = pathlib.Path("live/live_journal.jsonl")
rows=[]
for ln in p.read_text(encoding="utf-8",errors="replace").splitlines():
    if not ln.strip(): continue
    try: r=json.loads(ln)
    except Exception: continue
    rows.append(r)
# всички редове, споменаващи sh-exit:tp1 / tp2 около 17.08
for r in rows:
    for s in r.get("status") or []:
        if str(s).startswith("sh-exit:tp"):
            print(r.get("run_utc"), "|", s[:100])
