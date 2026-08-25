# -*- coding: utf-8 -*-
"""AST карта на функциите-карти в live_bot.py (само четене)."""
import io, ast, sys

p = "live_bot.py"
src = io.open(p, encoding="utf-8").read()
t = ast.parse(src)
print("=== функции ===")
for n in ast.walk(t):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if n.name.endswith("_msg") or "msg" in n.name.lower() or n.name.startswith("_"):
            args = [a.arg for a in n.args.args]
            if n.name.endswith("_msg"):
                print(f"{n.lineno:6d}  {n.name}({', '.join(args)})")
print()
print("=== глави / заглавия речници ===")
for n in ast.walk(t):
    if isinstance(n, ast.Assign):
        for tg in n.targets:
            if isinstance(tg, ast.Name) and tg.id in ("глави", "ГЛАВИ", "ЗАГЛАВИЯ"):
                print(n.lineno, ast.unparse(n)[:2000])
