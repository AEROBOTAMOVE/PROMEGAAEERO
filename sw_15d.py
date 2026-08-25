import sys, json, datetime as dt
sys.stdout.reconfigure(encoding='utf-8')
rows=[json.loads(l) for l in open('live/live_journal.jsonl',encoding='utf-8') if l.strip()]
rows=[r for r in rows if isinstance(r.get("board"),dict) and r["board"] and r["run_utc"]>="2026-08-18T05:00"]
rows.sort(key=lambda r:r["run_utc"])
def key_of(b):
    o=sorted({f"{v[0]}:{v[2]}" for v in b.values() if v[2]!="weak" and v[0]!="wait"})
    return f"{len(o)}|"+";".join(o)
print("ръна след ОДИТ-67 (18.08 07:00 +):", len(rows))
cur=None;start=None;prev=None;st=[]
for r in rows:
    k=key_of(r["board"]); t=dt.datetime.fromisoformat(r["run_utc"])
    if k!=cur:
        if cur is not None: st.append((cur,start,prev))
        cur,start=k,t
    prev=t
st.append((cur,start,prev))
for k,s,e in st: print(f"  {(e-s).total_seconds()/3600:6.2f}ч  {s}→{e}  {k}")
