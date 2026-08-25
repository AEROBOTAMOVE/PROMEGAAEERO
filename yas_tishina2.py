# -*- coding: utf-8 -*-
import sys, numpy as np, pandas as pd
sys.argv=["x"]
d = pd.read_parquet("f21_dni.parquet")
d = d[d["d20"].notna() & d["r20"].notna()].copy()
print("валидни дни:", len(d), d.index.min().date(), "..", d.index.max().date())
m = d["mixed"].astype(bool).values
print("mixed дни: %d = %.1f%%   подредени: %.1f%%" % (m.sum(), 100*m.mean(), 100*(~m).mean()))
# серии
def серии(v, стойност):
    out=[]; n=0
    for x in v:
        if x==стойност: n+=1
        else:
            if n: out.append(n)
            n=0
    if n: out.append(n)
    return np.array(out)
sm = серии(m, True)
sp = серии(m, False)
print("\nТИХИ (mixed) епизоди: брой=%d  медиана=%.0f  средно=%.1f  макс=%d" % (len(sm), np.median(sm), sm.mean(), sm.max()))
for q in (50,75,90,95,99):
    print("   p%d = %.0f дни" % (q, np.percentile(sm,q)))
print("   дял епизоди <=2 дни: %.0f%%   <=5: %.0f%%   >10: %.0f%%" % (100*(sm<=2).mean(),100*(sm<=5).mean(),100*(sm>10).mean()))
print("\nПОДРЕДЕНИ епизоди: брой=%d медиана=%.0f макс=%d" % (len(sp), np.median(sp), sp.max()))
# вероятност: при mixed днес, колко често подрежда до утре / до 3 дни / до 7
import collections
изх=[]
for i in range(len(m)):
    if not m[i]: continue
    # колко дни до първия подреден
    j=i
    while j<len(m) and m[j]: j+=1
    изх.append(j-i)   # дни ОСТАВАЩИ от този ден нататък
изх=np.array(изх)
print("\nОТ ПРОИЗВОЛЕН ТИХ ДЕН колко още остава:")
for k in (1,2,3,5,7,14):
    print("   подрежда до %2d дни: %.0f%%" % (k, 100*(изх<=k).mean()))
print("   медиана оставащи: %.0f дни" % np.median(изх))
