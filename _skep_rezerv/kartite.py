import json, collections
p=r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/live/sent_log.jsonl"
n=0; c=collections.Counter(); makro=0; prim=None
for l in open(p, encoding="utf-8"):
    l=l.strip()
    if not l: continue
    r=json.loads(l); n+=1
    c[str(r.get("tag","")).split(":")[0]]+=1
    t=r.get("text","")
    if "макро" in t.lower() or "МАКРО" in t:
        makro+=1
        if prim is None: prim=(r.get("utc"), r.get("tag"), t[:200])
print("пратени карти общо:", n)
print("по вид:", dict(c.most_common(15)))
print("карти, споменаващи 'макро':", makro, prim)
