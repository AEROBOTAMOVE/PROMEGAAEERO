# -*- coding: utf-8 -*-
import subprocess, ast, sys
def src(rev):
    if rev is None:
        return open("live_bot.py",encoding="utf-8").read()
    return subprocess.run(["git","show",f"{rev}:live_bot.py"],capture_output=True).stdout.decode("utf-8")
def fn(txt,name):
    t=ast.parse(txt)
    for n in ast.walk(t):
        if isinstance(n,ast.FunctionDef) and n.name==name:
            return ast.get_source_segment(txt,n)
    return None
for rev in ("bbf6f77",):
    try:
        old=fn(src(rev),"_spot_sane"); new=fn(src(None),"_spot_sane")
        if old is None: print(rev,"-> няма функцията/комита"); continue
        import re
        def логика(s):  # само изпълнимият код, без коментари/докстринг
            t=ast.parse(s); f=t.body[0]
            if isinstance(f.body[0],ast.Expr) and isinstance(f.body[0].value,ast.Constant): f.body=f.body[1:]
            return ast.dump(ast.parse(ast.unparse(f)))
        print(f"{rev}: байт-за-байт идентични: {old==new} | ЛОГИКАТА идентична: {логика(old)==логика(new)}")
        print(f"  редове тогава {len(old.splitlines())} → сега {len(new.splitlines())}")
    except Exception as e: print(rev, type(e).__name__, e)
