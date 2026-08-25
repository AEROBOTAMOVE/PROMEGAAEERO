# -*- coding: utf-8 -*-
"""I · Константата PAXG_ПРЕМИЯ=2.0$ в ПРИЛОЖЕНАТА поправка — измерена ли е?
премия = (базис от swq точно преди) − (бар − paxg цена) за същия рун."""
import json, io, sys, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
rows = []
for ln in open("live/live_journal.jsonl", encoding="utf-8"):
    try: rows.append(json.loads(ln))
    except: pass
rows.sort(key=lambda d: str(d.get("run_utc")))
прем = []
for i, d in enumerate(rows):
    if not str(d.get("spot_src") or "").startswith("paxg"): continue
    if d.get("bar") is None or d.get("spot") is None: continue
    преди = None
    for k in range(i-1, -1, -1):
        if rows[k].get("spot_src") == "swq" and rows[k].get("basis") is not None:
            преди = rows[k]; break
    if not преди: continue
    now_b = float(d["bar"]) - float(d["spot"])
    прем.append((str(d["run_utc"]), float(преди["basis"]) - now_b))
v = [p for _, p in прем]
print("измерени премии:", len(v))
print("мин %.2f$  медиана %.2f$  средно %.2f$  макс %.2f$" % (min(v), statistics.median(v), sum(v)/len(v), max(v)))
v.sort()
print("p10 %.2f  p90 %.2f" % (v[int(len(v)*.1)], v[int(len(v)*.9)]))
print("константата в кода: PAXG_ПРЕМИЯ = 2.0$")
print("отрицателни (PAXG под спота):", sum(1 for x in v if x < 0), "от", len(v))
