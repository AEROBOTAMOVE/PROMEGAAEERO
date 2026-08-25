# -*- coding: utf-8 -*-
"""P11: СДВОЕНА разлика в ДОЛАРИ НА ГОДИНА (общ резултат, не на сделка),
блоков бутстрап по ДЕН, едни и същи дни за двете страни."""
import json, numpy as np
T=json.load(open("prag_lab/_trades.json")); P=json.load(open("prag_lab/_picked_all.json"))
NET={int(k):v for k,v in T["net"].items()}; DAY={int(k):v for k,v in T["day"].items()}
ГОД=19.88
ALLD=sorted({DAY[c] for c in NET}); DI={d:i for i,d in enumerate(ALLD)}
def vec(cfg):
    s=np.zeros(len(ALLD)); n=np.zeros(len(ALLD))
    for c in P[cfg]:
        if c in NET: s[DI[DAY[c]]]+=NET[c]; n[DI[DAY[c]]]+=1
    return s,n
rng=np.random.default_rng(20260825); REP=4000
CFG=["3/6","2/6","0/6","3/5","4/5","4/7","4/4","5/6","5/7","6/6","6/7","7/8"]
V={c:vec(c) for c in CFG+["4/6"]}
sb,nb=V["4/6"]
print("СДВОЕНА РАЗЛИКА срещу живото 4/6, в ДОЛАРИ НА ГОДИНА (цялата извадка мащабирана")
print(f"към {ГОД:.2f} години; 95% интервал = блоков бутстрап по ДЕН, 4000 повторения)")
print(f"{'прагове':>9} {'Δ$/год':>9} {'95% интервал':>24} {'Δсделки/год':>12}  присъда")
for c in CFG:
    s,n=V[c]; d=np.empty(REP)
    for r in range(REP):
        p=rng.integers(0,len(ALLD),len(ALLD))
        d[r]=(s[p].sum()-sb[p].sum())/ГОД
    lo,hi=np.percentile(d,[2.5,97.5]); pt=(s.sum()-sb.sum())/ГОД
    dn=(n.sum()-nb.sum())/ГОД
    v="ДОКАЗАНО ПО-ЛОШО" if hi<0 else ("ДОКАЗАНО ПО-ДОБРО" if lo>0 else "НЕ Е ДОКАЗАНО (интервалът пресича 0)")
    print(f"{c:>9} {pt:>+9.0f}  [{lo:>+8.0f} .. {hi:>+8.0f}] {dn:>+12.0f}  {v}")
