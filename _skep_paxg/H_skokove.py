# -*- coding: utf-8 -*-
"""H · Истински ли са 30$-те за 70 мин, или са роловър/презакотвяне?"""
import json, io, sys
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
rows = []
for ln in open("live/live_journal.jsonl", encoding="utf-8"):
    try: d = json.loads(ln)
    except: continue
    if d.get("basis") is None: continue
    rows.append((str(d["run_utc"]), float(d["basis"]), d.get("spot_src"),
                 json.dumps(d.get("notes") or [], ensure_ascii=False)))
rows.sort()
скокове = []
for i in range(1, len(rows)):
    Δ = abs(rows[i][1] - rows[i-1][1])
    if Δ > 5: скокове.append((Δ, rows[i-1], rows[i]))
скокове.sort(reverse=True, key=lambda x: x[0])
print("руна с местене на базиса >5$ ЗА ЕДИН РУН:", len(скокове), "от", len(rows))
for Δ, a, b in скокове[:8]:
    print("  %.2f$  %s (%.2f) → %s (%.2f)  бележки: %s" % (Δ, a[0], a[1], b[0], b[1], b[3][:150]))
