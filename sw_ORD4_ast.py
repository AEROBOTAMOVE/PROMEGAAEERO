# -*- coding: utf-8 -*-
import ast, io
src=io.open("live_bot.py",encoding="utf-8").read()
tree=ast.parse(src)
main=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="main"][0]
print("main():",main.lineno,"->",main.end_lineno)
hits=[]
for n in ast.walk(main):
    txt=None
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ("append","extend"):
        if isinstance(n.func.value,ast.Name) and n.func.value.id=="new_msgs":
            txt="new_msgs.%s(...)"%n.func.attr
    elif isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=="new_msgs":
        txt="new_msgs += ..."
    elif isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="new_msgs" for t in n.targets):
        txt="new_msgs = "+ast.unparse(n.value)[:60]
    if txt: hits.append((n.lineno,txt))
for ln,t in sorted(hits):
    ctx=src.splitlines()[ln-1].strip()[:90]
    print(f"{ln:5d}  {t:35s} | {ctx}")
# къде е _outbox_flush
for n in ast.walk(main):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="_outbox_flush":
        print("FLUSH на ред",n.lineno)
