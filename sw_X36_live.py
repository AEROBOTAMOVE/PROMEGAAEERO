# -*- coding: utf-8 -*-
import json, io, sys, re
sys.stdout.reconfigure(encoding="utf-8")
rows=[json.loads(l) for l in io.open("live/sent_log.jsonl",encoding="utf-8") if l.strip()]
p=[r for r in rows if r.get("tag")=="pulse"]
print("пулс-карти в sent_log:", len(p))
над=0
for r in p:
    txt=re.sub(r"<[^>]+>","",r["text"])
    ln=[x for x in txt.split("\n") if x.strip()]
    зн=len(txt)
    if len(ln)>7: над+=1
    print(f'{r["utc"]} · редове={len(ln)} знаци={зн} {"🔴" if len(ln)>7 else ""}')
print("НАД тавана 7:", над, "от", len(p))
