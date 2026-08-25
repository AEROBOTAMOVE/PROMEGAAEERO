# -*- coding: utf-8 -*-
import ast
src=open('live_bot.py',encoding='utf-8').read()
t=ast.parse(src)
res=[]
for n in ast.walk(t):
    if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): continue
    a=n.args
    params=[x.arg for x in a.posonlyargs+a.args+a.kwonlyargs]
    if a.vararg: params.append(a.vararg.arg)
    if a.kwarg: params.append(a.kwarg.arg)
    used=set()
    for sub in ast.walk(n):
        if isinstance(sub,ast.Name): used.add(sub.id)
        elif isinstance(sub,ast.Attribute):
            pass
    # също имена в f-string и т.н. са Name възли -> покрити
    dead=[p for p in params if p not in used and p!="self"]
    if dead:
        res.append(f"{n.lineno}\t{n.name}\tМЪРТВИ ПАРАМЕТРИ: {', '.join(dead)}")
open('par_mrtvi.txt','w',encoding='utf-8').write("\n".join(res))
print("\n".join(res))
