# -*- coding: utf-8 -*-
import sys, io, json, ast, pathlib
sys.argv=["x"]
src=io.open("live_bot.py",encoding="utf-8").read()
tree=ast.parse(src)
# 1) намери реда на new_msgs.append(CB.карта(...)) и на извикването на _мозък_следене
class V(ast.NodeVisitor):
    def __init__(self): self.karta=[]; self.sled=[]; self.remove=[]
    def visit_Call(self,n):
        s=ast.unparse(n)
        if "new_msgs.append" in s and "CB.карта" in s: self.karta.append(n.lineno)
        if isinstance(n.func,ast.Name) and n.func.id=="_мозък_следене": self.sled.append(n.lineno)
        if "new_msgs.remove" in s or "new_msgs.pop" in s or "new_msgs.clear" in s: self.remove.append(n.lineno)
        self.generic_visit(n)
v=V(); v.visit(tree)
print("ред на new_msgs.append(CB.карта):", v.karta)
print("ред на извикване _мозък_следене:", v.sled)
print("някой маха от new_msgs?:", v.remove or "НЕ — нищо не трие/маха от new_msgs")
# 2) присвоявания на new_msgs (пренареждане/презаписване)
for n in ast.walk(tree):
    if isinstance(n,(ast.Assign,ast.AugAssign)):
        t=n.targets[0] if isinstance(n,ast.Assign) else n.target
        if isinstance(t,ast.Name) and t.id=="new_msgs":
            print("   присвояване new_msgs на ред",n.lineno,":",ast.unparse(n)[:80])
# 3) тялото на _мозък_следене: пипа ли new_msgs изобщо
fn=[x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name=="_мозък_следене"][0]
body=ast.unparse(fn)
print("_мозък_следене споменава new_msgs?:", "new_msgs" in body)
print("_мозък_следене редове:", fn.lineno, "-", fn.end_lineno)
