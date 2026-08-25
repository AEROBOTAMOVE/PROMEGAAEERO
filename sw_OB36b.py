# -*- coding: utf-8 -*-
"""Изолация: ТОЧНО входът на selftest П44, после ЕДНА промяна наведнъж."""
import sys, json
sys.argv=["x"]; sys.stdout.reconfigure(encoding="utf-8")
import live_bot as lb, стил
stats=json.load(open("backtest_stats.json",encoding="utf-8"))
_raw=json.load(open("_o37_18392/trade.json",encoding="utf-8"))
tr=lb._migrate_trade(json.loads(json.dumps(_raw)),0.0,notes=[])
бд=[(l,"long",5,"medium","СРЕДЕН") for l in ("1мин","5м","15м","30м","1час","4час","1ден")]
def n(trade=None,s_trade=None,st=None,adv=False,мр={"долар":0.0145,"лихви":-0.07},стр={"long":0}):
    t=стил.чист(lb._pulse_msg("09",бд,бд[-1],"long","x",adv,trade,s_trade,
        {"mid":4370.12},{"mid":64.821},{"миньори":True,"долар":True,"лихви":False},
        False,False,macro_raw=мр,streaks=стр,stats=st))
    return len([r for r in t.split("\n") if r.strip()])
print("A  точно selftest П44 (trade=None,stats=None,adv_ok=False) :",n(),"реда")
print("B  A + само истинската статистика (както живият път)       :",n(st=stats),"реда")
print("C  A + само отворена ЗЛАТНА сделка                          :",n(trade=tr),"реда")
print("D  A + сделка + статистика (живият път)                     :",n(trade=tr,st=stats),"реда")
print("E  D + сребърна сделка                                      :",n(trade=tr,s_trade=tr,st=stats),"реда")
print("F  ПОДРЕДЕНО макро + сделка + статистика                    :",
      n(trade=tr,st=stats,мр={"долар":0.0145,"лихви":0.07},стр={"long":6}),"реда")
print("G  ПОДРЕДЕНО макро, БЕЗ сделка (контрола)                   :",
      n(st=stats,мр={"долар":0.0145,"лихви":0.07},стр={"long":6}),"реда")
print("H  A + adv_ok=True, без сделка                              :",n(adv=True),"реда")
print("\nтаван стил.МАКС_РЕДОВЕ =",стил.МАКС_РЕДОВЕ)
