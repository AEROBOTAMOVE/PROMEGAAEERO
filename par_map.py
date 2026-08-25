import ast,sys
src=open('live_bot.py',encoding='utf-8').read()
t=ast.parse(src)
out=[]
for n in t.body:
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
        out.append(f"{n.lineno}\tdef {n.name}")
    elif isinstance(n,ast.ClassDef):
        out.append(f"{n.lineno}\tclass {n.name}")
        for m in n.body:
            if isinstance(m,(ast.FunctionDef,ast.AsyncFunctionDef)): out.append(f"   {m.lineno}\tdef {m.name}")
open('par_map.txt','w',encoding='utf-8').write("\n".join(out))
print(len(out))
