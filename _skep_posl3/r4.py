# -*- coding: utf-8 -*-
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
os.chdir(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
import pandas as pd, numpy as np

rs = [json.loads(l) for l in open("live/brain_result.jsonl", encoding="utf-8") if l.strip()]
print("### ИСТИНСКАТА ГЕОМЕТРИЯ на 17-те затворени наблюдения (вход/стоп/цел2 от самия дневник)")
gs = []
for r in rs:
    зн = 1 if r["посока"]=="long" else -1
    ds = (float(r["вход"])-float(r["стоп"]))*зн          # >0, разстояние до стоп СРЕЩУ
    d2 = (float(r["цел2"])-float(r["вход"]))*зн if r.get("цел2") is not None else None
    gs.append((r["рамка"], ds, d2))
    print("   %5s посока=%-5s стоп на %.2f$  цел2 на %s$" % (r["рамка"], r["посока"], ds, "None" if d2 is None else round(d2,2)))
D = [(a,b) for _,a,b in gs if b is not None]
print("   стоп: медиана %.2f max %.2f · цел2: медиана %.2f max %.2f"
      % (np.median([a for a,_ in D]), max(a for a,_ in D), np.median([b for _,b in D]), max(b for _,b in D)))

ls = [json.loads(l) for l in open("live/live_journal.jsonl", encoding="utf-8") if l.strip()]
S = sorted((pd.Timestamp(r["run_utc"]), float(r["spot"])) for r in ls if r.get("spot") is not None)
ts = np.array([x[0].value for x in S]); px = np.array([x[1] for x in S]); n=len(px)

def sim(ds, d2, дълго=True):
    """време до затваряне: цената излиза под −ds или над +d2 (за лонг)"""
    out=[]
    for i in range(n):
        lo, hi = px[i]-ds, px[i]+d2
        j=i+1
        while j<n and lo < px[j] < hi:
            j+=1
        out.append((ts[j]-ts[i])/3.6e12 if j<n else None)
    return out

print()
print("### СИМУЛАЦИЯ върху 3281 ЖИВИ спот-точки (02.08–21.08), асиметрична вратичка като истинската")
for ds,d2,етик in ((np.median([a for a,_ in D]), np.median([b for _,b in D]), "медианната истинска геометрия"),
                   (max(a for a,_ in D), max(b for _,b in D), "НАЙ-ШИРОКАТА истинска (max стоп, max цел2)"),
                   (100.0, 200.0, "синтетичната от находката (стоп 100$, цел2 200$)")):
    o=sim(ds,d2); ok=[x for x in o if x is not None]; нет=sum(1 for x in o if x is None)
    print("   стоп −%.2f$ / цел2 +%.2f$  (%s)" % (ds,d2,етик))
    print("      часове: медиана %.2f · p95 %.2f · max %.2f | ≥24ч: %d (%.1f%%) | ≥72ч: %d (%.1f%%) | не се затваря: %d"
          % (np.median(ok), np.percentile(ok,95), max(ok),
             sum(1 for x in ok if x>=24), 100*sum(1 for x in ok if x>=24)/len(o),
             sum(1 for x in ok if x>=72), 100*sum(1 for x in ok if x>=72)/len(o), нет))
