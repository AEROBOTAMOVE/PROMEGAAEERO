# -*- coding: utf-8 -*-
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
ln=[l for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
recs=[json.loads(l) for l in ln]
print("записи:",len(recs))
print("от",recs[0]["run_utc"],"до",recs[-1]["run_utc"])
имабоард=sum(1 for r in recs if isinstance(r.get("board"),dict) and r["board"])
print("с борд (dict):",имабоард)
print("с gate:",sum(1 for r in recs if isinstance(r.get("gate"),dict)))
print("с gate.ok=True:",sum(1 for r in recs if isinstance(r.get("gate"),dict) and r["gate"].get("ok")))
print("trade != None:",sum(1 for r in recs if r.get("trade")))
# формат на борда — има ли други
формати=set()
for r in recs:
    b=r.get("board")
    if isinstance(b,dict):
        for v in b.values(): формати.add(type(v).__name__+":"+str(len(v)) if hasattr(v,'__len__') else type(v).__name__)
    else: формати.add("НЕ-dict:"+type(b).__name__)
print("формати на клетките:",формати)
# версии
from collections import Counter
print("версии:",Counter(r.get("v") for r in recs).most_common())
# дати
дни=Counter(r.get("date") for r in recs)
print("дни:",sorted(дни.items())[:5],"...",sorted(дни.items())[-5:])
