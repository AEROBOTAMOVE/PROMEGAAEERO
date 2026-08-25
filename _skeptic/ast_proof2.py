# -*- coding: utf-8 -*-
import ast, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
PATH = sys.argv[1]
tree = ast.parse(open(PATH, encoding="utf-8").read())
hits = []

def walk_stmt(st, chain):
    if isinstance(st, ast.If):
        c = ast.unparse(st.test)
        for b in st.body:   walk_stmt(b, chain + [("IF   ", c)])
        for b in st.orelse: walk_stmt(b, chain + [("ELSE¬", c)])
        return
    if isinstance(st, ast.Assign):
        for t in st.targets:
            if isinstance(t, ast.Name) and t.id == "_спрян":
                hits.append((st.lineno, ast.unparse(st.value)[:46], list(chain)))
    # рекурсия във всяко тяло-поле
    for f in ("body", "orelse", "finalbody", "handlers"):
        for b in getattr(st, f, []) or []:
            if isinstance(b, ast.stmt): walk_stmt(b, chain)
            else:
                for bb in getattr(b, "body", []): walk_stmt(bb, chain)

for st in tree.body: walk_stmt(st, [])

print("ФАЙЛ:", PATH, "| намерени присвоявания:", len(hits))
print("="*80)
n_not, n_yes, n_none = 0, 0, 0
for ln, val, chain in hits:
    j = " ;; ".join(c for _k, c in chain)
    if "not should_sig" in j:      tag, n_not  = "ПОД `not should_sig`  ✅ ДОСТИЖИМА ПРИ МЪЛЧАНИЕ", n_not+1
    elif "should_sig" in j:        tag, n_yes  = "под should_sig", n_yes+1
    else:                          tag, n_none = "без should_sig", n_none+1
    print(f"ред {ln:5d} | {tag}")
    print(f"          = {val}")
    for k, c in chain: print(f"          {k} {c[:130]}")
    print("-"*80)
print(f"\nИТОГ: под `not should_sig` = {n_not} | под `should_sig` = {n_yes} | без = {n_none}")
