# -*- coding: utf-8 -*-
import sys, json, io
sys.argv=["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import numpy as np, pandas as pd
import live_bot as lb

entry=4400.10
lv = lb._levels(entry,"long")
trade = {"direction":"long","entry":entry,"levels":dict(lv),"hit":{},"opened":"2026-08-18T10:00:00",
         "checked":"2026-08-18T10:00:00","status":"open","sym":"XAUUSD","ledger":"spot"}
print("сделка:", json.dumps(trade,ensure_ascii=False))
BASIS = 9.0   # фючърс − спот
# барове = ФЮЧЪРС (спот + базис). Правим път: минава ТП1, после ТП2, после се връща на входа
ts = pd.date_range("2026-08-18 10:05", periods=8, freq="5min")
spot_path = [
 (4400,4402,4399,4401),
 (4401,4408.5,4400,4408),   # ТП1 4407.60
 (4408,4409,4405,4406),
 (4406,4413.0,4405,4412.5), # ТП2 4412.10
 (4412,4413,4405,4406),
 (4406,4407,4399,4400.5),
 (4400.5,4401,4399.0,4400.2), # докосва входа 4400.10? low 4399.0 <= 4400.10 → BE стоп
 (4400,4401,4400,4400.5),
]
rows=[]
for o,h,l,c in spot_path:
    rows.append({"Open":o+BASIS,"High":h+BASIS,"Low":l+BASIS,"Close":c+BASIS})
bars = pd.DataFrame(rows, index=ts)
print("\n=== track_trade (само барове, без спот) ===")
tr, ev = lb.track_trade(trade, bars, BASIS, 4400.5, "2026-08-18T10:45:00", spot=None)
for e in ev: print("  СЪБИТИЕ:", e)
print("  trade след:", None if tr is None else {k:tr[k] for k in ("levels","hit","checked","status")})
print("  hit_px:", (tr or trade).get("hit_px"))

print("\n=== _exit_msg за всяко събитие ===")
tr2 = trade
for kind,px,when,via,gap in ev:
    print(lb._exit_msg(kind, tr2, px, when, via, gap, spot=None, next_line="", dec=2))
    print("---")
