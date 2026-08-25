# -*- coding: utf-8 -*-
"""P8: пари + 95% интервал от БЛОКОВ БУТСТРАП ПО ДЕН (П2 на одита: 6.4 сделки
текат едновременно, независимите интервали са 1.7-1.9x по-тесни от истината)."""
import json, numpy as np
T=json.load(open("prag_lab/_trades.json"))
NET={int(k):v for k,v in T["net"].items()}; DAY={int(k):v for k,v in T["day"].items()}
P=json.load(open("prag_lab/_picked_all.json"))
rng=np.random.default_rng(20260825)
REP=4000

def dneven(cfg):
    cps=[c for c in P[cfg] if c in NET]
    d={}
    for c in cps: d.setdefault(DAY[c],[]).append(NET[c])
    return d, cps

ALLDAYS=sorted({DAY[c] for c in NET})
DIDX={d:i for i,d in enumerate(ALLDAYS)}

def boot_matrix(cfgs):
    """една и съща извадка от ДНИ за всички конфигурации -> сдвоена разлика"""
    per={}
    for c in cfgs:
        d,_=dneven(c)
        s=np.zeros(len(ALLDAYS)); n=np.zeros(len(ALLDAYS))
        for k,v in d.items():
            s[DIDX[k]]=sum(v); n[DIDX[k]]=len(v)
        per[c]=(s,n)
    out={c:np.empty(REP) for c in cfgs}
    for r in range(REP):
        pick=rng.integers(0,len(ALLDAYS),len(ALLDAYS))
        for c in cfgs:
            s,n=per[c]
            nn=n[pick].sum()
            out[c][r]= s[pick].sum()/nn if nn>0 else np.nan
    return out

CFG=["4/6","3/5","5/7","3/6","5/6","6/6","4/5","4/7","4/4","6/7","7/8","0/6"]
BM=boot_matrix(CFG)
print("ДОСТАВЕНАТА ГЕОМЕТРИЯ (стълба 7.5/12/20, СЛ 20, БЕ след ТП1), net вкл. слип 0.02$")
print(f"{'прагове':>9} {'сделки':>7} {'$/сделка':>9} {'95% интервал (блок по ДЕН)':>30} {'общо $':>11}  {'дълги$':>8} {'къси$':>8}")
base=None
for c in CFG:
    cps=[x for x in P[c] if x in NET]
    net=np.array([NET[x] for x in cps])
    dirs=np.array([T["dir"][str(x)] for x in cps])
    lo,hi=np.nanpercentile(BM[c],[2.5,97.5])
    L=net[dirs==1].mean() if (dirs==1).any() else float('nan')
    S=net[dirs==-1].mean() if (dirs==-1).any() else float('nan')
    mark="  <== ЖИВОТО" if c=="4/6" else ""
    print(f"{c:>9} {len(net):>7,} {net.mean():>+9.4f}   [{lo:>+7.4f} .. {hi:>+7.4f}]  {net.sum():>+11.0f}  {L:>+8.3f} {S:>+8.3f}{mark}")
print()
print("СДВОЕНА РАЗЛИКА срещу живото 4/6 (едни и същи бутстрап-дни за двете страни):")
print(f"{'прагове':>9} {'Δ$/сделка':>10} {'95% интервал':>26}  {'Δсделки':>8}  присъда")
for c in CFG:
    if c=="4/6": continue
    d=BM[c]-BM["4/6"]
    lo,hi=np.nanpercentile(d,[2.5,97.5]); pt=np.nanmean(d)
    n_c=len([x for x in P[c] if x in NET]); n_b=len([x for x in P["4/6"] if x in NET])
    v = "ДОКАЗАНО ПО-ДОБРО" if lo>0 else ("ДОКАЗАНО ПО-ЛОШО" if hi<0 else "интервалът пресича 0 - не е доказано")
    print(f"{c:>9} {pt:>+10.4f}   [{lo:>+7.4f} .. {hi:>+7.4f}]  {n_c-n_b:>+8}  {v}")
print()
print("ПРЕДЕЛНИТЕ ВХОДОВЕ (какво точно добавя/маха всяко местене):")
def marg(a,b,ime):
    A=set(x for x in P[a] if x in NET); Bs=set(x for x in P[b] if x in NET)
    for етик,ss in ((f"САМО в {a}",A-Bs),(f"САМО в {b}",Bs-A),(f"ОБЩИ",A&Bs)):
        if not ss: print(f"   {ime} · {етик:<14} n=0"); continue
        v=np.array([NET[x] for x in ss])
        # интервал по ден за подмножеството
        dd={}
        for x in ss: dd.setdefault(DAY[x],[]).append(NET[x])
        ks=list(dd); arr=[np.array(dd[k]) for k in ks]
        bs=np.empty(2000)
        for r in range(2000):
            p=rng.integers(0,len(ks),len(ks))
            cat=np.concatenate([arr[i] for i in p]); bs[r]=cat.mean()
        lo,hi=np.percentile(bs,[2.5,97.5])
        print(f"   {ime} · {етик:<14} n={len(v):>5}  {v.mean():>+8.4f}$  [{lo:>+7.4f} .. {hi:>+7.4f}]  общо {v.sum():>+8.0f}$")
marg("4/6","5/6","T_MED 4->5")
marg("4/6","4/7","T_STRONG 6->7")
marg("4/6","4/5","T_STRONG 6->5")
marg("4/6","5/7","4/6 -> 5/7")
