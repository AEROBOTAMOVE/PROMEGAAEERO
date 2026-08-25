# -*- coding: utf-8 -*-
"""F · ЧЕСТНОТО число: колко се мести ИСТИНСКИЯТ базис за N руна, БЕЗ
замразената епоха 19-21.08 (там 25.52 е самата повреда, не пазарът)."""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
rows = []
for ln in open("live/live_journal.jsonl", encoding="utf-8"):
    try: rows.append(json.loads(ln))
    except: pass
rows.sort(key=lambda d: str(d.get("run_utc")))
b = [(str(d["run_utc"]), float(d["basis"])) for d in rows
     if d.get("basis") is not None and abs(float(d["basis"]) - 25.515) > 0.01]
изх = [(t, v) for t, v in b]
print("използвани руна (без замразената епоха):", len(изх), изх[0][0], "→", изх[-1][0])
v = [x[1] for x in изх]
for W in (12, 14, 30, 200):
    d = sorted(abs(v[i+W] - v[i]) for i in range(len(v)-W))
    if not d: continue
    print("прозорец %3d руна: медиана %.2f  p90 %.2f  p99 %.2f  МАКС %.2f$  (n=%d)"
          % (W, d[len(d)//2], d[int(len(d)*.9)], d[int(len(d)*.99)], d[-1], len(d)))
# колко често изобщо разминаването би надхвърлило 8$ (допускът)
for W in (14, 200):
    d = [abs(v[i+W]-v[i]) for i in range(len(v)-W)]
    print("W=%3d: над 8$ в %d от %d прозореца (%.2f%%)" % (W, sum(1 for x in d if x > 8), len(d), 100*sum(1 for x in d if x > 8)/len(d)))
