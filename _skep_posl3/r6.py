# -*- coding: utf-8 -*-
import sys, io, os, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
os.chdir(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
src = open("live_bot.py", encoding="utf-8").read()
tree = ast.parse(src)

# 1) какви файлове ПИША _мозък_следене
fn = next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="_мозък_следене")
пиша = set()
for n in ast.walk(fn):
    if isinstance(n,ast.Call):
        f=n.func
        име = getattr(f,"attr",None) or getattr(f,"id",None)
        if име in ("open","unlink","write","write_text","_запиши_атомарно","_load_state","mkdir","replace"):
            пиша.add(име+"("+ast.unparse(n.args[0])[:40]+")" if n.args else име+"()")
print("### В · какво ДОКОСВА _мозък_следене (AST на текущия файл)")
for x in sorted(пиша): print("   ", x)
имена = {ast.unparse(n) for n in ast.walk(fn) if isinstance(n,ast.Name)}
print("   споменава ли trade.json/state/guard/meta/outbox?",
      [w for w in ("trade","guard","meta","state","outbox","balance","статистика","stats") if w in имена] or "НЕ")

# 2) под какви условия се праща мозъчната КАРТА и къде спрямо следенето
класове = {}
for n in ast.walk(tree):
    for ch in ast.iter_child_nodes(n): класове[ch]=n
def предци(n):
    p=[]; 
    while n in класове:
        n=класове[n]
        if isinstance(n,ast.If): p.append("if "+ast.unparse(n.test)[:70])
        if isinstance(n,ast.For): p.append("for "+ast.unparse(n.target)[:30]+" in "+ast.unparse(n.iter)[:40])
        if isinstance(n,ast.FunctionDef): p.append("def "+n.name)
    return list(reversed(p))

карта=следене=None
for n in ast.walk(tree):
    if isinstance(n,ast.Call) and ast.unparse(n.func)=="new_msgs.append" and "CB.карта" in ast.unparse(n):
        карта=n
    if isinstance(n,ast.Call) and ast.unparse(n.func)=="_мозък_следене":
        следене=n
print()
print("### Г · условията НАД мозъчната КАРТА (ред %d)" % карта.lineno)
for c in предци(карта): print("     ", c)
print("### Г · условията НАД _мозък_следене (ред %d)" % следене.lineno)
for c in предци(следене): print("     ", c)
print()
print("   картата е на ред %d, следенето на ред %d → картата излиза ПРЕДИ и НЕЗАВИСИМО: %s"
      % (карта.lineno, следене.lineno, карта.lineno < следене.lineno))
