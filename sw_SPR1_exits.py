import json, collections, io
P="live/live_journal.jsonl"
via=collections.Counter(); kinds=collections.Counter()
rows=[]
n=0
for ln in io.open(P,encoding="utf-8"):
    ln=ln.strip()
    if not ln: continue
    try: r=json.loads(ln)
    except Exception: continue
    n+=1
    for e in (r.get("exits") or []):
        # e = (kind, price, when, via, gap) or dict
        if isinstance(e,(list,tuple)) and len(e)>=4:
            kinds[e[0]]+=1; via[(e[0],e[3])]+=1
            rows.append((r.get("run_utc"),e[0],e[1],e[3],r.get("spot"),r.get("spread"),json.dumps(r.get("trade"),ensure_ascii=False)))
        else:
            kinds[("?"+str(type(e)))]+=1
print("ръна:",n)
print("вид:",dict(kinds))
print("вид×път:",{f"{k[0]}/{k[1]}":v for k,v in sorted(via.items())})
print("---- първите 5 записа ----")
for r in rows[:5]: print(r)
