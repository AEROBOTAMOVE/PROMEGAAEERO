# -*- coding: utf-8 -*-
import sys, io, ast, textwrap
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def dostavi(path, name):
    src = open(path, encoding='utf-8').read()
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            seg = ast.get_source_segment(src, n)
            ns = {}
            exec(compile(seg, path, 'exec'), ns)
            return ns[name], src
    raise SystemExit('няма '+name)

стар, src_star = dostavi('_chernovi/_prefix_lb.py', '_reentry_ban')
нов,  src_nov  = dostavi('live_bot.py', '_reentry_ban')

print("╔═══ А · ПРЕДИ ФИКСА (v13.7) — 'до утре' удържа ли се? ═══")
meta = {}
# ден 1: два стопа, забраната се слага
print("  ден 1 слагане :", стар(meta, 'long', 2, why='2 стопа днес в тази посока — спирам до утре', set_it=True))
print("  запис         :", meta)
for ден in ('2026-08-19','2026-08-20','2026-08-21','2026-09-30','2027-01-01'):
    print(f"  {ден} стрийк 2 :", стар(meta, 'long', 2))
print("  записът оцеля :", meta)

print()
print("╔═══ Б · СЕГА (работно дърво) — същият сценарий ═══")
meta2 = {}
print("  ден 1 слагане :", нов(meta2, 'long', 2, why='2 стопа днес в тази посока — спирам до утре', set_it=True, ден='2026-08-19'))
print("  запис         :", meta2)
print("  същият ден    :", нов(meta2, 'long', 2, ден='2026-08-19'))
print("  СЛЕДВАЩ ден   :", нов(meta2, 'long', 2, ден='2026-08-20'))
print("  записът след  :", meta2)
