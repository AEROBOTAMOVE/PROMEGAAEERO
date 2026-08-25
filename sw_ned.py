# -*- coding: utf-8 -*-
import sys,json; sys.argv=["x"]
import live_bot as lb, pandas as pd
ts=[]
for p in ["live/archive/live_journal-2026-07.jsonl","live/live_journal.jsonl"]:
    for ln in open(p,encoding="utf-8"):
        ln=ln.strip()
        if ln:
            try: ts.append(str(json.loads(ln)["run_utc"]))
            except: pass
ts=sorted(set(ts))
for d in ["2026-08-09","2026-08-16","2026-08-07","2026-08-14"]:
    дн=[t for t in ts if t.startswith(d)]
    print(f"{d} ({pd.Timestamp(d).day_name()}): {len(дн)} ръна, от {дн[0][-5:]} до {дн[-1][-5:]} UTC" if дн else f"{d}: 0 ръна")
