# -*- coding: utf-8 -*-
"""P3: РАЗДЕЛЕН свип. Мърдам САМО единия праг наведнъж и сравнявам
ПОСЛЕДОВАТЕЛНОСТТА ОТ КЛЮЧОВЕ буква по буква срещу живото (4/6)."""
import json, io, collections
rows=[json.loads(l) for l in io.open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]

def keys_seq(TM,TS):
    seq=[]; tiers=collections.Counter()
    for d in rows:
        mac=d.get("macro") or {}; mrt=(d.get("macro_raw") or {}).get("мъртви") or []
        m3l=bool(mac) and all(mac.values()); m3s=bool(mac) and not any(mac.values())
        o=set()
        for f,v in (d.get("board") or {}).items():
            if not isinstance(v,list) or len(v)<3: continue
            dr,sc=v[0],v[1]
            if dr=="wait": tk="weak"
            else:
                m3=m3l if dr=="long" else m3s
                tk="premium" if m3 else ("strong" if sc>=TS else ("medium" if sc>=TM else "weak"))
                if tk=="premium" and mrt: tk="strong"
            tiers[tk]+=1
            if tk!="weak": o.add(f"{dr}:{tk}")
        oo=sorted(o); seq.append((f"{len(oo)}|"+";".join(oo)) if oo else "")
    return seq,tiers

def smeni(seq):
    n=0
    for i in range(1,len(seq)):
        if seq[i]!=seq[i-1]: n+=1
    return n

base,btier=keys_seq(4,6)
print(f"БАЗА живото 4/6: смени={smeni(base)} различни={len(set(base))} активни={sum(1 for k in base if k)}")
print()
print("A) СВИП НА T_MEDIUM, T_STRONG=6 ЗАКОВАН:")
print(f"{'TM':>4} {'смени':>6} {'активни ръна':>13} {'клетки medium':>14} {'клетки weak':>12}  {'ключове != база':>16}")
for TM in range(0,8):
    s,t=keys_seq(TM,6)
    diff=sum(1 for a,b in zip(s,base) if a!=b)
    print(f"{TM:>4} {smeni(s):>6} {sum(1 for k in s if k):>13} {t['medium']:>14} {t['weak']:>12}  {diff:>16}"
          + ("   <== ЖИВОТО" if TM==4 else ("   ← НУЛЕВА РАЗЛИКА" if diff==0 and TM!=4 else "")))
print()
print("Б) СВИП НА T_STRONG, T_MEDIUM=4 ЗАКОВАН:")
print(f"{'TS':>4} {'смени':>6} {'активни ръна':>13} {'клетки strong':>14} {'клетки medium':>14}  {'ключове != база':>16}")
for TS in range(4,10):
    s,t=keys_seq(4,TS)
    diff=sum(1 for a,b in zip(s,base) if a!=b)
    print(f"{TS:>4} {smeni(s):>6} {sum(1 for k in s if k):>13} {t['strong']:>14} {t['medium']:>14}  {diff:>16}"
          + ("   <== ЖИВОТО" if TS==6 else ""))
print()
print("В) КОИ СА 8-те ключа при живото и колко ръна стои всеки:")
c=collections.Counter(base)
for k,v in c.most_common():
    print(f"   {v:>5}  {k!r}")
