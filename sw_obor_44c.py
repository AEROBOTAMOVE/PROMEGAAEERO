# -*- coding: utf-8 -*-
import json, io, os, collections
P = os.path.dirname(os.path.abspath(__file__))
rows=[json.loads(l) for l in io.open(os.path.join(P,"live","sent_log.jsonl"),encoding="utf-8") if l.strip()]
st=[r for r in rows if r["tag"]=="standing" and "🎯" in r["text"]]
d0,d1=st[0]["utc"][:10], st[-1]["utc"][:10]
print("нов формат стоящи: от",d0,"до",d1)
win=[r for r in rows if d0<=r["utc"][:10]<=d1]
print("ВСИЧКИ карти в този прозорец:",len(win))
c=collections.Counter()
for r in win:
    t=r["text"]
    if "двете се бият" in t or "не са единодушни" in t: c["макро СМЕСЕНО"]+=1
    elif "двете сочат" in t or "в същата посока" in t: c["макро ПОДРЕДЕНО"]+=1
print("  ",dict(c))
print()
# има ли ИЗОБЩО подредено макро някъде в целия дневник?
al=[r for r in rows if ("двете сочат" in r["text"] or "в същата посока" in r["text"])]
print("карти с ПОДРЕДЕНО макро в ЦЕЛИЯ дневник:",len(al))
mx=[r for r in rows if ("двете се бият" in r["text"] or "не са единодушни" in r["text"])]
print("карти със СМЕСЕНО макро в целия дневник:",len(mx), "от",mx[0]["utc"][:10],"до",mx[-1]["utc"][:10])
