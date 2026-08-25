# -*- coding: utf-8 -*-
import json, os, collections
D = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/live"
p = os.path.join(D, "live_journal.jsonl")
rows=[]
for ln in open(p, encoding="utf-8"):
    ln=ln.strip()
    if not ln: continue
    try: rows.append(json.loads(ln))
    except Exception: pass
print("записи:", len(rows))
tf=[r for r in rows if r.get("tf_basis") is not None]
print("записи с tf_basis:", len(tf))
by=collections.defaultdict(list)
for r in tf:
    d=str(r.get("ts") or r.get("time") or r.get("utc") or "")[:10]
    by[d].append((float(r["tf_basis"]), float(r.get("price") or r.get("bar") or 0)))
for d in sorted(by):
    v=[x[0] for x in by[d]]; pr=[x[1] for x in by[d] if x[1]]
    v.sort()
    med=v[len(v)//2]
    print("%s  n=%3d  медиана %+8.2f  min %+8.2f  max %+8.2f  цена~%.0f  |med|=%.2f%% от цената"
          % (d, len(v), med, v[0], v[-1], (sum(pr)/len(pr) if pr else 0),
             (100*abs(med)/(sum(pr)/len(pr)) if pr else 0)))
# заклещване: колко пъти поред една и съща стойност
seq=[float(r["tf_basis"]) for r in tf]
best=1; cur=1
for i in range(1,len(seq)):
    cur = cur+1 if seq[i]==seq[i-1] else 1
    best=max(best,cur)
print("най-дълга серия С ЕДНА И СЪЩА стойност:", best, "поредни ръна")
print("макс |tf_basis| в целия дневник:", max(abs(x) for x in seq))
