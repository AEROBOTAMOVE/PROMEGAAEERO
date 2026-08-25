# -*- coding: utf-8 -*-
"""Пълна таблица на ДОСТИЖИМИТЕ макро-състояния × отворена сделка."""
import sys, json
sys.argv=["x"]; sys.stdout.reconfigure(encoding="utf-8")
import live_bot as lb, стил
stats=json.load(open("backtest_stats.json",encoding="utf-8"))
tr=lb._migrate_trade(json.load(open("_o37_18392/trade.json",encoding="utf-8")),0.0,notes=[])
бд=[(l,"long",5,"medium","СРЕДЕН") for l in ("1мин","5м","15м","30м","1час","4час","1ден")]
СЪСТ=[("подредено НАГОРЕ",{"миньори":0.01,"долар":0.0145,"лихви":0.07,"мъртви":[]},{"long":6}),
      ("подредено НАДОЛУ",{"миньори":-0.01,"долар":-0.0145,"лихви":-0.07,"мъртви":[]},{"short":3}),
      ("разбъркано     ",{"миньори":0.01,"долар":0.0145,"лихви":-0.07,"мъртви":[]},{"long":0}),
      ("мъртво макро   ",{"долар":None,"лихви":None,"мъртви":["долар","лихви"]},{})]
print(f"{'макро':<17}{'без сделка':>12}{'+злато':>9}{'+злато&сребро':>15}   (таван {стил.МАКС_РЕДОВЕ})")
for име,мр,ст in СЪСТ:
    ред=[]
    for trade,s in ((None,None),(tr,None),(tr,tr)):
        t=стил.чист(lb._pulse_msg("09",бд,бд[-1],"long","x",False,trade,s,
            {"mid":4370.12},{"mid":64.821},{"миньори":True,"долар":True,"лихви":False},
            False,False,macro_raw=мр,streaks=ст,stats=stats))
        n=len([r for r in t.split("\n") if r.strip()])
        ред.append(f"{n}{'🔴' if n>стил.МАКС_РЕДОВЕ else '✅'}")
    print(f"{име:<17}{ред[0]:>12}{ред[1]:>10}{ред[2]:>16}")
