# -*- coding: utf-8 -*-
import sys, io, json
sys.argv=["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import live_bot as lb

print("=== СТРАНАТА НА СПРЕДА: вход срещу изход ===")
spot_in={"bid":4399.50,"ask":4400.10,"mid":4399.80,"src":"swq"}
e = lb._entry_side(spot_in,"long")
print("  ВХОД long: _entry_side -> ASK %.2f  (вярната страна ✓)"%e)
lv = lb._levels(round(e,2),"long")
print("  нива:", lv)

tr={"direction":"long","entry":round(e,2),"levels":dict(lv),"hit":{},
    "opened":"2026-08-18T10:00:00","checked":"2026-08-18T10:00:00","status":"open","sym":"XAUUSD"}
# цената стига ТП1 по MID; bid е 0.60 по-ниско
spot_out={"bid":4407.30,"ask":4407.90,"mid":4407.60,"src":"swq"}
tr2, ev = lb.track_trade(tr, None, 0.0, spot_out["mid"], "2026-08-18T11:00:00", spot=spot_out)
print("\n  ИЗХОД: spot bid=%.2f mid=%.2f ask=%.2f"%(spot_out["bid"],spot_out["mid"],spot_out["ask"]))
print("  събитие от track_trade:", ev)
print("  → засича се по MID и се ОТЧИТА нивото %.2f"%ev[0][1])
print("  → но long се ЗАТВАРЯ на BID = %.2f"%spot_out["bid"])
print(lb._exit_msg(ev[0][0], tr, ev[0][1], ev[0][2], ev[0][3], ev[0][4]))
реално = (spot_out["bid"] - round(e,2))
print("\n  картата казва : %s"%lb._пари(ev[0][1]-round(e,2)))
print("  на bid реално : %s"%lb._пари(реално))
print("  разлика       : %.2f$ = %.0f пипса (половин спред на всеки край)"
      %(ev[0][1]-spot_out["bid"], (ev[0][1]-spot_out["bid"])/lb.PIP))

print("\n=== същото за СРЕБРО (dec=3) ===")
si={"bid":64.100,"ask":64.140,"mid":64.120}
es=lb._entry_side(si,"long"); lvs=lb._levels_silver(round(es,3),"long")
so={"bid":64.320,"ask":64.360,"mid":64.340}
trs={"direction":"long","entry":round(es,3),"levels":dict(lvs),"hit":{},
     "opened":"2026-08-18T10:00:00","checked":"2026-08-18T10:00:00","status":"open","sym":"XAGUSD"}
_,evs=lb.track_trade(trs,None,0.0,so["mid"],"2026-08-18T11:00:00",spot=so)
print("  събитие:",evs)
if evs:
    print("  картата казва: %s"%lb._пари(evs[0][1]-round(es,3),"XAGUSD"))
    print("  на bid реално: %s"%lb._пари(so["bid"]-round(es,3),"XAGUSD"))
