# -*- coding: utf-8 -*-
"""AST: ползва ли `сглоби` въобще `мерено`? И къде отива `_m` в live_bot?"""
import ast, sys
sys.stdout.reconfigure(encoding='utf-8')

src = open("brain/b_карта.py", encoding="utf-8").read()
t = ast.parse(src)
for f in ast.walk(t):
    if isinstance(f, ast.FunctionDef) and f.name == "сглоби":
        # изхвърляме докстринга
        тяло = f.body[1:] if (f.body and isinstance(f.body[0], ast.Expr)
                              and isinstance(f.body[0].value, ast.Constant)) else f.body
        имена = [n.id for b in тяло for n in ast.walk(b) if isinstance(n, ast.Name)]
        print("сглоби: редове %d-%d" % (f.lineno, f.end_lineno))
        print("  'мерено' в ТЯЛОТО (без докстринга):", "мерено" in имена)
        print("  всички имена в тялото:", sorted(set(имена)))
        # има ли изобщо низ 'мерен' в тялото
        тек = "\n".join(ast.unparse(b) for b in тяло)
        print("  подниз 'мерен' в разпарсеното тяло:", "мерен" in тек)

print()
src2 = open("live_bot.py", encoding="utf-8").read()
t2 = ast.parse(src2)
ползи = []
for n in ast.walk(t2):
    if isinstance(n, ast.Name) and n.id == "_m":
        ползи.append((n.lineno, type(n.ctx).__name__))
print("всяко ползване на името `_m` в live_bot.py:", ползи)
for л, к in ползи:
    print("   ред %d (%s): %s" % (л, к, src2.splitlines()[л-1].strip()))
