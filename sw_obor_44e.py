# -*- coding: utf-8 -*-
import ast, io, os, json, collections
P=os.path.dirname(os.path.abspath(__file__))
src=io.open(os.path.join(P,"live_bot.py"),encoding="utf-8").read()
t=ast.parse(src)
calls=[n for n in ast.walk(t) if isinstance(n,ast.Call)
       and isinstance(n.func,ast.Name) and n.func.id=="_standing_msg"]
print("ПОВИКВАНИЯ на _standing_msg:",len(calls),"на редове",[c.lineno for c in calls])
# намери if-а, който ги обгражда
for f in ast.walk(t):
    if isinstance(f,ast.If):
        ls=[n.lineno for n in ast.walk(f) if isinstance(n,ast.Call)
            and isinstance(n.func,ast.Name) and n.func.id=="_standing_msg"]
        if ls and f.lineno>3400:
            print("ПАЗАЧ на ред",f.lineno,":",ast.unparse(f.test))
# и определението на stale_setup
for a in ast.walk(t):
    if isinstance(a,ast.Assign) and any(isinstance(x,ast.Name) and x.id=="stale_setup" for x in a.targets):
        print("\nstale_setup (ред %d) ="%a.lineno)
        for part in ast.unparse(a.value).split(" and "):
            print("   AND", part)
