# -*- coding: utf-8 -*-
import json, statistics as st, collections
rows=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
tr=[r for r in rows if isinstance(r.get("saniti"),dict) and r["saniti"].get("разлика") is not None]
rej=[r for r in tr if r.get("spot_rejected")]; ok=[r for r in tr if not r.get("spot_rejected")]
def has(r): return any("базис" in str(n) for n in (r.get("notes") or []))
print("== КОНТРОЛА: бележката за базиса дискриминира ли ==")
print(f"  ОТРЯЗАНИ  n={len(rej):4d}  с бележка за базиса: {sum(map(has,rej)):4d} ({100*sum(map(has,rej))/len(rej):5.1f}%)")
print(f"  ПРИЕТИ    n={len(ok):4d}  с бележка за базиса: {sum(map(has,ok)):4d} ({100*sum(map(has,ok))/len(ok):5.1f}%)")
print()
print("== ЗАЩО се отряза: кой клон на max() е дал допуска ==")
c=collections.Counter()
for r in rej:
    s=r["saniti"]; base=s["база"]; br=s.get("диапазон") or 0; jp=s.get("скок") or 0
    a=base; b=1.8*br; cc=min(1.5*jp, 2.5*br) if jp and br else (2*base if jp else 0)
    win=max((a,"БАЗА 8.00$ (фиксиран под)"),(b,"1.8×диапазон"),(cc,"скок"))[1]
    c[win]+=1
print(" ", c.most_common())
print()
print("== КОЛКО от отрязаните биха МИНАЛИ, ако БАЗАТА беше по-широка ==")
for nb in (8.0,10.0,12.0,15.0,20.0):
    p=sum(1 for r in rej if r["saniti"]["разлика"]<=max(nb, r["saniti"]["допуск"]-r["saniti"]["база"]+nb))
    print(f"  база={nb:5.1f}$ → биха минали {p:3d}/{len(rej)}")
print()
print("== А колко ГЛИЧА би пуснала по-широка база (проверка в ДРУГАТА посока) ==")
d=[r["saniti"]["разлика"] for r in tr]
print(f"  всички следи n={len(d)}: p50={st.median(d):.2f} p95={sorted(d)[int(.95*len(d))]:.2f} max={max(d):.2f}")
print(f"  дял >20$: {sum(1 for x in d if x>20)}/{len(d)}   дял >40$: {sum(1 for x in d if x>40)}/{len(d)}")
