# -*- coding: utf-8 -*-
import sys, io, json, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.argv=["x"]
# --- 1 · AST: чете ли `сглоби` изобщо параметъра `мерено`? ---
src = open("brain/b_карта.py", encoding="utf-8").read()
mod = ast.parse(src)
fn = [n for n in mod.body if isinstance(n, ast.FunctionDef) and n.name == "сглоби"][0]
имена = [n.id for n in ast.walk(fn) if isinstance(n, ast.Name)]
атрибути = [n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)]
print("тяло на сглоби · ползва ли 'мерено':", "мерено" in имена)
print("редове на сглоби:", fn.lineno, "-", fn.end_lineno)
# кои низове изобщо съществуват в тялото
низове = [n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
print("има ли низ с '✗':", any("✗" in s for s in низове))
print("има ли низ с 'НОВО':", any("НОВО" in s for s in низове))
print("има ли низ с 'мерен':", any("мерен" in s.lower() for s in низове))
