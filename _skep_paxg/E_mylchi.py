# -*- coding: utf-8 -*-
"""E · «БЕЗ нито една бележка» — вярно ли е? Какво е казал ботът в 66-те
реални руна на резерва? И къде е скокът от 35$ за 14 руна?"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
rows = []
for ln in open("live/live_journal.jsonl", encoding="utf-8"):
    try: rows.append(json.loads(ln))
    except: pass
rows.sort(key=lambda d: str(d.get("run_utc")))
рез = [d for d in rows if str(d.get("spot_src") or "").startswith("paxg")]
print("руна на резерва:", len(рез))
с_дума = 0
for d in рез:
    т = json.dumps(d.get("notes") or [], ensure_ascii=False) + json.dumps(d.get("status") or [], ensure_ascii=False)
    if "резерв" in т: с_дума += 1
print("от тях с думата «резерв» в notes/status:", с_дума)
print("примерни бележки от първия:", (рез[0].get("notes") or [])[:4])
print("статус на първия:", рез[0].get("status"))
print("отрязан спот в руна на резерва:", sum(1 for d in рез if d.get("spot_rejected")))
print()
b = [(str(d.get("run_utc")), d.get("basis"), d.get("spot_src"), d.get("v")) for d in rows if d.get("basis") is not None]
най = max(range(len(b)-14), key=lambda i: abs(b[i+14][1]-b[i][1]))
print("НАЙ-ГОЛЯМОТО местене за 14 руна:")
for r in b[най:най+15]:
    print("   ", r[0], "базис %.2f" % r[1], r[2], r[3])
