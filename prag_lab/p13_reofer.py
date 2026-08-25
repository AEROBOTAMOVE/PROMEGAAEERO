# -*- coding: utf-8 -*-
"""P13: следствието. live_bot.py:4091 твърди «actionable вече иска tier != weak —
ТОВА Е прагът на входа». Мери се дали `rank(best) >= rank(РЕОФЕР_КЛАС=medium)`
може изобщо да е False."""
import json, io, collections
rows=[json.loads(l) for l in io.open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
rank={"premium":3,"strong":2,"medium":1,"weak":0}
TFS=["1мин","5м","15м","30м","1час","4час","1ден"]
бавност={l:i for i,l in enumerate(TFS)}
akt=0; bestc=collections.Counter(); falsy=0; blok_strong=0
for d in rows:
    mac=d.get("macro") or {}; mrt=(d.get("macro_raw") or {}).get("мъртви") or []
    bd=[]
    for f in TFS:
        v=(d.get("board") or {}).get(f)
        if not isinstance(v,list) or len(v)<3: continue
        dr,sc=v[0],v[1]
        if dr=="wait": tk="weak"
        else:
            m3=all(mac.values()) if dr=="long" else (not any(mac.values()))
            tk="premium" if m3 else ("strong" if sc>=6 else ("medium" if sc>=4 else "weak"))
            if tk=="premium" and mrt: tk="strong"
        bd.append((f,dr,sc,tk))
    A=[b for b in bd if b[1]!="wait" and b[3]!="weak"]
    if not A: continue
    akt+=1
    best=max(bd,key=lambda x:(rank[x[3]],x[2],бавност.get(x[0],0)))
    bestc[best[3]]+=1
    if rank.get(best[3],0) < 1: falsy+=1          # може ли РЕОФЕР_КЛАС=medium да спре?
    if rank.get(best[3],0) < 2: blok_strong+=1    # би ли спряло при РЕОФЕР_КЛАС=strong?
print(f"ръна с активна дъска: {akt}")
print(f"клас на BEST: {dict(bestc)}")
print(f"пъти, в които `rank(best) >= rank('medium')` е FALSE: {falsy}  ({100*falsy/akt:.2f}%)")
print(f"пъти, в които РЕОФЕР_КЛАС='strong' БИ спрял напомнянето: {blok_strong}  ({100*blok_strong/akt:.2f}%)")
print()
print("Тоест при РЕОФЕР_КЛАС=medium условието е ТЪЖДЕСТВЕНО ИСТИНА —")
print("не защото прагът е нисък, а защото клас под medium е недостижим при посока.")
