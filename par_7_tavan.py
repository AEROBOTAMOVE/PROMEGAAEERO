# -*- coding: utf-8 -*-
import sys, io, json
sys.argv=["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import live_bot as lb
stats=json.load(open("backtest_stats.json",encoding="utf-8"))
spot={"bid":4399.5,"ask":4400.1,"mid":4399.8,"src":"swq"}
entry=4400.10; lv=lb._levels(entry,"long")
macro={'миньори':True,'долар':True,'лихви':True}
regime={"ma":{},"streaks":{"long":1}}
other={"direction":"long","entry":64.10,"sym":"XAGUSD"}
open_tr={"direction":"long","entry":4390.0,"levels":lb._levels(4390.0,"long"),"hit":{"tp1":True}}
sh={"entry":4395.0,"direction":"long"}

def R(**kw):
    d=dict(direction="long",score=7,agree_n=3,tier_name="ПРЕМИУМ",spot=spot,bar_price=4409.0,
           bar_ts="x",lv=lv,entry=entry,advice_txt="ДА (малък размер) — подреждането е отпреди 5 дни",
           macro=macro,streak_n=5,regime=regime,stats=stats,balance=10000.0,risk_pct=1.0)
    d.update(kw)
    return lb._sig_msg(**d)

cases = {
 "ПЪЛНА (вход + друга сделка + ре-влизане + зона C)":
   R(reentry=True, other_trade=other, zone=("C","z"), adv_ok=True),
 "БЕЗ ВХОД (adv_ok=False) + друга сделка + ре-влизане":
   R(reentry=True, other_trade=other, zone=("C","z"), adv_ok=False,
     advice_txt="НЕ — доларът и лихвите се карат днес", shadow_on=sh),
 "СДЕЛКАТА ТЕЧЕ + друга сделка + ре-влизане":
   R(reentry=True, other_trade=other, zone=("C","z"), adv_ok=True, open_trade=open_tr),
 "СРЕБРО пълна":
   lb._sig_msg("long",7,1,"ПРЕМИУМ",{"bid":64.10,"ask":64.14,"mid":64.12,"src":"swq"},64.3,"x",
               lb._levels_silver(64.14,"long"),64.14,
               "ДА (малък размер) — подреждането е отдавна",macro,5,regime,stats,10000.0,1.0,
               sym="XAGUSD",dec=3,adv_ok=True,reentry=True,
               other_trade={"direction":"long","entry":4400.0}),
}
for k,v in cases.items():
    n=len(v.split("\n"))
    print("### %s  → %d реда %s"%(k,n,"🔴 НАД 7" if n>7 else ""))
    print(v); print()
