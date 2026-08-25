# -*- coding: utf-8 -*-
import json, io, sys, re
sys.stdout.reconfigure(encoding="utf-8")
rows=[json.loads(l) for l in io.open("live/sent_log.jsonl",encoding="utf-8") if l.strip()]
p=[r for r in rows if r.get("tag")=="pulse"]
for r in p[-2:]:
    print("---", r["utc"]); print(re.sub(r"<[^>]+>","",r["text"]))
# има ли ръна с отворена сделка изобщо
j=[json.loads(l) for l in io.open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
k=[x for x in j if x.get("trade") or x.get("open_trade") or x.get("trade_open")]
print("ключове на един ред:", sorted(j[-1].keys()))
