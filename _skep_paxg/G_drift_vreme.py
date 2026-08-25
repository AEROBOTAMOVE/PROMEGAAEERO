# -*- coding: utf-8 -*-
"""G · Поправка на СОБСТВЕНАТА ми мярка: F сравняваше редове ПРЕЗ дупката,
която сам изрязах. Тук прозорците са по ВРЕМЕ и вътре не се допуска
прекъсване >20 мин, нито замразената епоха."""
import json, io, sys
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
rows = []
for ln in open("live/live_journal.jsonl", encoding="utf-8"):
    try: d = json.loads(ln)
    except: continue
    if d.get("basis") is None: continue
    t = datetime.fromisoformat(str(d["run_utc"]))
    rows.append((t, float(d["basis"]), abs(float(d["basis"]) - 25.515) < 0.01))
rows.sort()
# непрекъснати ивици: пауза ≤20 мин и без замразени редове
ивици = []; тек = []
for t, v, замразен in rows:
    if замразен or (тек and (t - тек[-1][0]).total_seconds() > 1200):
        if len(тек) > 3: ивици.append(тек)
        тек = []
    if not замразен: тек.append((t, v))
if len(тек) > 3: ивици.append(тек)
print("непрекъснати ивици:", len(ивици), " най-дълга:", max(len(i) for i in ивици), "руна")
for МИН in (70, 150, 1000):
    d = []
    for ив in ивици:
        j = 0
        for i in range(len(ив)):
            while j < len(ив) and (ив[j][0]-ив[i][0]).total_seconds() < МИН*60: j += 1
            if j >= len(ив): break
            d.append(abs(ив[j][1]-ив[i][1]))
    if not d: print("%d мин: няма достатъчно дълга ивица" % МИН); continue
    d.sort()
    print("%4d мин тишина: медиана %.2f  p90 %.2f  p99 %.2f  МАКС %.2f$  · над 8$: %.2f%% (n=%d)"
          % (МИН, d[len(d)//2], d[int(len(d)*.9)], d[int(len(d)*.99)], d[-1],
             100*sum(1 for x in d if x > 8)/len(d), len(d)))
