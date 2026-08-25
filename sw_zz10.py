# -*- coding: utf-8 -*-
"""ТЕСТ 5 · Навитият часовник заглушава ли карта, която НЕ е дубликат?
Пуска ИСТИНСКИЯ сканирай върху синтетични барове и сравнява две състояния."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'.')
from brain import chart_brain as CB
np.random.seed(7)
n=1200
idx=pd.date_range('2026-08-01', periods=n, freq='1min')
p=4000+np.cumsum(np.random.randn(n))*1.5
df=pd.DataFrame({'open':p,'high':p+abs(np.random.randn(n)),'low':p-abs(np.random.randn(n)),
                 'close':p+np.random.randn(n)*0.3,'volume':np.random.randint(50,500,n)},index=idx)
frames={'1мин':df,'5м':df.resample('5min').agg(open=('open','first'),high=('high','max'),
        low=('low','min'),close=('close','last'),volume=('volume','sum')).dropna()}
s=CB.сканирай(frames, сега=None, работни=('1мин','5м'), праг=1, състояние={})
print('сетъпи:', len(s))
if s:
    a=s[0]
    print('първи:', a['рамка'], a['посока'], 'ранг', a['ранг'], 'точки', a['точки'], 'време', a['време'], 'праща', a['праща'])
    ключ=f"{a['рамка']}|{a['посока']}"
    # състояние: часовник навит ПРЕДИ 1 минута със СЪЩИЯ ранг
    import datetime as dt
    предх=str(pd.Timestamp(a['време'])-pd.Timedelta(minutes=1))
    for етикет, ранг_стар in (('РАВЕН ранг', a['ранг']), ('ПО-НИСЪК ранг (картата е по-силна)', a['ранг']-1)):
        st={ключ:{'ранг':ранг_стар,'точки':1,'време':предх}}
        r=CB.сканирай(frames, сега=None, работни=('1мин','5м'), праг=1, състояние=st)
        m=[x for x in r if f"{x['рамка']}|{x['посока']}"==ключ][0]
        print(f"  {етикет:38s} → праща={m['праща']}  застудяване={m.get('застудяване')}")
