# -*- coding: utf-8 -*-
"""ЦЕНАТА НА ОТВАРЯНЕТО НА ВРАТА — мерено, не на усет.
Пуска АНТИ-СПАМ пласта на live_bot върху живия дневник при различни прагове и
брои: КАРТИ (should_sig) и ВХОДОВЕ (should_sig И gate.ok от същия рън)."""
import json, collections, itertools
import pandas as pd
RANK={"premium":3,"strong":2,"medium":1,"weak":0}
TFS=["1мин","5м","15м","30м","1час","4час","1ден"]
L=[json.loads(x) for x in open('live/live_journal.jsonl',encoding='utf-8') ]
L=[r for r in L if isinstance(r.get('board'),dict)]
G=[r for r in L if isinstance(r.get('gate'),dict)]   # само тези имат присъда на гейта

def run(REOFFER_H, MAXAGE, only_gate_runs=False):
    rows = G if only_gate_runs else L
    last={}; cards=0; entries=0
    for r in rows:
        b=[]
        for l in TFS:
            v=(r['board'] or {}).get(l); b.append((l,v[0],v[1],v[2]) if v else (l,"wait",0,"weak"))
        act=[x for x in b if x[1]!="wait" and x[3]!="weak"]
        slow={l:i for i,l in enumerate(TFS)}
        best=max(b,key=lambda x:(RANK[x[3]],x[2],slow[x[0]])) if act else b[0]
        new_dir=best[1] if act else None
        now=r['run_utc']
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
        reoffer=(bool(act) and not trade_open and new_dir is not None
                 and RANK.get(best[3],0)>=1 and mins is not None and mins>=REOFFER_H*60
                 and key_age is not None and key_age<=MAXAGE)
        should=bool(act) and (last.get('key')!=key or tier_up or reoffer) and cool_ok
        if should:
            cards+=1
            if bool((r.get('gate') or {}).get('ok')) and not trade_open: entries+=1
            ks=last.get('key_since') if last.get('key')==key and last.get('key_since') else now
            last={'key':key,'dir':new_dir,'tier':best[3],'sent_utc':now,'key_since':ks}
    return cards,entries

дни=16
print("прагове (REOFFER_H ч, таван възраст ч) → карти / вх. с ДА от гейта   [4344 ръна, 16 делника]")
for rh,ma in [(6,12),(6,24),(6,48),(6,999),(2,12),(2,24),(2,48),(2,999),(1,999),(0.5,999)]:
    c,e=run(rh,ma)
    print(f"  REOFFER_H={rh:<4} таван={ma:<4} → карти {c:4d} ({c/дни:5.2f}/делник)   входа {e:3d} ({e/дни:5.3f}/делник)")
print()
print("ДЕЙСТВИТЕЛНО (живо): карти 57 (3.56/делник), входа 4 (0.250/делник)")
