import json, collections, statistics as st
P="live/live_journal.jsonl"
rows=[json.loads(l) for l in open(P,encoding="utf-8") if l.strip()]
print("общо ръна:", len(rows))
v=collections.Counter(r.get("v") for r in rows)
print("версии:", v.most_common())
# rejected по версия
tab=collections.defaultdict(lambda:[0,0])
for r in rows:
    k=r.get("v")
    tab[k][0]+=1
    if r.get("spot_rejected"): tab[k][1]+=1
for k in sorted(tab, key=lambda x:(x is None, str(x))):
    n,rej=tab[k]
    print(f"  {k:>10} n={n:5d} отрязани={rej:4d} ({100*rej/n:5.1f}%)")
