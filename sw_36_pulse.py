# -*- coding: utf-8 -*-
import sys, json
sys.argv=["x"]; import live_bot as lb, стил
sys.stdout.reconfigure(encoding='utf-8')
stats=json.load(open("backtest_stats.json",encoding="utf-8"))
spot_g={"mid":3350.12,"src":"binance"}; spot_s={"mid":38.123,"src":"binance"}
trade={"entry":3300.0,"dir":"long","sl":3280.0,"tp1":3320.0,"tp2":3340.0,"tp3":3360.0,
       "hit":{"tp1":True},"lots":1.0,"lot":1.0,"opened":"2026-08-18T10:00"}
s_trade={"entry":37.5,"dir":"long","sl":37.0,"tp1":38.0,"tp2":38.5,"tp3":39.0,
         "hit":{},"lots":1.0,"lot":1.0,"opened":"2026-08-18T10:00"}
board={"15m":"long","1h":"long","4h":"long"}
for име,macro_raw in (("разбъркано макро",{"долар":0.004,"лихви":-0.03}),
                      ("съгласно макро",{"долар":0.004,"лихви":0.03})):
    txt=lb._pulse_msg("09",board,None,"long","",True,trade,s_trade,spot_g,spot_s,
                      {"долар":1,"лихви":1},False,False,macro_raw=macro_raw,
                      streaks={"long":3},stats=stats)
    n=len(txt.split("\n"))
    print(f"=== {име}: {n} реда (таван стил.МАКС_РЕДОВЕ={стил.МАКС_РЕДОВЕ}) ===")
    for i,l in enumerate(txt.split("\n"),1): print(f"  {i:2d} {l}")
    ok=стил.провери("пулс",txt)
    print("  стил.провери →",ok)
    print()
