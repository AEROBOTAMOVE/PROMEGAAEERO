# -*- coding: utf-8 -*-
import ast, io, sys
sys.stdout.reconfigure(encoding="utf-8")
src = io.open("live_bot.py", encoding="utf-8").read()
t = ast.parse(src)
for n in ast.walk(t):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = [a.arg for a in n.args.args]
        print("%-34s L%-5d %s" % (n.name, n.lineno, ", ".join(args)))
