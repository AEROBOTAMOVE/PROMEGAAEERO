# -*- coding: utf-8 -*-
import sys, re, html, datetime as dt
from pathlib import Path
Б = Path(__file__).resolve().parent
sys.path.insert(0, str(Б)); sys.argv=["x"]
import огледало as ог
lb, st = ог.lb, ог.st
def чист(t): return re.sub(r"<[^>]+>","",html.unescape(str(t)))
def показ(и,т):
    т=чист(т); print("="*68); print(f"### {и}  [{len(т.splitlines())} реда]"); print("="*68); print(т); print()

for дни in (1, 29):
    отв = dt.datetime(2026,8,11,9,12,tzinfo=dt.timezone.utc) - dt.timedelta(days=дни)
    tr = {"direction":"long","entry":4358.00,"opened":отв.isoformat(),
          "levels":{"tp1":4365.5,"tp2":4370.0,"tp3":4378.0,"sl":4338.0},
          "hit":{"tp1":True},"sym":"XAUUSD"}
    показ(f"СТАТУС · сделката е на {дни} дни (изход по време на 30)",
      lb._status_msg(ог.brd,"long",tr,None,{"mid":4365.2},{"mid":65.15},0.0,0.0,
                     {"long":1},False,"2026-08-11",ог.mac))
    показ(f"ПУЛС · сделката е на {дни} дни (изход по време на 30)",
      lb._pulse_msg("14",ог.brd,ог.best,"long","",True,tr,None,{"mid":4365.2},
                    {"mid":65.15},ог.mac,False,False,
                    macro_raw={"долар":0.0145,"лихви":0.07},streaks={"long":1},stats=st))

показ("ИЗХОД ПО ВРЕМЕ (kind='time') — как звучи, когато удари 30-ия ден",
  lb._exit_msg("time",{"direction":"long","entry":4358.00,"opened":"2026-07-12T09:12",
   "levels":{"tp1":4365.5,"tp2":4370.0,"tp3":4378.0,"sl":4358.0},
   "hit":{"tp1":True},"sym":"XAUUSD"},4361.0,"2026-08-11T11:15","бар",False))

# ПУЛС при разбъркано макро БЕЗ отворена — най-честото живо състояние, вечерен слот
показ("ПУЛС 22ч · разбъркано макро, нищо отворено",
  lb._pulse_msg("22",ог.brd,ог.best,"short","",False,None,None,{"mid":4365.2},
   {"mid":65.15},ог.macm,False,False,macro_raw={"долар":0.0145,"лихви":-0.07},
   streaks={"short":0},stats=st))
