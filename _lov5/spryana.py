# -*- coding: utf-8 -*-
"""Колко пъти v15.1 БИ пратила картата «спряна:» — без нито един ограничител."""
import json, collections
import pandas as pd
RANK={"premium":3,"strong":2,"medium":1,"weak":0}
TFS=["1мин","5м","15м","30м","1час","4час","1ден"]
REOFFER_H=6; MAXAGE=12
L=[json.loads(x) for x in open('live/live_journal.jsonl',encoding='utf-8')]
L=[r for r in L if isinstance(r.get('board'),dict)]
last={}; n_card=0; n_run=0; per=collections.Counter(); prichini=collections.Counter()
for r in L:
    b=[]
    for l in TFS:
        v=(r['board'] or {}).get(l); b.append((l,v[0],v[1],v[2]) if v else (l,"wait",0,"weak"))
    act=[x for x in b if x[1]!="wait" and x[3]!="weak"]
    slow={l:i for i,l in enumerate(TFS)}
    best=max(b,key=lambda x:(RANK[x[3]],x[2],slow[x[0]])) if act else b[0]
    new_dir=best[1] if act else None
    now=r['run_utc']; n_run+=1
    if not act and last.get('key'): last.pop('key',None)
    отч=sorted({f"{d}:{t}" for _l,d,_s,t in b if t!="weak" and d!="wait"})
    key=f"{len(отч)}|"+";".join(отч)
    mins=None
    if last.get('sent_utc'): mins=(pd.Timestamp(now)-pd.Timestamp(last['sent_utc'])).total_seconds()/60
    tier_up=bool(new_dir) and RANK.get(best[3],0)>RANK.get(last.get('tier','weak'),0) and new_dir==last.get('dir')
    cool_ok=(mins is None or mins>=45 or (new_dir is not None and new_dir!=last.get('dir') and mins>=15) or tier_up)
    key_age=None
    if last.get('key')==key and last.get('key_since'):
        key_age=(pd.Timestamp(now)-pd.Timestamp(last['key_since'])).total_seconds()/3600
    trade_open=r.get('trade') is not None
    reoffer=(bool(act) and not trade_open and new_dir is not None and RANK.get(best[3],0)>=1
             and mins is not None and mins>=REOFFER_H*60 and key_age is not None and key_age<=MAXAGE)
    should=bool(act) and (last.get('key')!=key or tier_up or reoffer) and cool_ok
    # блокът live_bot.py:4003-4013
    spryan=None
    if act and new_dir and not should and not trade_open:
        if key_age is not None and key_age>MAXAGE: spryan='сетъпът е стар (>12ч)'
        elif mins is not None and mins<REOFFER_H*60: spryan='<6ч от последната карта'
        elif last.get('key')==key: spryan='същият сетъп'
    if spryan:
        n_card+=1; per[r['date']]+=1; prichini[spryan]+=1
    if should:
        ks=last.get('key_since') if last.get('key')==key and last.get('key_since') else now
        last={'key':key,'dir':new_dir,'tier':best[3],'sent_utc':now,'key_since':ks}
print(f"ръна: {n_run}")
print(f"ръна, в които v15.1 БИ построила и пратила «спряна:» карта: {n_card} = {100*n_card/n_run:.1f}%")
print("по причини:", dict(prichini))
print("на ден (топ 8):", per.most_common(8))
print()
print("СРАВНЕНИЕ: реално пратени «спряна:» карти в целия sent_log = 1")
