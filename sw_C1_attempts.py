# -*- coding: utf-8 -*-
import ast, io, sys, pathlib
root = pathlib.Path(".")
targets = ["live_bot.py","selftest.py","audit_bot.py","стил.py"]
for t in targets:
    p = root/t
    if not p.exists(): print("НЯМА",t); continue
    src = p.read_text(encoding="utf-8")
    tree = ast.parse(src)
    hits=[]
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value,str) and "attempts" in n.value:
            hits.append((n.lineno,"STR",repr(n.value)[:90]))
        if isinstance(n, ast.Name) and "attempts" in n.id:
            hits.append((n.lineno,"NAME",n.id))
        if isinstance(n, ast.Attribute) and "attempts" in n.attr:
            hits.append((n.lineno,"ATTR",n.attr))
    hits=sorted(set(hits))
    print("=== ",t, len(hits))
    lines=src.splitlines()
    for ln,k,v in hits:
        print("  ",ln,k,v,"|",lines[ln-1].strip()[:120])
