# -*- coding: utf-8 -*-
import json, io, sys, os, re, collections
P = os.path.dirname(os.path.abspath(__file__))
rows=[]
for ln in io.open(os.path.join(P,"live","sent_log.jsonl"),encoding="utf-8"):
    ln=ln.strip()
    if not ln: continue
    try: rows.append(json.loads(ln))
    except Exception as e: pass
print("записи:",len(rows))
print("ключове:", sorted(rows[0].keys()))
# tag distribution
c=collections.Counter(str(r.get("tag") or r.get("kind") or "?") for r in rows)
print(c.most_common(20))
