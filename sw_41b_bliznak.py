# -*- coding: utf-8 -*-
"""№41 · БЛИЗНАКЪТ: реалният тракер гледа БАРА (High/Low), следенето — една точка."""
import sys, json, shutil
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8'); sys.argv=["x"]
import live_bot as lb, pandas as pd

def bars(rows, start):
    idx=pd.date_range(start, periods=len(rows), freq="5min")
    return pd.DataFrame(rows, columns=["Open","High","Low","Close"], index=idx)

# СЪЩАТА сделка: вход 4000, стоп 3990. Между два ръна цената е слязла до 3985 и се е върнала.
tr={"direction":"long","entry":4000.0,"opened":"2026-08-19T10:00","checked":"2026-08-19T10:00",
    "levels":{"tp1":4010.0,"tp2":4015.0,"tp3":4020.0,"sl":3990.0},"hit":{},"status":"open",
    "v2":True,"ledger":"bar","sym":"XAUUSD"}
b=bars([(4000,4002,3985,4001)],"2026-08-19 10:00:00")     # барът ГО Е ВИДЯЛ: Low 3985
tr2,ex=lb.track_trade(tr, b, 0.0, 4001.0, "2026-08-19T10:05")
print("РЕАЛНИЯТ тракер (по бар High/Low):", [(e[0], e[1]) for e in ex] or "нищо")

БАЗА=Path("C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/sw41")
if БАЗА.exists(): shutil.rmtree(БАЗА)
БАЗА.mkdir(parents=True)
Ф=БАЗА/"brain_track.json"; Д=БАЗА/"brain_result.jsonl"
нов={"лонг":True,"рамка":"15м","степен":"✅ ГОТОВ","точки":11,
     "залог":{"вход":4000.0,"стоп":3990.0,"цел":4010.0,"цел2":4020.0}}
lb._мозък_следене(Ф,Д,4000.0,"2026-08-19T10:00:00",нов=нов)
m=lb._мозък_следене(Ф,Д,4001.0,"2026-08-19T10:05:00")     # СЪЩИЯТ бар, само последната цена
print("МОЗЪЧНОТО следене (по една точка 4001):", [t for t,_ in m] or "нищо · сделката остава ОТВОРЕНА")
print("отвореният файл още съществува:", Ф.exists())
print()
print("подписът на двете функции:")
import inspect
print("  track_trade    :", str(inspect.signature(lb.track_trade))[:90])
print("  _мозък_следене :", str(inspect.signature(lb._мозък_следене)))
