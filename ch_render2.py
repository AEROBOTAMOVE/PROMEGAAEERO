# -*- coding: utf-8 -*-
import sys, json, io, re, html
sys.argv = ["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import live_bot as lb
import стил as st

stats = json.load(open("backtest_stats.json", encoding="utf-8"))
lv = lb._levels(4365.20, "long")
mac = {"долар": True, "лихви": True, "миньори": True}
brd = [("1час","long",6,"strong","СИЛЕН")]*7
best = ("1час","long",6,"strong","СИЛЕН")
zoneB = ("B", "🟨 зона отдолу (4,352.10), но има насрещна отгоре")

K = {}
K["1 сигнал ДА"] = lb._sig_msg("long",6,7,"СИЛЕН",{"mid":4365.2},4365.0,"2026-08-21T06:39",
        lv,4365.20,"ДА — доларът и лихвите падат от днес, това вдига златото",
        mac,1,{"vol_rank":0.5},stats,5000,2.0,adv_ok=True, zone=zoneB)
K["2 без вход"] = lb._sig_msg("short",5,4,"ГОТОВ",{"mid":4365.2},4365.0,"2026-08-21T06:39",
        lb._levels(4365.20,"short"),4365.20,"НЕ — доларът и лихвите се карат днес",
        mac,0,{"vol_rank":0.5},stats,5000,2.0,adv_ok=False,
        shadow_on={"direction":"short","entry":4111.0})
ot = {"direction":"long","entry":4358.0,"opened":"2026-08-18T09:00","sym":"XAUUSD",
      "levels":{"tp1":4365.5,"tp2":4370.0,"tp3":4378.0,"sl":4358.0},
      "hit":{"tp1":True,"tp2":True}}
K["3 сделката тече"] = lb._sig_msg("long",6,7,"СИЛЕН",{"mid":4365.2},4365.0,"2026-08-21T06:39",
        lv,4365.20,"ДА — пресен клас",mac,1,{"vol_rank":0.5},stats,5000,2.0,
        adv_ok=True, open_trade=ot)
K["4 цел 1"] = lb._exit_msg("tp1", {"direction":"long","entry":4358.0,"sym":"XAUUSD",
        "levels":{"tp1":4365.5,"tp2":4370.0,"tp3":4378.0,"sl":4338.0},"hit":{}},
        4365.5,"2026-08-21T10:00","бар",False)
K["5 стоп"] = lb._exit_msg("sl", {"direction":"long","entry":4358.0,"sym":"XAUUSD",
        "levels":{"tp1":4365.5,"tp2":4370.0,"tp3":4378.0,"sl":4338.0},"hit":{}},
        4335.62,"2026-08-21T10:00","бар",True)
K["6 стои"] = lb._standing_msg("long",best,14.0,{"mid":4365.2},4365.0,4365.20,brd,mac,
        {"мъртви":["лихви"]},"2026-08-21T11:20")
K["7 къде сме"] = lb._status_msg(brd,"long",ot,None,{"mid":4365.2},{"mid":65.150},
        None,None,{"long":2,"short":0},False,"2026-08-21",mac)

for име in sorted(K):
    т = K[име]
    ч = st.чист(т)
    print("="*70); print(име)
    print(ч)
    print(f"--- редове={len(ч.split(chr(10)))} знаци={len(ч)}")
    f = st.провери(име, т)
    for v,x in f: print("   [",v,"]",x)
