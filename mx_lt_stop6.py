# -*- coding: utf-8 -*-
import sys, io, runpy
sys.argv=["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0,".")
_r=sys.stdout
class _T(io.StringIO):
    buffer=io.BytesIO()
sys.stdout=_T()
m=runpy.run_path("mx_stopstoi4.py")
sys.stdout=_r
import live_bot as lb
нов_стоп=m["нов_стоп"]; нов_стои=m["нов_стои"]
NOW="2026-08-21T10:00"

print("### СЛУЧАЙ 1 · ТП1 взет, СТОП с ГАП ПОД входа (стълба ОТРИЦАТЕЛНА)")
tr={"direction":"long","entry":4358.0,"sym":"XAUUSD","opened":"2026-08-19T09:00",
    "levels":{"tp1":4365.50,"tp2":4370.00,"tp3":4378.00,"sl":4358.00},
    "hit":{"tp1":True},"hit_px":{"tp1":4365.50}}
print(lb._exit_msg("sl", dict(tr), 4350.00, NOW, "бар", True))
print("--- НОВАТА:")
print(нов_стоп("sl", dict(tr), 4350.00, NOW, "бар", True, guard_n=0, next_line="", now_utc=NOW))

print()
print("### СЛУЧАЙ 2 · същото, но фил малко под входа (−0.30$)")
print(нов_стоп("sl", dict(tr), 4357.70, NOW, "бар", True, guard_n=0, next_line="", now_utc=NOW))

print()
print("### СЛУЧАЙ 3 · 5г (продажба, чист, ДА нова карта)")
print(m["К"]["5г СТОП · продажба · чист · нова карта идва"])

print()
print("### СЛУЧАЙ 4 · сделка под 1 час")
tr4={"direction":"long","entry":4358.0,"sym":"XAUUSD","opened":"2026-08-21T09:40",
     "levels":lb._levels(4358.0,"long"),"hit":{}}
print(нов_стоп("sl", tr4, 4338.00, NOW, "бар", False, guard_n=0, next_line="", now_utc=NOW))

print()
print("### СЛУЧАЙ 5 · СТОП с гап, но БЕЗ флаг gap (спот-път, _повече>0.5)")
tr5={"direction":"long","entry":4358.0,"sym":"XAUUSD","opened":"2026-08-20T09:00",
     "levels":lb._levels(4358.0,"long"),"hit":{}}
print(нов_стоп("sl", tr5, 4335.62, NOW, "спот", False, guard_n=0, next_line="", now_utc=NOW))

print()
print("### СЛУЧАЙ 6 · СТОИ · age_h точно None")
print(нов_стои("long", None, 4365.20, {"долар":True,"лихви":True}, {}, "2026-08-21T11:20"))

print()
print("### константи:", "PIP",lb.PIP,"SL_PIPS",lb.SL_PIPS,"S_SL",getattr(lb,"S_SL",None),
      "S_TPS",lb.S_TPS,"ДНИ_МАКС",lb.ДНИ_МАКС,"STANDING_H",lb.STANDING_H)
print("_пари(-22.38):",lb._пари(-22.38),"| _пари(0.0):",lb._пари(0.0))
