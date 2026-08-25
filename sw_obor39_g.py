# -*- coding: utf-8 -*-
import json, collections, statistics as st
rows=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
san=[(i,r,r["saniti"]) for i,r in enumerate(rows)
     if r.get("spot_rejected") and isinstance(r.get("saniti"),dict) and r["saniti"].get("разлика") is not None]
print("== РАЗПРЕДЕЛЕНИЕ на отрязаните (n=%d) ==" % len(san))
d=[s["разлика"] for i,r,s in san]; t=[s["допуск"] for i,r,s in san]
rng=[s["диапазон"] for i,r,s in san if s.get("диапазон")]
print("  разлика: медиана %.2f p90 %.2f max %.2f" % (st.median(d), sorted(d)[int(.9*len(d))], max(d)))
print("  допуск : медиана %.2f  дял с допуск==база(8.0): %d/%d" % (st.median(t), sum(1 for x in t if abs(x-8.0)<1e-9), len(t)))
print("  диапазон(1мин, 5 бара): медиана %.2f p90 %.2f" % (st.median(rng), sorted(rng)[int(.9*len(rng))]))
print("  дял разлика>3x допуск (=глич-мащаб): %d/%d" % (sum(1 for x,y in zip(d,t) if x>3*y), len(d)))
print()
print("== BASIS: чист ли е референтът ==")
bad=sum(1 for i,r,s in san if any("базис" in str(n) for n in (r.get("notes") or [])))
print("  отрязани ръна с бележка за БАЗИСА:", bad, "/", len(san))
b_rej=[abs(r.get("basis") or 0) for i,r,s in san]
b_ok=[abs(r.get("basis") or 0) for r in rows if not r.get("spot_rejected") and r.get("spot")]
print("  |базис| медиана: отрязани %.2f  срещу приети %.2f" % (st.median(b_rej), st.median(b_ok)))
print()
print("== ПЕРСИСТЕНТНОСТ: единичен глич или траен разрив ==")
idx={i for i,r,s in san}
runs=[];cur=0
for i in range(len(rows)):
    if i in idx: cur+=1
    elif cur: runs.append(cur);cur=0
if cur: runs.append(cur)
print("  серии:", collections.Counter(runs).most_common())
print("  дял ЕДИНИЧНИ отрязвания:", sum(1 for x in runs if x==1), "от", len(runs), "серии")
print()
print("== ЗНАКОВ ТЕСТ: барът движи ли се КЪМ отхвърления спот ==")
# знакът се възстановява от НАЙ-БЛИЗКИЯ приет спот в следващите 3 ръна
към=0; от_него=0; неопр=0
for i,r,s in san:
    ref=(r.get("bar") or 0)-(r.get("basis") or 0)
    nxt=next((rows[j] for j in range(i+1,min(i+4,len(rows))) if rows[j].get("spot")), None)
    if not nxt: неопр+=1; continue
    sp_hi=ref+s["разлика"]; sp_lo=ref-s["разлика"]
    sp=sp_hi if abs(sp_hi-nxt["spot"])<abs(sp_lo-nxt["spot"]) else sp_lo
    j=min(i+2,len(rows)-1)
    b0=r.get("bar"); b1=rows[j].get("bar")
    if b0 is None or b1 is None: неопр+=1; continue
    dv=(b1-b0)*(1 if sp>ref else -1)
    if dv>0: към+=1
    elif dv<0: от_него+=1
    else: неопр+=1
print(f"  барът тръгна КЪМ отхвърлената цена: {към} | ОБРАТНО: {от_него} | неопределено: {неопр}")
