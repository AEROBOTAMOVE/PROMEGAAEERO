# -*- coding: utf-8 -*-
import sys, json, io
sys.argv=["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import live_bot as lb
stats=json.load(open("backtest_stats.json",encoding="utf-8"))
spot = {"bid":4399.50,"ask":4400.10,"mid":4399.80,"src":"swq","age_sec":1.0}
entry = lb._entry_side(spot,"long"); entry=round(entry,2)
lv = lb._levels(entry,"long")
macro={'миньори':True,'долар':True,'лихви':True}
regime={"below_sma200":False,"low_vol":True,"ma":{},"vol_rank":0.4,"sma50":4375.5,"sma200":4300.0,
        "streaks":{"long":1,"short":0}}
advice="ДА — доларът и лихвите падат от днес, това вдига златото"

for zc in ("A","B","C"):
    for малък in (False,True):
        adv = advice if not малък else "ДА (малък размер) — подреждането е отпреди 5 дни"
        txt = lb._sig_msg("long", 7, 3, "ПРЕМИУМ", spot, 4409.0, "2026-08-18T12:00", lv, entry,
                          adv, macro, 1, regime, stats, 10000.0, 1.0,
                          sym="XAUUSD", dec=2, adv_ok=True, zone=(zc,"z"))
        print("### ЗОНА %s  малък=%s"%(zc,малък))
        print(txt)
        print("   редове:", len(txt.split("\n")))
        print()
