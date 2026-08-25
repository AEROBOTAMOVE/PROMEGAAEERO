# -*- coding: utf-8 -*-
import json,io,collections
J=[json.loads(l) for l in io.open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
print("рънове в живия дневник:",len(J), J[0]["run_utc"], J[-1]["run_utc"])
# рънове, в които статусите съдържат и signal=SENT и brain-exit
n=0; bad=0
for r in J:
    st=[str(s) for s in (r.get("status") or [])]
    has_sig=any(s.startswith("signal=SENT") for s in st)
    has_bx=any(s.startswith("brain-exit") and "SENT" in s for s in st)
    if has_sig and has_bx:
        n+=1
        i_s=min(i for i,s in enumerate(st) if s.startswith("signal=SENT"))
        i_x=max(i for i,s in enumerate(st) if s.startswith("brain-exit") and "SENT" in s)
        print("  ",r["run_utc"],st)
        if i_s<i_x: bad+=1
print("рънове signal+brain-exit (по statuses):",n,"нарушени:",bad)
