# -*- coding: utf-8 -*-
import sys, json, io
sys.stdout.reconfigure(encoding='utf-8')
sys.argv = ["x"]
import live_bot as lb

print("=== КОНСТАНТИ В ЖИВИЯ КОД ===")
for k in ["PIP","SL_D","TP1_D","TP2_D","TP3_D","MIN_N","МАЛЪК_РАЗМЕР_W","ZONE_W",
          "СТАТ_ЗАДЪЛЖИТЕЛНА","MAX_AGE_D","S_SL","СРЕБРО_СПРЕД","NEAR_HIGH_DD20"]:
    print(f"  {k} =", getattr(lb, k, "<НЯМА>"))

print()
print("=== ВСИЧКИ ИМЕНА С 'TP'/'ЦЕЛ'/'AGE'/'ДНИ' ===")
for k in dir(lb):
    if k.isupper() and any(s in k.upper() for s in ("TP","AGE","ДНИ","SL","РИСК","RISK")):
        print("  ",k,"=",getattr(lb,k))
