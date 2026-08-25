# -*- coding: utf-8 -*-
import ast, io, sys, json
src = io.open("live_bot.py", encoding="utf-8").read()
lines = src.splitlines()
tree = ast.parse(src)
out=[]
for node in tree.body:
    if isinstance(node,(ast.Assign,ast.AnnAssign)):
        tgts = node.targets if isinstance(node,ast.Assign) else [node.target]
        names=[]
        for t in tgts:
            if isinstance(t,ast.Name): names.append(t.id)
            elif isinstance(t,ast.Tuple):
                for e in t.elts:
                    if isinstance(e,ast.Name): names.append(e.id)
        if not names: continue
        seg = "\n".join(lines[node.lineno-1:node.end_lineno])
        out.append((node.lineno,",".join(names),seg))
print("TOTAL module-level assigns:", len(out))
for ln,n,seg in out:
    print("="*70)
    print("L%d  %s" % (ln,n))
    print(seg[:600])
