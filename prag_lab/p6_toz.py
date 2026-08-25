# -*- coding: utf-8 -*-
"""P6: тъждественост на избора буква по буква + размер на обединението."""
import json, numpy as np
P=json.load(open("prag_lab/_picked_all.json"))
base=P["4/6"]
print("СРАВНЕНИЕ НА ИЗБРАНИТЕ ЧЕКПОЙНТИ срещу живото 4/6 (6858 входа):")
for k,v in P.items():
    same = (v==base)
    inter=len(set(v)&set(base))
    print(f"   {k:6s} n={len(v):>6}  тъждествен={'ДА' if same else 'НЕ':3s}  общи={inter:>6}  "
          f"само тук={len(set(v)-set(base)):>5}  само в 4/6={len(set(base)-set(v)):>5}")
u=set()
for v in P.values(): u|=set(v)
print(f"\nОБЕДИНЕНИЕ на всички конфигурации: {len(u):,} чекпойнта")
json.dump(sorted(u),open("prag_lab/_union.json","w"))
