# -*- coding: utf-8 -*-
import ast, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
def check(path, fname):
    src = io.open(path, encoding="utf-8").read()
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == fname:
            args = [a.arg for a in n.args.args] + [a.arg for a in n.args.kwonlyargs]
            body = n.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                body = body[1:]
            used = set()
            for m in body:
                for x in ast.walk(m):
                    if isinstance(x, ast.Name): used.add(x.id)
                    if isinstance(x, ast.arg): used.add(x.arg)
            dead = [a for a in args if a not in used]
            print(f"{path}::{fname}  аргументи={len(args)}  МЪРТВИ={dead}")
check("brain/b_карта.py", "сглоби")
check("live_bot.py", "_мозък_изход_msg")
check("live_bot.py", "_ma_alert_msg")
check("live_bot.py", "_спряна_msg")
