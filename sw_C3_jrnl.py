# -*- coding: utf-8 -*-
import json, collections, pathlib
p = pathlib.Path("live/live_journal.jsonl")
cnt = collections.Counter(); runs=0; withstat=0
ex=[]
for ln in p.read_text(encoding="utf-8",errors="replace").splitlines():
    if not ln.strip(): continue
    try: r=json.loads(ln)
    except Exception: continue
    runs+=1
    st=r.get("status")
    if st is None: continue
    withstat+=1
    for s in st:
        s=str(s)
        if "SEND_FAILED" in s or "HARD_FAIL" in s or "=SENT" in s or "DRY" in s or "ОТРОВНО" in s or "опашката преля" in s:
            key = s.split("=")[-1][:22] if "=" in s else s[:22]
            cnt[key]+=1
            if ("SEND_FAILED" in s or "HARD_FAIL" in s) and len(ex)<8: ex.append((r.get("run_utc"),s[:110]))
print("рънове в дневника:", runs, "· със 'status':", withstat)
for k,v in cnt.most_common(15): print(f"  {v:6d}  {k}")
print("примери за провал:")
for e in ex: print("   ", e)
