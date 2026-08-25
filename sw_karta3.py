# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
rows=[json.loads(l) for l in open("live/sent_log.jsonl",encoding="utf-8") if l.strip()]
br=[r for r in rows if str(r.get("tag","")).startswith("brain")]
print("brain карти в дневника:", len(br), " от", br[0]["utc"], "до", br[-1]["utc"])
import collections
def cls(t):
    return (("✗" in t), ("мерено" in t or "МЕРЕНО" in t or "n=" in t), ("НОВО" in t or "ново" in t))
c=collections.Counter(cls(r["text"]) for r in br)
print("(има✗, има мерено, има НОВО) -> брой:")
for k,v in c.items(): print("  ", k, v)
print()
for r in br[-3:]:
    print("=== ", r["utc"], r["tag"])
    print(r["text"])
    print()
