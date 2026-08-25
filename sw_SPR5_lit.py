# -*- coding: utf-8 -*-
import sys; sys.argv=["x"]; import live_bot as lb
def проба(bid, ask, посока, tp1_на_нивото):
    mid=round((bid+ask)/2,3)
    lv=lb._levels(4400.0 if посока=="long" else 4400.0, посока)
    lv=dict(lv); lv["tp1"]=tp1_на_нивото
    tr={"direction":посока,"entry":(ask if посока=="long" else bid),"levels":lv,
        "hit":{},"status":"open","opened":"2026-08-19T05:00","checked":"2026-08-19T05:00","sym":"XAUUSD"}
    sp={"bid":bid,"ask":ask,"mid":mid}
    _,ev=lb.track_trade(tr,None,0.0,mid,"2026-08-19T05:30",spot=sp)
    return [e for e in ev if e[0]=="tp1"]
print("ЛОНГ  bid=3299.90 ask=3300.10 mid=3300.00, цел 3300.00 ->", проба(3299.90,3300.10,"long",3300.00))
print("ШОРТ  bid=3299.90 ask=3300.10 mid=3300.00, цел 3300.00 ->", проба(3299.90,3300.10,"short",3300.00))
print("ЛОНГ  цел 3299.80 (под BID)                        ->", проба(3299.90,3300.10,"long",3299.80))
print("_entry_side long/short:", lb._entry_side({"bid":3299.90,"ask":3300.10,"mid":3300.0},"long"),
      lb._entry_side({"bid":3299.90,"ask":3300.10,"mid":3300.0},"short"))
