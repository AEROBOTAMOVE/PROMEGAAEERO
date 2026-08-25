import sys, json, datetime as dt
sys.stdout.reconfigure(encoding='utf-8')
sys.argv=["x"]; import live_bot as lb
print("REOFFER_MAX_AGE_H =", lb.REOFFER_MAX_AGE_H, "| REOFFER_H =", lb.REOFFER_H, "| РЕОФЕР_КЛАС =", lb.РЕОФЕР_КЛАС)

rows=[]
for l in open('live/live_journal.jsonl',encoding='utf-8'):
    l=l.strip()
    if not l: continue
    try: r=json.loads(l)
    except Exception: continue
    b=r.get("board")
    if not isinstance(b,dict) or not b: continue
    rows.append(r)
rows.sort(key=lambda r: r["run_utc"])
print("ръна с дъска:", len(rows), rows[0]["run_utc"], "→", rows[-1]["run_utc"])

def key_of(b):
    отч = sorted({f"{v[0]}:{v[2]}" for v in b.values() if v[2]!="weak" and v[0]!="wait"})
    return f"{len(отч)}|" + ";".join(отч)

# 1) СЕГАШНАТА формула
def stretches(fn):
    out=[]; cur=None; start=None; prev=None
    for r in rows:
        k=fn(r["board"]); t=dt.datetime.fromisoformat(r["run_utc"])
        if k!=cur:
            if cur is not None: out.append((cur,start,prev))
            cur=k; start=t
        prev=t
    if cur is not None: out.append((cur,start,prev))
    return out

for name,fn in (("СЕГА (различни отчети)", key_of),
                ("СТАРАТА (по рамка)", lambda b: "|".join(f"{k}:{v[0]}:{v[2]}" for k,v in sorted(b.items())))):
    st=stretches(fn)
    hrs=[(e-s).total_seconds()/3600 for _,s,e in st]
    over=[h for h in hrs if h>lb.REOFFER_MAX_AGE_H]
    print(f"\n{name}: {len(st)} отрязъка; макс {max(hrs):.1f}ч; медиана {sorted(hrs)[len(hrs)//2]:.2f}ч; "
          f"над {lb.REOFFER_MAX_AGE_H}ч: {len(over)}")
    over2=[h for h in hrs if h>=lb.REOFFER_H]
    print(f"   отрязъци, доживели поне REOFFER_H={lb.REOFFER_H}ч: {len(over2)}")
    print("   най-дългите 5:", [round(h,1) for h in sorted(hrs)[-5:]])
