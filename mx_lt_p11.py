# -*- coding: utf-8 -*-
import sys, io, runpy
sys.argv=["x"]; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0,".")
_r=sys.stdout
class _T(io.StringIO): buffer=io.BytesIO()
sys.stdout=_T(); m=runpy.run_path("mx_stopstoi4.py"); sys.stdout=_r
import live_bot as lb
нов=m["нов_стоп"]
_E=4358.0
_LVs=lb._levels(_E,"short")
def _rtr(hit, sl_at_entry=True):
    return {"direction":"short","entry":_E,"hit":dict(hit),"sym":"XAUUSD",
            "opened":"2026-08-03T00:00:00",
            "levels":dict(_LVs, sl=(_E if sl_at_entry else _E+20.0))}
NOW="2026-08-04T00:30:00"
_be2=нов("sl",_rtr({"tp1":True,"tp2":True}),_E,"2026-08-03T03:01:00","бар",False,now_utc=NOW)
_be1=нов("sl",_rtr({"tp1":True}),_E,"2026-08-03T05:56:00","бар",False,now_utc=NOW)
_hard=нов("sl",_rtr({},False),_E+20.0,"2026-08-04T00:21:00","бар",False,now_utc=NOW)
T=[
 ("П11 стоп след 2 ТП НЕ се нарича СТОП", not _be2.split("\n")[0].startswith("🛑")),
 ("П11 стоп след 2 ТП се нарича НУЛА", "НУЛА" in _be2.split("\n")[0]),
 ("П11 +6.50 по стълбата", "+6.50$" in _be2),
 ("П11 +2.50 по стълбата", "+2.50$" in _be1),
 ("П11 заглавието казва «стопът беше на входа»", "стопът беше на входа" in _be2 and "стопът беше на входа" in _be1),
 ("П11 картата дава ОБЩАТА сметка («донесе»)", "+6.50$" in _be2 and "+2.50$" in _be1 and "донесе" in _be2 and "донесе" in _be1),
 ("П11 разграничава крака от общата сметка", "донесе" in _be2 and "пипса" in _be2 and _be2.count("$")>=2),
 ("П11 ИСТИНСКИЯТ стоп СИ ОСТАВА «🛑 СТОП»", _hard.split("\n")[0].startswith("🛑 СТОП")),
 ("П11 истинският стоп показва −20.00", _hard.count("−20.00$")>=1),
 ("П11 в пипсове −200", "−200 пипса" in _hard),
 ("П11 паричният ред НЕ смесва два минуса", not any(("-" in л and "−" in л) for л in _hard.split("\n"))),
 ("П11 истинският стоп НЕ твърди, че е безрисков", "НУЛА" not in _hard),
 ("П11 балансиран HTML", all(c.count("<b>")==c.count("</b>") and c.count("<i>")==c.count("</i>") for c in (_be2,_be1,_hard))),
]
for и,ok in T: print(("  ЗЕЛЕНО " if ok else "❌ ЧЕРВЕНО"), и)
print("\n--- _be2 ---"); print(_be2)
print("\n--- _hard ред по ред за двата минуса ---")
for л in _hard.split("\n"):
    if "-" in л: print("   има ASCII '-':", л[:80], "| има '−':", "−" in л)

# СПРЕД-СЛУЧАЙ: спот-път, фил под нивото с ПО-МАЛКО от спред → gap=False, но _повече>0.5
print("\n### СПРЕД (не гап!) · лонг, стоп 4338.00, фил 4337.70 (0.30$ = под един спред)")
tr={"direction":"long","entry":4358.0,"sym":"XAUUSD","opened":"2026-08-20T09:00",
    "levels":lb._levels(4358.0,"long"),"hit":{}}
print(нов("sl",dict(tr),4337.70,"2026-08-21T10:00","спот",False,now_utc="2026-08-21T10:00"))
