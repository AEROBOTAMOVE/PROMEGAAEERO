# -*- coding: utf-8 -*-
import json, collections, io
J="live/brain_journal.jsonl"; R="live/brain_result.jsonl"
rows=[json.loads(l) for l in io.open(J,encoding="utf-8") if l.strip()]
print("общо записа в дневника:", len(rows))
pr=[r for r in rows if r.get("праща")]
print("праща=True:", len(pr))
# групиране по рън (utc)
by=collections.Counter(r["utc"] for r in pr)
print("рънове с поне 1 пратена:", len(by))
mult={k:v for k,v in by.items() if v>1}
print("рънове с >1 пратена в СЪЩИЯ рън:", len(mult), "=> изгубени от `or`:", sum(v-1 for v in mult.values()))
for k,v in sorted(mult.items())[:20]: print("   ", k, v)
# резултати
res=[json.loads(l) for l in io.open(R,encoding="utf-8") if l.strip()]
print("развръзки в brain_result:", len(res))
# кои са пратените по време
print("първа пратена:", min(r["utc"] for r in pr), " последна:", max(r["utc"] for r in pr))
print("първа развръзка:", min(r["отворен"] for r in res), " последна:", max(r.get("затворен","") for r in res))
