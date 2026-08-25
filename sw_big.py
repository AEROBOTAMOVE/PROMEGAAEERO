# -*- coding: utf-8 -*-
import sys, json, re; sys.argv=["x"]
import live_bot as lb, pandas as pd
ts=[]
for p in ["live/archive/live_journal-2026-07.jsonl","live/live_journal.jsonl"]:
    for ln in open(p, encoding="utf-8"):
        ln=ln.strip()
        if ln:
            try: ts.append(str(json.loads(ln)["run_utc"]))
            except: pass
ts=sorted(set(ts))
for a,b in zip(ts,ts[1:]):
    wall=(pd.Timestamp(b)-pd.Timestamp(a)).total_seconds()/60
    if wall<=480: continue
    tm=lb._търговски_минути(a,b)
    wk=lb._market_closed(b)
    пали = tm>=lb.СПАЛ_МИН and not wk
    print("="*70)
    print(f"РЕАЛНА дупка {a} -> {b}")
    print(f"  стенно {wall:.0f} мин ({wall/60:.1f}ч) | ТЪРГОВСКИ {tm:.0f} мин ({tm/60:.1f}ч)")
    print(f"  _market_closed(край)={wk} -> картата пали ли се: {пали}")
    if пали:
        print(re.sub(r"<[^>]+>","",lb._спал_msg(tm,a,b)))
    else:
        print("  (картата НЕ се показва)")
