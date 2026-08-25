# -*- coding: utf-8 -*-
import sys, io, json
sys.argv=["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import live_bot as lb

print("=== ТЕСТ 1: _status_msg с guard за СРЕБРО ===")
tr_g = None; tr_s=None
spot_g={"bid":4399.5,"ask":4400.1,"mid":4399.8,"src":"swq"}
spot_s={"bid":64.10,"ask":64.14,"mid":64.12,"src":"swq"}
for guard in ({"long":2},{"short":2},{"s_long":2},{"s_short":2},{"s_long":3,"short":2}):
    m = lb._status_msg([], "long", None, None, spot_g, spot_s, 9.0, 0.2, guard, False, "2026-08-18", {})
    ред = [x for x in m.split("\n") if "спрени днес" in x]
    print("  guard=%-28s -> %s" % (json.dumps(guard,ensure_ascii=False), ред or "НЯМА РЕД"))

print()
print("=== ТЕСТ 2: 'notes' in dir() вътре във функция ===")
def f():
    return 'notes' in dir()
print("  вътре в чужда функция без локална notes:", f())
import inspect
src = inspect.getsource(lb._status_msg)
print("  _status_msg има ли локална notes? ", "notes =" in src or "notes=" in src.replace("notes if",""))

print()
print("=== ТЕСТ 3: _отворена_стълба гърми -> стига ли бележка ===")
bad = {"direction":"long","entry":"боклук","levels":{},"hit":{}}
notes=[]
print("  с notes:", lb._отворена_стълба(bad, spot_g, notes), "notes=", notes)
# сега както го викат картите:
notes2=[]
m = lb._status_msg([], "long", bad, None, spot_g, None, 9.0, 0.2, {}, False, "2026-08-18", {})
print("  през _status_msg — бележка стигна ли до notes2?", notes2)
