# -*- coding: utf-8 -*-
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
recs=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
gok=[r for r in recs if (r.get("gate") or {}).get("ok")]
print("ВСИЧКИ ръна с gate.ok=True в целия дневник:",len(gok))
print("  първи:",gok[0]["run_utc"],"| последен:",gok[-1]["run_utc"])
from collections import Counter
print("  по дни:",Counter(r["date"] for r in gok))
print()
# кога streak стана >=1
пр=None
for r in recs:
    g=r.get("gate") or {}
    if g.get("streak",0)>=1 and g.get("dir"):
        пр=r; break
print("ПЪРВИ рън със streak>=1:",пр["run_utc"],"| streak",пр["gate"]["streak"],
      "| ok",пр["gate"]["ok"],"| by",пр["gate"].get("by"),"| spot",пр.get("spot"),"| basis",пр.get("basis"))
print()
print("=== 20.08 20:00 → 21.08 13:00, на всеки рън: gate.ok / by / spot / basis ===")
for r in recs:
    t=r["run_utc"]
    if "2026-08-20T19:5"<=t<="2026-08-21T12:10":
        g=r.get("gate") or {}
        print(f"  {t} ok={str(g.get('ok')):5} by={str(g.get('by'))[:22]:22} streak={g.get('streak')} spot={r.get('spot')} basis={r.get('basis')} rej={r.get('spot_rejected')}")
