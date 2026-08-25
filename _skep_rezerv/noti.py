import json, collections
p = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/live/live_journal.jsonl"
c = collections.Counter(); prim = {}
klyuchove = collections.Counter()
n=0
for ln in open(p, encoding="utf-8"):
    ln=ln.strip()
    if not ln: continue
    r=json.loads(ln); n+=1
    for k in r: klyuchove[k]+=1
    for note in (r.get("notes") or r.get("бележки") or r.get("status") or []):
        s=str(note)
        if "резерв" in s or "не се дърп" in s or "О1" in s:
            key=s[:60]; c[key]+=1; prim.setdefault(key, r.get("run_utc"))
print("записи:", n)
print("ключове в записа:", dict(klyuchove.most_common(20)))
print("--- бележки за резерв/мъртъв фийд ---")
for k,v in c.most_common(): print(f"{v:5d}  (първо {prim[k]})  {k}")
