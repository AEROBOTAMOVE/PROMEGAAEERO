# -*- coding: utf-8 -*-
import sys, json, io, os
sys.argv=["x"]; import live_bot as lb
st=json.load(io.open("backtest_stats.json",encoding="utf-8"))
L=lb._защо_мълчи({"долар":0.012,"лихви":-0.31},{"long":3},"long",стат=st)
print("_защо_мълчи връща %d РЕДА (влиза САМО в пулса/обрата/статуса):"%len(L))
for r in L: print("   ",r)
print("\nпоследният ред вече е 👁 :", L[-1].startswith("👁"))
print("\nА стоящата карта има САМО ЕДИН макро-ред и НЯМА свой 👁 преди присъдата.")
# къде се вика _защо_мълчи
import ast
t=ast.parse(io.open("live_bot.py",encoding="utf-8").read())
c=[n.lineno for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="_защо_мълчи"]
print("_защо_мълчи се вика на редове:",c,"  (_standing_msg е на 599-634 → НЕ Е сред тях)")
