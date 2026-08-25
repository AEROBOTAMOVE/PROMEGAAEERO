import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.argv=["x"]
import live_bot as lb

spot = {"bid": 3299.90, "ask": 3300.10, "mid": 3300.00}
print("entry side LONG (плаща ASK):", lb._entry_side(spot, "long"))
print("entry side SHORT (взима BID):", lb._entry_side(spot, "short"))

# ЛОНГ с цел РОВНО на mid; BID-ът (реалната цена на продажба) е ПОД целта
tr = {"direction":"long","entry":3280.0,"opened":"2026-08-19T09:00","checked":"2026-08-19T09:00",
      "levels":{"sl":3270.0,"tp1":3300.0,"tp2":3310.0,"tp3":3320.0},"hit":{},"status":"open",
      "v2":True,"ledger":"spot","tier":"A","date":"2026-08-19"}
t2, ev = lb.track_trade(dict(tr, levels=dict(tr["levels"])), None, 0.0, spot["mid"], "2026-08-19T09:05", spot=spot)
print("ЦЕЛ · събития:", ev)
print("  → BID е", spot["bid"], "а целта е 3300.00 — продажбата НЕ може да стане на 3300.00")

# ШОРТ: цел под mid, ASK (реалната цена на изкупуване) е НАД целта
tr2 = {"direction":"short","entry":3320.0,"opened":"2026-08-19T09:00","checked":"2026-08-19T09:00",
      "levels":{"sl":3330.0,"tp1":3300.0,"tp2":3290.0,"tp3":3280.0},"hit":{},"status":"open",
      "v2":True,"ledger":"spot","tier":"A","date":"2026-08-19"}
t3, ev3 = lb.track_trade(dict(tr2, levels=dict(tr2["levels"])), None, 0.0, spot["mid"], "2026-08-19T09:05", spot=spot)
print("ЦЕЛ ШОРТ · събития:", ev3, " ASK е", spot["ask"])

# СТОП по спот — поправката от 19.08
tr3 = {"direction":"long","entry":3310.0,"opened":"2026-08-19T09:00","checked":"2026-08-19T09:00",
      "levels":{"sl":3300.0,"tp1":3320.0,"tp2":3330.0,"tp3":3340.0},"hit":{},"status":"open",
      "v2":True,"ledger":"spot","tier":"A","date":"2026-08-19"}
t4, ev4 = lb.track_trade(dict(tr3, levels=dict(tr3["levels"])), None, 0.0, spot["mid"], "2026-08-19T09:05", spot=spot)
print("СТОП · събития:", ev4)
