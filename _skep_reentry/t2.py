# -*- coding: utf-8 -*-
import sys, io, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
src = open("live_bot.py", encoding="utf-8").read()
tree = ast.parse(src)
# намери реда на чистещия блок
lines = src.splitlines()
target = None
for i,l in enumerate(lines,1):
    if 'notes.append("♻️ забраната за ре-влизане падна' in l:
        target = i
print("чистещ блок на ред:", target)
for n in ast.walk(tree):
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
        if n.lineno <= target <= max(getattr(x,'lineno',n.lineno) for x in ast.walk(n)):
            end = max(getattr(x,'lineno',n.lineno) for x in ast.walk(n))
            print(f"функция {n.name}  редове {n.lineno}..{end}")
            rets = [r.lineno for r in ast.walk(n) if isinstance(r,ast.Return) and r.lineno < target]
            raises = [r.lineno for r in ast.walk(n) if isinstance(r,ast.Raise) and r.lineno < target]
            print("  return-и ПРЕДИ блока:", rets)
            print("  raise-и ПРЕДИ блока:", raises)
