# -*- coding: utf-8 -*-
import json, statistics as st
rows=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
def тест(sel, име, използвай_истински=False):
    към=от=неопр=0; амп=[]; точни=0; общо=0
    for i,r in enumerate(rows):
        s=r.get("saniti")
        if not (isinstance(s,dict) and s.get("разлика") is not None): continue
        if not sel(r): continue
        ref=(r.get("bar") or 0)-(r.get("basis") or 0)
        prev=next((rows[j] for j in range(i-1,max(i-4,-1),-1) if rows[j].get("spot")), None)
        if not prev or not s.get("скок"): неопр+=1; continue
        p=prev["spot"]; k=s["скок"]
        good=[x for x in (p+k,p-k) if abs(abs(ref-x)-s["разлика"])<0.35]
        if len(good)!=1: неопр+=1; continue
        sp=good[0]
        if r.get("spot") is not None:                 # проверка на самата реконструкция
            общо+=1; точни+= abs(sp-r["spot"])<0.35
        if използвай_истински and r.get("spot") is not None: sp=r["spot"]
        j=min(i+2,len(rows)-1); b0=r.get("bar"); b1=rows[j].get("bar")
        if b0 is None or b1 is None: неопр+=1; continue
        dv=(b1-b0)*(1 if sp>ref else -1); амп.append(dv)
        към+= dv>0; от+= dv<0
    acc=f" | реконструкцията вярна {точни}/{общо}" if общо else ""
    print(f"  {име:38} n={към+от:4d}  КЪМ={към:4d} ОБРАТНО={от:4d} "
          f"({100*към/max(към+от,1):5.1f}%) медиана={st.median(амп) if амп else 0:+6.2f}${acc}")
print("== НЕГАТИВНА КОНТРОЛА на знаковия тест ==")
тест(lambda r: r.get("spot_rejected"), "ОТРЯЗАНИ (възстановен знак)")
тест(lambda r: not r.get("spot_rejected"), "ПРИЕТИ (възстановен знак)")
тест(lambda r: not r.get("spot_rejected"), "ПРИЕТИ (ИСТИНСКИЯТ спот)", True)
print()
print("== същото, но контролата ограничена до сходен разрив (>=4$) ==")
тест(lambda r: (not r.get("spot_rejected")) and r["saniti"]["разлика"]>=4.0, "ПРИЕТИ разрив>=4$ (истински спот)", True)
