import json, sys
from datetime import datetime
p = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/live/live_journal.jsonl"
runs=[]; weekend=0; delnichni=0; mrtvi_cnt=0; mrtvi_prim=[]
bad=0
for ln in open(p, encoding="utf-8"):
    ln=ln.strip()
    if not ln: continue
    try: r=json.loads(ln)
    except Exception: bad+=1; continue
    t=r.get("run_utc")
    if not t: continue
    runs.append((t, bool(r.get("weekend"))))
    if r.get("weekend"): weekend+=1
    else:
        delnichni+=1
        mh = r.get("macro_raw") or r.get("macro_health") or {}
        m = (mh or {}).get("мъртви")
        if m:
            mrtvi_cnt+=1
            if len(mrtvi_prim)<5: mrtvi_prim.append((t,m))
print("записи:", len(runs), "| уикенд:", weekend, "| делнични:", delnichni, "| нечетими:", bad)
print("делнични с непразно macro['мъртви']:", mrtvi_cnt, mrtvi_prim)
# дупки между ПОСЛЕДОВАТЕЛНИ ДЕЛНИЧНИ ръна (както ги вижда макро-резервът: пише се само в делничен рън)
d=[t for t,w in runs if not w]
d=sorted(set(d))
print("уникални делнични печата:", len(d))
gaps=[]
for a,b in zip(d, d[1:]):
    h=(datetime.fromisoformat(b)-datetime.fromisoformat(a)).total_seconds()/3600
    if h>6: gaps.append((a,b,round(h,2)))
print("дупки >6ч между делнични ръна:", len(gaps))
for g in gaps: print("   ", g)
