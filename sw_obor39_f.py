# -*- coding: utf-8 -*-
import json, collections, statistics as st
rows=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
print("ръна с ОТВОРЕНА сделка изобщо:", sum(1 for r in rows if r.get("trade")),
      "| от тях с отрязан спот:", sum(1 for r in rows if r.get("trade") and r.get("spot_rejected")))
print("saniti пример:", next((r["saniti"] for r in reversed(rows) if r.get("saniti")), None))
print()
print("== spot_src при ОТРЯЗАН спот (кой фийд е дал числото) ==")
c=collections.Counter(r.get("spot_src") for r in rows if r.get("spot_rejected"))
print(" ", c.most_common())
print("== spot_src при ПРИЕТ спот ==")
c2=collections.Counter(r.get("spot_src") for r in rows if not r.get("spot_rejected") and r.get("spot"))
print(" ", c2.most_common())
print()
print("== РЕШАВАЩ ТЕСТ: ако живата цена е била ПРАВА, барът трябва да я ДОГОНИ ==")
# за всеки отрязан рън със следа: разлика D. Сравняваме с |bar(+k) - bar(0)|
san=[]
for i,r in enumerate(rows):
    s=r.get("saniti")
    if r.get("spot_rejected") and isinstance(s,dict) and s.get("разлика") is not None:
        san.append((i,r,s))
print("отрязани СЪС следа:", len(san))
for k in (1,2,3,6):
    D=[];M=[]
    for i,r,s in san:
        if i+k>=len(rows): continue
        b0=r.get("bar"); b1=rows[i+k].get("bar")
        if b0 is None or b1 is None: continue
        D.append(float(s["разлика"])); M.append(abs(float(b1)-float(b0)))
    if not D: continue
    догонил=sum(1 for d,m in zip(D,M) if m>=0.5*d)
    print(f"  след {k} рън(а) (n={len(D)}): медиана разлика={st.median(D):6.2f}$ "
          f"медиана движение на бара={st.median(M):6.2f}$ "
          f"| барът покрива >=50% от разликата в {догонил}/{len(D)} ({100*догонил/len(D):.0f}%)")
print()
print("== СЪЩОТО за ПРИЕТИТЕ (контрола) ==")
ok=[(i,r,r["saniti"]) for i,r in enumerate(rows) if not r.get("spot_rejected") and isinstance(r.get("saniti"),dict) and r["saniti"].get("разлика") is not None]
print("приети СЪС следа:", len(ok))
for k in (1,3):
    D=[];M=[]
    for i,r,s in ok:
        if i+k>=len(rows): continue
        b0=r.get("bar"); b1=rows[i+k].get("bar")
        if b0 is None or b1 is None: continue
        D.append(float(s["разлика"])); M.append(abs(float(b1)-float(b0)))
    if D: print(f"  след {k}: медиана разлика={st.median(D):6.2f}$ движение на бара={st.median(M):6.2f}$")
