import sys, importlib.util, numpy as np, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')
def mod(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
B7=mod("brain/b_диапазон.py","b7")
rng=np.random.default_rng(7)
n=4000
ix=pd.date_range("2026-06-01", periods=n, freq="5min", tz="UTC")
c=4000+np.cumsum(rng.normal(0,1.2,n))
df=pd.DataFrame({"open":c,"high":c+abs(rng.normal(0,1,n)),"low":c-abs(rng.normal(0,1,n)),
                 "close":c,"volume":abs(rng.normal(100,20,n))}, index=ix)
несъв=0; общо=0; примери=[]
for a in range(1500,n,37):
    r=B7.f_диапазон(df, as_of=a)          # mode по подразбиране = "plus" (както го вика chart_brain)
    общо+=1
    if r["посока"]!=r["съгласие"]["водеща"]:
        несъв+=1; примери.append((a,r["посока"],r["съгласие"]["водеща"]))
print(f"f_диапазон (plus) на {общо} момента: посока ≠ съгласие.водеща в {несъв} случая")
print("примери:",примери[:3])
r=B7.f_диапазон(df, as_of=3000)
print("пример:", {"посока":r["посока"],"водеща":r["съгласие"]["водеща"],
                  "мнозинство":r["съгласие"]["мнозинство"],"единодушно":r["съгласие"]["единодушно"]})
