# -*- coding: utf-8 -*-
import json,re
sent=[json.loads(l) for l in open("live/sent_log.jsonl",encoding="utf-8") if l.strip()]
want=["2026-08-18T14:0","2026-08-18T15:3"]
for s in sent:
    if str(s.get("tag","")).startswith(("signal","s-signal")) and any(str(s["utc"]).startswith(w[:13]) for w in want):
        print("===", s["utc"], s["tag"])
        t=re.sub(r"<[^>]+>","",s["text"])
        for ln in t.split("\n")[:9]: print("   ",ln)
        print()
