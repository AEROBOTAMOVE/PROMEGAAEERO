import pandas as pd, numpy as np
t = pd.read_parquet("f21_dni.parquet")
m = t["mixed"].fillna(False).astype(bool)
print("дни:", len(t), t.index[0], "→", t.index[-1], "| тихи:", int(m.sum()), f"{m.mean()*100:.1f}%")
# епизоди
eps=[]; n=0
for v in m.values:
    if v: n+=1
    elif n: eps.append(n); n=0
if n: eps.append(n)
e=np.array(eps)
print("епизоди:", len(e), "медиана", np.median(e), "p75", np.percentile(e,75), "p90", np.percentile(e,90), "макс", e.max())
# от произволен ТИХ ден: колко остават (вкл. текущия? -> след днешния)
rem=[]
for L in e:
    for i in range(L):
        rem.append(L-i-1)   # оставащи ДНИ след днешния
r=np.array(rem)
print("от произволен тих ден остават: медиана", np.median(r), "| ≤3 дни", f"{(r<=3).mean()*100:.0f}%", "| ≤7", f"{(r<=7).mean()*100:.0f}%", "| ≤14", f"{(r<=14).mean()*100:.0f}%")
print("средно оставащи:", round(r.mean(),1))
