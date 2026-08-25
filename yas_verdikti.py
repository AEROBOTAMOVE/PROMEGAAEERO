# -*- coding: utf-8 -*-
"""Кои присъди изобщо СЪЩЕСТВУВАТ с живата статистика + коя клетка ги е дала."""
import sys, json
sys.argv = ["x"]
import live_bot as lb

stats = json.load(open("backtest_stats.json", encoding="utf-8"))
print("| посока | стрийк | клетка | n | нето$ | 95% | присъда |")
for d in ("long", "short"):
    for st in (0, 1, 2, 3, 4, 5, 7):
        for dd20 in (None, 0.005):
            tr = {}
            txt, ok = lb._advice_entry(d, st, stats, None, False, 0, "XAUUSD",
                                       dd20=dd20, trace=tr)
            м = tr.get("мерено") or {}
            print(f"{d:5} стрийк={st} dd20={dd20}  кофа={м.get('кофа','—'):12} "
                  f"n={м.get('n')} нето={м.get('net')} [{м.get('lo')}..{м.get('hi')}] "
                  f"by={tr.get('by')}  →  ok={ok}  «{txt}»")

print("\n=== _cell_name ===")
for st in (0, 1, 2, 3, 4, 9):
    print(st, lb._cell_name(st))

print("\n=== МЪРТВО ЛИ Е `риск`? AST-проверка на _sig_msg ===")
import ast, io
src = io.open("live_bot.py", encoding="utf-8").read()
tree = ast.parse(src)
fn = next(n for n in ast.walk(tree)
          if isinstance(n, ast.FunctionDef) and n.name == "_sig_msg")
чете, пише = [], []
for n in ast.walk(fn):
    if isinstance(n, ast.Name) and n.id in ("риск", "лот_окр", "лот"):
        (пише if isinstance(n.ctx, ast.Store) else чете).append((n.id, n.lineno))
print("ЗАПИСИ :", пише)
print("ЧЕТЕНИЯ:", чете)
