import sys, importlib.util, numpy as np, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')
def mod(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
CB=mod("brain/chart_brain.py","cb")
print("ПРОЗОРЕЦ =",CB.ПРОЗОРЕЦ,"| МИН_БАРОВЕ =",CB.МИН_БАРОВЕ)
B6=mod("brain/b_обеми.py","b6")
print("прагове дни_профил/мин_дни:", B6.ПРАГОВЕ["дни_профил"], B6.ПРАГОВЕ["мин_дни"])
rng=np.random.default_rng(3)
for име,мин in (("1мин",1),("5м",5),("15м",15),("1час",60)):
    n=CB.ПРОЗОРЕЦ
    ix=pd.date_range("2026-08-01", periods=n, freq=f"{мин}min", tz="UTC")
    c=4000+np.cumsum(rng.normal(0,0.5,n))
    d=pd.DataFrame({"open":c,"high":c+1,"low":c-1,"close":c,
                    "volume":np.abs(rng.normal(500,150,n))}, index=ix)
    d.loc[d.index[-1],"volume"]=100000.0     # ОГРОМЕН обем на последния бар
    отн=B6.f_относителен_обем(d)
    o=отн.get("отн")
    сега=float(o[-1]) if o is not None and len(o) else float("nan")
    ск=B6.f_обемен_скок(d)
    покрити=(ix[-1]-ix[0]).total_seconds()/86400
    print(f"{име:5s} прозорец {n} бара = {покрити:5.2f} дни · отн_сега={сега} "
          f"· J1(≥1.5)={np.isfinite(сега) and сега>=1.5} · J1b(≥2.5)={np.isfinite(сега) and сега>=2.5}"
          f" · последен_скок={'има' if ск.get('последен') else 'НЯМА'}")
