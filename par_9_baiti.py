# -*- coding: utf-8 -*-
import sys, io, json, hashlib
sys.argv=["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import live_bot as lb
stats=json.load(open("backtest_stats.json",encoding="utf-8"))
spot={"bid":4399.5,"ask":4400.1,"mid":4399.8,"src":"swq"}
entry=4400.10; lv=lb._levels(entry,"long")
macro={'миньори':True,'долар':True,'лихви':True}
regime={"ma":{},"streaks":{"long":1}}
def h(s): return hashlib.md5(s.encode()).hexdigest()[:10]

def sig(**kw):
    d=dict(direction="long",score=7,agree_n=3,tier_name="ПРЕМИУМ",spot=spot,bar_price=4409.0,
           bar_ts="x",lv=lv,entry=entry,advice_txt="ДА — доларът и лихвите падат от днес, това вдига златото",
           macro=macro,streak_n=1,regime=regime,stats=stats,balance=10000.0,risk_pct=1.0,
           zone=("A","z"),adv_ok=True)
    d.update(kw); return lb._sig_msg(**d)

print("=== _sig_msg: extra_ctx (макро-щит / дневен контекст) ===")
a=sig(extra_ctx=None)
b=sig(extra_ctx="⚠ ЩИТ: NFP 15:30 · днес: златото под натиск")
print("  без extra_ctx :", h(a))
print("  с ЩИТ+контекст:", h(b))
print("  🔴 БАЙТ-ИДЕНТИЧНИ" if a==b else "  различни")

print("\n=== _sig_msg: weekly ===")
print("  🔴 БАЙТ-ИДЕНТИЧНИ" if sig(weekly=None)==sig(weekly={"x":1}) else "  различни")

print("\n=== _status_msg: macro ===")
m1=lb._status_msg([], "long", None, None, spot, None, 9.0, 0.2, {}, False, "2026-08-18",
                  {'миньори':True,'долар':True,'лихви':True})
m2=lb._status_msg([], "long", None, None, spot, None, 9.0, 0.2, {}, False, "2026-08-18",
                  {'миньори':False,'долар':False,'лихви':False})
print("  макро 3/3 vs 0/3:", "🔴 БАЙТ-ИДЕНТИЧНИ" if m1==m2 else "различни")

print("\n=== _pulse_msg: advice_txt + macro ===")
def pulse(adv, mac):
    return lb._pulse_msg("09", [], None, "long", adv, True, None, None, spot, None,
                         mac, False, False, macro_raw={"долар":0.01,"лихви":0.02},
                         streaks={"long":1}, stats=stats)
p1=pulse("ДА — влизай", {'долар':True,'лихви':True})
p2=pulse("НЕ — не влизай", {'долар':False,'лихви':False})
print("  ДА/3-3 vs НЕ/0-3:", "🔴 БАЙТ-ИДЕНТИЧНИ" if p1==p2 else "различни")
print(p1)

print("\n=== _exit_msg / _shadow_exit_msg: spot ===")
tr={"direction":"long","entry":4400.10,"levels":lv,"hit":{},"sym":"XAUUSD"}
e1=lb._exit_msg("sl",tr,4380.10,"2026-08-18T12:00","бар",False,spot=None)
e2=lb._exit_msg("sl",tr,4380.10,"2026-08-18T12:00","бар",False,spot=spot)
print("  _exit_msg spot:", "🔴 БАЙТ-ИДЕНТИЧНИ" if e1==e2 else "различни")
