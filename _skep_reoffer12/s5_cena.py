# -*- coding: utf-8 -*-
"""S5: КОЛКО СТРУВА вратата. Коя спирачка е БИНДИНГ — възрастта или гейтът?"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0,".")
import pandas as pd, live_bot as LB
from collections import Counter
exec(open("_skep_reoffer12/s3_replay.py",encoding="utf-8").read().split("for етикет,ск in")[0])
ред=прогон(старключ=False)

карти=[x for x in ред if x["should"]]
print("пратени карти в реплея:",len(карти))
print("  от тях с gate.ok=True (тоест РЕАЛЕН вход):",sum(1 for x in карти if x["gok"]))
print("  по дни:",Counter(x["utc"][:10] for x in карти))
print()
# бордът днес — мени ли се ключът след 11:46?
дн=[x for x in ред if x["utc"][:10]=="2026-08-21"]
print("21.08: различни ключове:",Counter(x["key"] for x in дн))
print("21.08: ръна с жив сетъп:",sum(1 for x in дн if x["act"]),"/",len(дн))
gок=[x for x in дн if x["gok"]]
print("21.08: gate.ok=True ръна:",len(gок),"| от",gок[0]["utc"],"до",gок[-1]["utc"])
print("21.08: блокери при gate.ok=True:",Counter(x["блокер"] or ("ПРАТЕНА" if x["should"] else "?") for x in gок))
print("21.08: възраст на ключа при първия gate.ok:",round(gок[0]["key_age"],2),"ч")
print()
# 06.08→18.08: имало ли е ИЗОБЩО gate.ok
пер=[x for x in ред if "2026-08-06T23:03"<=x["utc"]<="2026-08-18T15:26"]
print("06.08→18.08 (280.4ч):",len(пер),"ръна · gate.ok=True в",sum(1 for x in пер if x["gok"]))
print("  блокери:",Counter(x["блокер"] for x in пер).most_common(6))
print()
# има ли РЕАЛНО пратена карта днес, която реплеят също дава
print("реплей — карти на 21.08:",[ (x['utc'],x['причина'],x['gok']) for x in карти if x['utc'][:10]=='2026-08-21'])
