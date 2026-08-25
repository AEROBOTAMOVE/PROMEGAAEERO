# -*- coding: utf-8 -*-
import json, collections, re, statistics as st
rows=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
san=[(i,r,r["saniti"]) for i,r in enumerate(rows)
     if r.get("spot_rejected") and isinstance(r.get("saniti"),dict) and r["saniti"].get("разлика") is not None]
c=collections.Counter()
for i,r,s in san:
    for n in (r.get("notes") or []):
        if "базис" in str(n): c[re.sub(r"[-+]?\d[\d.,]*","N",str(n))[:95]]+=1
print("== БЕЛЕЖКИ ЗА БАЗИСА в отрязаните ръна ==")
for k,v in c.most_common(6): print(f"  {v:4d} × {k}")
print()
print("== ЗНАК БЕЗ ПОГЛЕД В БЪДЕЩЕТО (spot_{i-1} + |скок| → spot_i) ==")
към=от_него=неопр=0; амп=[]
for i,r,s in san:
    ref=(r.get("bar") or 0)-(r.get("basis") or 0)
    prev=next((rows[j] for j in range(i-1,max(i-4,-1),-1) if rows[j].get("spot")), None)
    if not prev or not s.get("скок"): неопр+=1; continue
    p=prev["spot"]; k=s["скок"]
    cands=[p+k,p-k]
    good=[x for x in cands if abs(abs(ref-x)-s["разлика"])<0.35]
    if len(good)!=1: неопр+=1; continue
    sp=good[0]
    j=min(i+2,len(rows)-1); b0=r.get("bar"); b1=rows[j].get("bar")
    if b0 is None or b1 is None: неопр+=1; continue
    dv=(b1-b0)*(1 if sp>ref else -1)
    амп.append(dv)
    if dv>0: към+=1
    elif dv<0: от_него+=1
    else: неопр+=1
print(f"  възстановен знак: {към+от_него} случая (неопределени {неопр})")
print(f"  барът тръгна КЪМ отхвърлената цена: {към} | ОБРАТНО: {от_него}")
if амп: print(f"  медиана изминато КЪМ спота за 10 мин: {st.median(амп):+.2f}$ (при медиана разрив 10.12$)")
