# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
rows=[json.loads(l) for l in open("live/sent_log.jsonl",encoding="utf-8") if l.strip()]
print("общо записа:", len(rows))
print("ключове:", sorted({k for r in rows for k in r})) 
br=[r for r in rows if "brain" in json.dumps(r,ensure_ascii=False)]
print("brain записи:", len(br))
for r in br[:3]:
    print("-----")
    print(json.dumps(r,ensure_ascii=False)[:1500])
