# -*- coding: utf-8 -*-
"""P9: колко често се сменя КЛАСЪТ срещу колко често се сменя score-ът, и
единственото изключение под 4 в живия дневник."""
import json,io,collections
rows=[json.loads(l) for l in io.open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
FR=["1мин","5м","15м","30м","1час","4час","1ден"]
def cell(d,f,TM=4,TS=6):
    v=(d.get("board") or {}).get(f)
    if not isinstance(v,list) or len(v)<3: return None
    dr,sc=v[0],v[1]; mac=d.get("macro") or {}
    mrt=(d.get("macro_raw") or {}).get("мъртви") or []
    if dr=="wait": tk="weak"
    else:
        m3=all(mac.values()) if dr=="long" else (not any(mac.values()))
        tk="premium" if m3 else ("strong" if sc>=TS else ("medium" if sc>=TM else "weak"))
        if tk=="premium" and mrt: tk="strong"
    return dr,sc,tk

print("ЖИВИЯТ ДНЕВНИК · 4404 ръна, преход между ПОСЛЕДОВАТЕЛНИ ръна:")
print(f"{'рамка':>6} {'смени на score':>15} {'смени на КЛАС':>15} {'смени на посока':>16} {'дял клас/score':>16}")
for f in FR:
    ps=pc=pd_=None; ns=nc=nd=0
    for d in rows:
        c=cell(d,f)
        if c is None: continue
        dr,sc,tk=c
        if ps is not None:
            if sc!=ps: ns+=1
            if tk!=pc: nc+=1
            if dr!=pd_: nd+=1
        ps,pc,pd_=sc,tk,dr
    print(f"{f:>6} {ns:>15} {nc:>15} {nd:>16} {(nc/ns if ns else 0):>15.0%}")
print()
print("Разстояние на score-а до праговете (живи клетки с посока):")
h=collections.Counter()
for d in rows:
    for f in FR:
        c=cell(d,f)
        if c and c[0]!="wait": h[c[1]]+=1
tot=sum(h.values())
for s in sorted(h):
    маркер = "  <-- прагът MEDIUM (>=4)" if s==4 else ("  <-- прагът STRONG (>=6)" if s==6 else "")
    print(f"   score={s}: {h[s]:>7,}  {100*h[s]/tot:6.2f}%{маркер}")
print(f"   под 4: {sum(v for k,v in h.items() if k<4):,}   на или над 6: {sum(v for k,v in h.items() if k>=6):,}")
print()
print("ЕДИНСТВЕНАТА клетка с посока и score<4:")
for d in rows:
    for f in FR:
        c=cell(d,f)
        if c and c[0]!="wait" and c[1]<4:
            print("   ",d["run_utc"],f,c,"macro=",d.get("macro"),"мъртви=",(d.get("macro_raw") or {}).get("мъртви"),
                  "  status=",d.get("status"))
