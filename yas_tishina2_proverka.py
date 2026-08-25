import pandas as pd, numpy as np
t = pd.read_parquet("f21_dni.parquet")
m = t["mixed"].fillna(False).astype(bool)
eps=[]; n=0
for v in m.values:
    if v: n+=1
    elif n: eps.append(n); n=0
if n: eps.append(n)
e=np.array(eps)
rem=[]  # ВКЛЮЧИТЕЛНО днешния: колко дни още ще е тихо, броейки днес
for L in e:
    for i in range(L):
        rem.append(L-i)
r=np.array(rem)
for k in (1,2,3,4,5,7,10,14):
    print(f"свършва до {k} дни (вкл. днес): {(r<=k).mean()*100:.0f}%")
print("медиана вкл. днес:", np.median(r), "средно", round(r.mean(),1))
