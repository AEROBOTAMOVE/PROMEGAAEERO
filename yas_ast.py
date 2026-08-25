# -*- coding: utf-8 -*-
import ast, io, sys
from pathlib import Path
Б = Path(__file__).resolve().parent
src = io.open(Б/"live_bot.py", encoding="utf-8").read()
t = ast.parse(src)
for n in ast.walk(t):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if "msg" in n.name.lower() or "карт" in n.name.lower() or n.name.endswith("_txt"):
            args = [a.arg for a in n.args.args]
            d = ast.get_docstring(n) or ""
            print(f"{n.lineno:6d}  {n.name}({', '.join(args)})")
            if d: print("        # " + d.split("\n")[0][:100])
