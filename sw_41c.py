# -*- coding: utf-8 -*-
import sys, shutil
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8'); sys.argv=["x"]
import live_bot as lb, pandas as pd
def bars(rows, start):
    return pd.DataFrame(rows, columns=["Open","High","Low","Close"],
                        index=pd.date_range(start, periods=len(rows), freq="5min"))
tr={"direction":"long","entry":4000.0,"opened":"2026-08-19T09:55","checked":"2026-08-19T09:55",
    "levels":{"tp1":4010.0,"tp2":4015.0,"tp3":4020.0,"sl":3990.0},"hit":{},"status":"open",
    "v2":True,"ledger":"spot","sym":"XAUUSD"}
b=bars([(4000,4002,3985,4001),(4001,4003,4000,4002)],"2026-08-19 10:00:00")  # Low 3985 в първия бар
tr2,ex=lb.track_trade(tr, b, 0.0, 4002.0, "2026-08-19T10:10")
print("РЕАЛНИЯТ тракер (бар High/Low, Low=3985 < стоп 3990):",
      [(e[0], e[1], e[3]) for e in ex] or "нищо")
print("  сделката затворена ли е:", tr2 is None)

БАЗА=Path("C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/sw41c")
if БАЗА.exists(): shutil.rmtree(БАЗА)
БАЗА.mkdir(parents=True)
Ф=БАЗА/"brain_track.json"; Д=БАЗА/"brain_result.jsonl"
нов={"лонг":True,"рамка":"15м","степен":"✅ ГОТОВ","точки":11,
     "залог":{"вход":4000.0,"стоп":3990.0,"цел":4010.0,"цел2":4020.0}}
lb._мозък_следене(Ф,Д,4000.0,"2026-08-19T09:55:00",нов=нов)
m1=lb._мозък_следене(Ф,Д,4001.0,"2026-08-19T10:05:00")   # СЪЩИЯТ период, само крайната цена
m2=lb._мозък_следене(Ф,Д,4002.0,"2026-08-19T10:10:00")
print("МОЗЪЧНОТО следене (само точката 4001/4002):", [t for t,_ in m1+m2] or "нищо")
print("  наблюдението още отворено:", Ф.exists(), "· дневникът празен:", not Д.exists() or Д.stat().st_size==0)
