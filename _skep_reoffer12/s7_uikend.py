# -*- coding: utf-8 -*-
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0,".")
import pandas as pd, live_bot as LB
recs=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
пер=[r for r in recs if "2026-08-06T23:03"<=r["run_utc"]<="2026-08-18T15:26"]
uk=[r for r in пер if LB._market_closed(r["run_utc"])]
print("прозорецът 06.08T23:03 → 18.08T15:26:")
print("  ръна:",len(пер),"· от тях борсата ЗАТВОРЕНА (уикенд):",len(uk),f"({100*len(uk)/len(пер):.1f}%)")
print("  gate.ok=True в целия прозорец:",sum(1 for r in пер if (r.get('gate') or {}).get('ok')))
# груба сметка в часове: ръновете са ~на 5 мин
print(f"  ≈ уикенд часове: {len(uk)*280.4/len(пер):.0f}ч от 280.4ч")
# ръна, в които спотът е бил жив (не сляпо)
жив=[r for r in пер if r.get("spot") is not None]
print("  ръна с ЖИВ спот:",len(жив))
# и в целия дневник: колко пъти вратата е била затворена ПРИ отворена борса И жив спот
всички=[r for r in recs]
import collections
c=collections.Counter()
for r in recs:
    g=r.get("gate") or {}
    c[(bool(g.get("ok")), LB._market_closed(r["run_utc"]))]+=1
print("\nцял дневник (gate.ok, уикенд) →",dict(c))
