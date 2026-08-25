# -*- coding: utf-8 -*-
import json, io, os, collections
P=os.path.dirname(os.path.abspath(__file__))
rows=[json.loads(l) for l in io.open(os.path.join(P,"live","sent_log.jsonl"),encoding="utf-8") if l.strip()]
print("дневникът: от",rows[0]["utc"],"до",rows[-1]["utc"])
by=collections.defaultdict(collections.Counter)
for r in rows: by[r["utc"][:10]][r["tag"]]+=1
for d in sorted(by):
    print(d, dict(by[d]))
