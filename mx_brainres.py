# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
rs = [json.loads(l) for l in open("live/brain_result.jsonl", encoding="utf-8") if l.strip()]
print("брой затворени наблюдения:", len(rs))
for r in rs:
    print({k: r.get(k) for k in ("отворен","степен","точки","посока","вход","цел1_взета","изход","цена_изход","част1","част2","резултат")})
res = [r.get("резултат") for r in rs if r.get("резултат") is not None]
print("сума:", round(sum(res),2), "средно:", round(sum(res)/len(res),2) if res else None,
      "печеливши:", sum(1 for x in res if x>0), "от", len(res))
js = [json.loads(l) for l in open("live/brain_journal.jsonl", encoding="utf-8") if l.strip()]
print("дневник записи:", len(js), "пратени:", sum(1 for j in js if j.get("праща")))
import collections
print("по степен (пратени):", collections.Counter(j.get("степен") for j in js if j.get("праща")))
print("първи/последен:", js[0].get("utc"), js[-1].get("utc"))
