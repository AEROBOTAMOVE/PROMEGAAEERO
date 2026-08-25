# -*- coding: utf-8 -*-
"""P1: разпределение на score-а на 4404 ЖИВИ ръна + сверка, че мога да ВЪЗПРОИЗВЕДА
записания клас от (score, m3, мъртви). Ако не мога — всичко нататък е измислица."""
import json, io, collections, sys

J = "live/live_journal.jsonl"
FR = ["1мин","5м","15м","30м","1час","4час","1ден"]

def tier(score, m3, T_STRONG=6, T_MED=4):
    if m3: return "premium"
    if score >= T_STRONG: return "strong"
    if score >= T_MED: return "medium"
    return "weak"

rows=[]
for line in io.open(J, encoding="utf-8"):
    line=line.strip()
    if not line: continue
    d=json.loads(line)
    rows.append(d)
print("ръна:", len(rows))

# --- 1. сверка: възпроизвеждам ли записания клас?
ok=0; bad=0; badex=[]
cells=0
for d in rows:
    b=d.get("board") or {}
    mac=d.get("macro") or {}
    mrt=(d.get("macro_raw") or {}).get("мъртви") or []
    m3l = bool(mac) and all(mac.values())
    m3s = bool(mac) and (not any(mac.values()))
    for f,v in b.items():
        if not isinstance(v,list) or len(v)<3: continue
        dr,sc,tk = v[0],v[1],v[2]
        cells+=1
        if dr=="wait":
            mine="weak"
        else:
            m3 = m3l if dr=="long" else m3s
            mine = tier(sc, m3)
            if mine=="premium" and mrt: mine="strong"
        if mine==tk: ok+=1
        else:
            bad+=1
            if len(badex)<6: badex.append((d["run_utc"],f,dr,sc,tk,mine,mac,mrt))
print("клетки:",cells,"  съвпадат:",ok,"  разминават:",bad)
for e in badex: print("   РАЗМИНАВАНЕ:",e)

# --- 1б. ОБРАТНА ПОСОКА: нарочно сгрешен праг ТРЯБВА да гръмне
ok2=0;bad2=0
for d in rows:
    b=d.get("board") or {}; mac=d.get("macro") or {}
    mrt=(d.get("macro_raw") or {}).get("мъртви") or []
    m3l=bool(mac) and all(mac.values()); m3s=bool(mac) and not any(mac.values())
    for f,v in b.items():
        if not isinstance(v,list) or len(v)<3: continue
        dr,sc,tk=v[0],v[1],v[2]
        if dr=="wait": mine="weak"
        else:
            m3=m3l if dr=="long" else m3s
            mine=tier(sc,m3,T_STRONG=99,T_MED=99)   # нарочно счупен
            if mine=="premium" and mrt: mine="strong"
        if mine==tk: ok2+=1
        else: bad2+=1
print("ОБРАТНА ПОСОКА (праг 99/99): съвпадат",ok2," разминават",bad2,
      "  <- ТРЯБВА да има много разминавания, иначе проверчикът не може да гръмне")

# --- 2. разпределение на score по рамка
print()
print("РАЗПРЕДЕЛЕНИЕ НА SCORE (всички рамки заедно, само dir!=wait):")
hist=collections.Counter(); histw=collections.Counter()
per_fr=collections.defaultdict(collections.Counter)
for d in rows:
    for f,v in (d.get("board") or {}).items():
        if not isinstance(v,list) or len(v)<3: continue
        dr,sc,tk=v[0],v[1],v[2]
        histw[sc]+=1
        per_fr[f][sc]+=1
        if dr!="wait": hist[sc]+=1
tot=sum(hist.values())
for s in range(0,9):
    n=hist.get(s,0)
    print(f"   score={s}: {n:7d}  {100*n/tot if tot else 0:6.2f}%  {'#'*int(60*n/tot) if tot else ''}")
print("   общо клетки с посока:",tot)
print()
print("по РАМКА (score хистограма):")
for f in FR:
    c=per_fr[f]; t=sum(c.values())
    print("  ",f.ljust(5), " ".join(f"{s}:{c.get(s,0)}" for s in range(0,9)), " N=",t)
