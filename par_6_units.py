# -*- coding: utf-8 -*-
import ast, io, sys
src=open('live_bot.py',encoding='utf-8').read()
t=ast.parse(src)
out=[]
class V(ast.NodeVisitor):
    def __init__(self): self.fn=[]
    def visit_FunctionDef(self,n):
        self.fn.append(n.name); self.generic_visit(n); self.fn.pop()
    def visit_Call(self,n):
        f=n.func
        name = f.id if isinstance(f,ast.Name) else (f.attr if isinstance(f,ast.Attribute) else None)
        if name in ("_пипс","_пари","_разст"):
            args=[ast.unparse(a) for a in n.args]
            out.append(f"{n.lineno}\t[{'.'.join(self.fn) or 'МОДУЛ'}]\t{name}({', '.join(args)})")
        self.generic_visit(n)
V().visit(t)
open('par_units.txt','w',encoding='utf-8').write("\n".join(out))
print(len(out))
