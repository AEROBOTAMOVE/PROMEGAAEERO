# -*- coding: utf-8 -*-
import json, io, os, collections
P = os.path.dirname(os.path.abspath(__file__))
rows=[json.loads(l) for l in io.open(os.path.join(P,"live","sent_log.jsonl"),encoding="utf-8") if l.strip()]
st=[r for r in rows if r["tag"]=="standing"]
print("СТОЯЩИ общо:",len(st))
nov=[r for r in st if "🎯" in r["text"]]
print("в НОВИЯ формат (с 🎯 ред):",len(nov))
c=collections.Counter()
for r in st:
    if "не са единодушни" in r["text"]: c["макро СМЕСЕНО"]+=1
    elif "СРЕЩУ тази посока" in r["text"]: c["макро СРЕЩУ"]+=1
    elif "в същата посока" in r["text"]: c["макро ЗА"]+=1
    else: c["без макро ред"]+=1
    if "не влизам · не е пресен" in r["text"]: c["последен ред 'не е пресен'"]+=1
print(dict(c))
print()
# БАЗОВА ЧЕСТОТА: смесено ли беше макрото и в ДРУГИТЕ карти?
pl=[r for r in rows if r["tag"]=="pulse"]
p=collections.Counter()
for r in pl:
    p["двете се бият" if "двете се бият" in r["text"] else
      ("двете сочат" if "двете сочат" in r["text"] else "макро мълчи/др")]+=1
print("ПУЛСОВЕ (%d):"%len(pl), dict(p))
print()
print("--- последната стояща карта ---")
print(st[-1]["utc"]); print(st[-1]["text"])
