# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
rows=[json.loads(l) for l in open("live/sent_log.jsonl",encoding="utf-8") if l.strip()]
br=[r for r in rows if str(r.get("tag","")).startswith("brain:")]
print("brain: карти:", len(br))
for r in br:
    t=r["text"]
    print(r["utc"], "| ✗:%d мерено:%d НОВО:%d ред:%d" % ("✗" in t, "n=" in t or "мерено" in t, "НОВО" in t or "ново · " in t, len(t.split("\n"))))
