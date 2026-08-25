# -*- coding: utf-8 -*-
import json, collections, statistics as st
rows=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
print("ключове в последния запис:", sorted(rows[-1].keys()))
rej=[r for r in rows if r.get("spot_rejected")]
print("отрязани общо:", len(rej), f"({100*len(rej)/len(rows):.1f}%)")
# има ли gate/ok поле
g=[r for r in rows if "gate" in r]
print("записи с 'gate':", len(g), "| пример:", g[-1]["gate"] if g else None)
print()
print("== ОТКРИ ЛИ СЕ СДЕЛКА В РЪН С ОТРЯЗАН СПОТ? ==")
c=collections.Counter()
for r in rej:
    t=r.get("trade")
    c[("trade" if t else "без сделка")]+=1
print(" ", dict(c))
# ok поле в gate за отрязани
ok=collections.Counter()
for r in rej:
    gg=r.get("gate")
    if isinstance(gg,dict): ok[gg.get("ok")]+=1
print("  gate.ok при отрязан спот:", dict(ok))
# кои gate.by
by=collections.Counter()
for r in rej:
    gg=r.get("gate")
    if isinstance(gg,dict): by[gg.get("by") or gg.get("причина")]+=1
print("  gate.by:", by.most_common(6))
print()
print("== ИЗПРАТЕНИ КАРТИ В ОТРЯЗАНИ РЪНА (по status/kinds) ==")
k=collections.Counter()
for r in rej:
    for s in (r.get("status") or []):
        k[str(s)[:60]]+=1
print("  ", k.most_common(12))
