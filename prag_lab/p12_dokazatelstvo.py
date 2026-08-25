# -*- coding: utf-8 -*-
"""P12: СТРУКТУРНОТО доказателство, изчерпателно изброено + сверено с лентата.
Проверявам в ДВЕТЕ посоки: (а) при пълните refs прагът 4 е недостижим;
(б) при СЧУПЕН ref (NaN) той СТАВА достижим -> проверчикът може да гръмне."""
import itertools, numpy as np
# --- (а) изчерпателно изброяване на всички възможни състояния при ЖИВИ refs
мин=99; макс=-1; случаи=0; s8_ne_premium=0
for ml in range(4):                                  # брой макро бита ЗА лонг
    for a,b,c in itertools.product([0,1],repeat=3):  # трите ВЗАИМНО ДОПЪЛВАЩИ теста -> lp=x, sp=1-x
        for t4 in (0,1,2):                           # 0=нито едно, 1=lp[3], 2=sp[3]  (взаимно изключващи)
            for l5 in (0,1):
                for s5 in (0,1):                     # lp[4]/sp[4] МОГАТ да са и двете (широк бар)
                    lp=a+b+c+(1 if t4==1 else 0)+l5
                    sp=(1-a)+(1-b)+(1-c)+(1 if t4==2 else 0)+s5
                    ls=ml+lp; ss=(3-ml)+sp
                    if ls==ss: continue              # wait
                    w=max(ls,ss); случаи+=1
                    мин=min(мин,w); макс=max(макс,w)
                    m3 = (ml==3) if ls>ss else (ml==0)
                    if w==8 and not m3: s8_ne_premium+=1
print(f"(а) изброени {случаи} възможни състояния при живи refs:")
print(f"    МИНИМАЛЕН score на победителя = {мин}   (прагът medium>=4 реже 0 от {случаи})")
print(f"    МАКСИМАЛЕН = {макс};  състояния със score=8, които НЕ са premium: {s8_ne_premium}")
# --- (б) обратната посока: изкуствено чупя един ref (NaN => и двата теста дават 0)
мин2=99
for ml in range(4):
    for a,b in itertools.product([0,1],repeat=2):    # само ДВА живи допълващи теста
        for t4 in (0,1,2):
            for l5 in (0,1):
                for s5 in (0,1):
                    lp=a+b+(1 if t4==1 else 0)+l5
                    sp=(1-a)+(1-b)+(1 if t4==2 else 0)+s5
                    ls=ml+lp; ss=(3-ml)+sp
                    if ls==ss: continue
                    мин2=min(мин2,max(ls,ss))
print(f"(б) ОБРАТНА ПОСОКА · с ЕДИН счупен ref: минимален score = {мин2}  "
      f"-> прагът 4 СТАВА достижим, значи изброяването може да гръмне")
# --- сверка с лентата
ls=np.load("prag_lab/_ls.npy").astype(int); ss=np.load("prag_lab/_ss.npy").astype(int)
ml=np.load("prag_lab/_ml.npy").astype(int); ok=np.load("prag_lab/_ok.npy")
a,b,m=ls[ok],ss[ok],ml[ok]
w=np.where(a>b,a,np.where(b>a,b,-1)); dirl=a>b
sel=w>=0
prem=np.where(dirl[sel],m[sel]==3,m[sel]==0)
print(f"\nСВЕРКА С ЛЕНТАТА ({sel.sum():,} клетки с посока):")
print(f"    min={w[sel].min()}  max={w[sel].max()}")
for v in (7,8):
    msk=(w[sel]==v)
    if msk.any():
        print(f"    score={v}: n={int(msk.sum()):,}  от тях premium: {int(prem[msk].sum()):,} "
              f"({100*prem[msk].mean():.1f}%)  -> «strong» при праг {v}: {int((~prem[msk]).sum()):,}")
