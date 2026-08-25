# -*- coding: utf-8 -*-
import ast, io
src = io.open("live_bot.py", encoding="utf-8").read()
tree = ast.parse(src)
res=[]
for n in ast.walk(tree):
    if isinstance(n, ast.Call):
        f=n.func
        # os.environ.get(...)
        if isinstance(f, ast.Attribute) and f.attr in ("get","getenv"):
            s = ast.unparse(f)
            if "environ" in s or "getenv" in s:
                res.append((n.lineno, ast.unparse(n)))
    if isinstance(n, ast.Subscript):
        s=ast.unparse(n)
        if s.startswith("os.environ["):
            res.append((n.lineno, s))
res.sort()
print("env reads:", len(res))
seen={}
for ln,s in res:
    print(ln, s)
