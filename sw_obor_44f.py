# -*- coding: utf-8 -*-
import json, io, os, collections
P=os.path.dirname(os.path.abspath(__file__))
rows=[json.loads(l) for l in io.open(os.path.join(P,"live","sent_log.jsonl"),encoding="utf-8") if l.strip()]
sig=[r for r in rows if r["tag"]=="signal" and "2026-08-11"<=r["utc"][:10]<="2026-08-17"]
print("СИГНАЛНИ карти в СЪЩИЯ прозорец (макрото е смесено 100%%):",len(sig))
if sig:
    print("--- пример:",sig[-1]["utc"],"---")
    print(sig[-1]["text"][:900])
