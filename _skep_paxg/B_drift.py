# -*- coding: utf-8 -*-
"""B · КОЛКО се мести ИСТИНСКИЯТ базис за 14 руна (най-дългата истинска
тишина на златния фийд) и за 200 руна (допускането на твърдението)?
Само swq редове — там базисът се обновява истински."""
import json, io, sys, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
rows = []
for ln in open("live/live_journal.jsonl", encoding="utf-8"):
    try: d = json.loads(ln)
    except: continue
    if d.get("basis") is None: continue
    rows.append((str(d.get("run_utc")), d.get("spot_src"), float(d["basis"]),
                 (d.get("saniti") or {}).get("база")))
rows.sort()
print("редове с базис:", len(rows), " от", rows[0][0], "до", rows[-1][0])
b = [r[2] for r in rows]
print("базис: мин %.2f макс %.2f медиана %.2f" % (min(b), max(b), statistics.median(b)))
бази = [r[3] for r in rows if r[3] is not None]
if бази:
    print("«база» (допускът) в живите руна: мин %.2f медиана %.2f макс %.2f  (твърдението ползва 8.0)"
          % (min(бази), statistics.median(бази), max(бази)))
for W in (14, 30, 200):
    d = [abs(b[i+W] - b[i]) for i in range(len(b)-W)]
    d.sort()
    print("прозорец %3d руна: медиана %.2f  p90 %.2f  p99 %.2f  МАКС %.2f$  (n=%d)"
          % (W, d[len(d)//2], d[int(len(d)*.9)], d[int(len(d)*.99)], d[-1], len(d)))
