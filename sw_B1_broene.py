# -*- coding: utf-8 -*-
import sys, ast, io, collections
sys.argv=["x"]
import live_bot as lb
print("CB module:", getattr(lb.CB, "__file__", None) or getattr(lb.CB,"__name__",None))
SL = None
import importlib
T = lb.CB.ТАБЛИЦА
print("len(CB.ТАБЛИЦА) =", len(T))
g = collections.Counter(v[1] for v in T.values())
print("групи:", dict(g), "брой групи:", len(g), "сбор:", sum(g.values()))
# същият ли обект е като на b_сливане?
import brain.b_сливане as SLm
print("CB.ТАБЛИЦА is SL.ТАБЛИЦА:", T is SLm.ТАБЛИЦА, " len(SL)=", len(SLm.ТАБЛИЦА))
print("SL file:", SLm.__file__)
# AST брой на литерала в b_сливане.py
src = io.open(SLm.__file__, encoding="utf-8").read()
tree = ast.parse(src)
for node in tree.body:
    if isinstance(node, ast.Assign) and any(getattr(t,"id","")=="ТАБЛИЦА" for t in node.targets):
        print("AST литерал ключове:", len(node.value.keys), "ред:", node.lineno)
# кои са «стъпала»
step = [k for k,v in T.items() if "стъпало" in v[2]]
print("стъпала:", len(step), step)
print("без стъпала:", len(T)-len(step))
print("без група А:", sum(1 for v in T.values() if v[1]!="А"))
print("без А и без стъпала:", sum(1 for k,v in T.items() if v[1]!="А" and "стъпало" not in v[2]))
# ред 16 от файла
lines = src.splitlines()
print("ред 16:", repr(lines[15]))
