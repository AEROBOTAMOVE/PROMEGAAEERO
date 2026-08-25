# -*- coding: utf-8 -*-
import sys, io, json, os, statistics as st
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from collections import defaultdict
d=defaultdict(list); c=defaultdict(list); n=0
for ln in open("live/live_journal.jsonl", encoding="utf-8"):
    ln=ln.strip()
    if not ln: continue
    try: o=json.loads(ln)
    except Exception: continue
    n+=1
    tb=o.get("tf_basis"); ts=str(o.get("ts") or o.get("time") or o.get("utc") or "")[:10]
    pr=o.get("price") or o.get("bar") or o.get("bar_price")
    if tb is None or not ts: continue
    try: d[ts].append(float(tb))
    except Exception: continue
    if pr:
        try: c[ts].append(float(pr))
        except Exception: pass
print("записа общо:", n, "| дни с tf_basis:", len(d))
for k in sorted(d)[-14:]:
    ц = st.median(c[k]) if c[k] else float("nan")
    print("%s  n=%3d  tf_basis медиана %+8.2f  |min| %+8.2f  цена %8.1f  таван=max(120,3%%)=%7.2f"
          % (k, len(d[k]), st.median(d[k]), min(d[k]), ц, max(120.0,0.03*ц) if ц==ц else float('nan')))
