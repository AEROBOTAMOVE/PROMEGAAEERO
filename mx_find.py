import ast, io, sys
p = "live_bot.py"
src = io.open(p, encoding="utf-8").read()
t = ast.parse(src)
for n in ast.walk(t):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        nm = n.name
        if "msg" in nm or "карта" in nm or "card" in nm:
            args = [a.arg for a in n.args.args]
            print(f"{n.lineno:6d}  {nm}({', '.join(args)})")
