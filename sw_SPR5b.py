# -*- coding: utf-8 -*-
import sys; sys.argv=["x"]; import live_bot as lb
def проба(bid, ask, посока, цел):
    mid=round((bid+ask)/2,3)
    вх = ask if посока=="long" else bid
    lv=dict(lb._levels(вх,посока)); lv["tp1"]=цел
    tr={"direction":посока,"entry":вх,"levels":lv,"hit":{},"status":"open",
        "opened":"2026-08-19T05:00","checked":"2026-08-19T05:00","sym":"XAUUSD"}
    _,ev=lb.track_trade(tr,None,0.0,mid,"2026-08-19T05:30",spot={"bid":bid,"ask":ask,"mid":mid})
    return [e for e in ev if e[0].startswith("tp")]
print("ЛОНГ  bid=3299.90 ask=3300.10 mid=3300.00 · цел 3300.00 (продажба, а BID е 3299.90):")
print("   ", проба(3299.90,3300.10,"long",3300.00))
print("ШОРТ  цел 3300.00 (обратна покупка, а ASK е 3300.10):")
print("   ", проба(3299.90,3300.10,"short",3300.00))
print("ЛОНГ  цел 3299.85 (под BID -> честно ударена):")
print("   ", проба(3299.90,3300.10,"long",3299.85))
