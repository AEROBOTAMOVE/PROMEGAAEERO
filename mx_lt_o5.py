# -*- coding: utf-8 -*-
import sys, io, runpy
sys.argv=["x"]; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0,".")
_r=sys.stdout
class _T(io.StringIO): buffer=io.BytesIO()
sys.stdout=_T(); m=runpy.run_path("mx_stopstoi4.py"); sys.stdout=_r
import live_bot as lb
нс=m["нов_стои"]
def L(t): return len(t.split("\n"))
_stm   = нс("short",27.4,4000.2,{"миньори":False,"долар":False,"лихви":False},{"мъртви":[]},"2026-07-29T10:00")
_млад  = нс("short",6.0 ,4000.2,{"миньори":False,"долар":False,"лихви":False},{"мъртви":[]},"2026-07-29T10:00")
_стар  = нс("long" ,500.0,4000.2,{"миньори":True,"долар":True,"лихви":True},{},"2026-07-29T10:00")
_stm2  = нс("short",20.0,4000.2,{"миньори":False,"долар":False,"лихви":False},{"мъртви":["долар"]},"2026-07-29T10:00")
for и,т in (("_stm 27.4ч",_stm),("_млад 6ч",_млад),("_стар 500ч",_стар),("_stm2 20ч мъртъв долар",_stm2)):
    print(f"== {и}: редове={L(т)} знаци={len(т)}")
print()
print("О5 «стоящата е къса — под 10 реда»:", L(_stm)<=10 and "1.59" not in _stm, "| редове:",L(_stm))
print("О5 «дава нивата»: 🛑 =", "🛑" in _stm, "| броя ️⃣ =", _stm.count("️⃣"))
print("О5 «НЕ чете лекция»:", "не покана" not in _stm and "Мерено:" not in _stm)
print("О5 «рендер/HTML/лимит»:", 30<len(_stm)<4096)
print()
print("--- МЛАД (6ч) ---"); print(_млад)
print()
print("_пари(0.052) =", lb._пари(0.052), "| _пари(0.231) =", lb._пари(0.231), "| _пари(-1.59) =", lb._пари(-1.59))
print()
print("--- _stm2 (мъртъв долар, шорт, 20ч) ---"); print(_stm2)
