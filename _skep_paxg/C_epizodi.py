# -*- coding: utf-8 -*-
"""C · 11-те ИСТИНСКИ епизода на резервата: колко се е разминал базисът
между последния swq ПРЕДИ и първия swq СЛЕД тишината."""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
rows = []
for ln in open("live/live_journal.jsonl", encoding="utf-8"):
    try: d = json.loads(ln)
    except: continue
    rows.append(d)
rows.sort(key=lambda d: str(d.get("run_utc")))
i = 0; ep = 0
while i < len(rows):
    s = rows[i].get("spot_src")
    if s and str(s).startswith("paxg"):
        j = i
        while j < len(rows) and str(rows[j].get("spot_src") or "").startswith("paxg"): j += 1
        преди = None
        for k in range(i-1, -1, -1):
            if rows[k].get("spot_src") == "swq": преди = rows[k]; break
        след = None
        for k in range(j, len(rows)):
            if rows[k].get("spot_src") == "swq": след = rows[k]; break
        ep += 1
        bp = преди and преди.get("basis"); bs = след and след.get("basis")
        отряз = sum(1 for r in rows[i:j] if r.get("spot_rejected"))
        print("епизод %2d · %s → %s · %2d руна · базис ПРЕДИ %s → СЛЕД %s · Δ=%s · отрязан спот в %d от %d"
              % (ep, rows[i]["run_utc"], rows[j-1]["run_utc"], j-i,
                 ("%.2f" % bp) if bp is not None else "—",
                 ("%.2f" % bs) if bs is not None else "—",
                 ("%.2f$" % abs(bs-bp)) if (bp is not None and bs is not None) else "—",
                 отряз, j-i))
        i = j
    else:
        i += 1
