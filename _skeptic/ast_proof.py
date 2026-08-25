# -*- coding: utf-8 -*-
"""AST: за ВСЯКО присвояване на _спрян — веригата от обхващащи `if` условия."""
import ast, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PATH = sys.argv[1] if len(sys.argv) > 1 else "live_bot.py"
src = open(PATH, encoding="utf-8").read()
tree = ast.parse(src)

hits = []
def walk(node, chain):
    for ch in ast.iter_child_nodes(node):
        newchain = chain
        if isinstance(ch, ast.If):
            # тялото носи условието, orelse носи отрицанието му
            cond = ast.unparse(ch.test)
            for b in ch.body:
                walk(b, chain + [("if", cond)])
            for b in ch.orelse:
                walk(b, chain + [("elif/else от", cond)])
            continue
        if isinstance(ch, (ast.Assign,)):
            for t in ch.targets:
                if isinstance(t, ast.Name) and t.id == "_спрян":
                    hits.append((ch.lineno, ast.unparse(ch.value)[:48], list(chain)))
        walk(ch, newchain)

walk(tree, [])

print("ФАЙЛ:", PATH)
print("НАМЕРЕНИ присвоявания на _спрян:", len(hits))
print("=" * 78)
pod_should = 0
pod_not_should = 0
bez = 0
for ln, val, chain in hits:
    conds = [c for _k, c in chain]
    joined = " ;; ".join(conds)
    has_should = "should_sig" in joined
    # има ли `not should_sig` някъде във веригата
    neg = "not should_sig" in joined
    pos = ("should_sig and" in joined) or joined.strip().endswith("should_sig") or ("if should_sig" in "if "+joined)
    if neg:
        tag = ">>> ПОД `not should_sig`  <<<"; pod_not_should += 1
    elif has_should:
        tag = "    под should_sig"; pod_should += 1
    else:
        tag = "    без should_sig"; bez += 1
    print(f"ред {ln:5d} | {tag}")
    print(f"          стойност: {val}")
    for k, c in chain[-2:]:
        print(f"          {k}: {c[:150]}")
    print("-" * 78)

print()
print(f"ОБОБЩЕНИЕ: под `not should_sig` = {pod_not_should}")
print(f"           под `should_sig`     = {pod_should}")
print(f"           без споменаване      = {bez}")
