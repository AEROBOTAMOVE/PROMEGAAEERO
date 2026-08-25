# -*- coding: utf-8 -*-
"""ЛОВ 5 · РЕПЛЕЙ на анти-спам пласта върху ЖИВИЯ дневник.
Не чете код — ИЗПЪЛНЯВА същата логика (live_bot.py:3931-4013) с живите числа.
Състоянието last_sent се пресъздава от РЕАЛНИТЕ пращания (status 'signal=SENT')."""
import json, collections, sys
import pandas as pd

REOFFER_H = 6
REOFFER_MAX_AGE_H = 12
STANDING_H = 2
RANK = {"premium":3,"strong":2,"medium":1,"weak":0}
РЕОФЕР_КЛАС = "medium"
TFS = ["1мин","5м","15м","30м","1час","4час","1ден"]

L=[json.loads(x) for x in open('live/live_journal.jsonl',encoding='utf-8')]
L=[r for r in L if isinstance(r.get('board'),dict)]

def board_of(r):
    b=[]
    for lbl in TFS:
        v=(r['board'] or {}).get(lbl)
        if not v: b.append((lbl,"wait",0,"weak")); continue
        b.append((lbl,v[0],v[1],v[2]))
    return b

def sofia_hour(iso):
    return (pd.Timestamp(iso, tz='UTC').tz_convert('Europe/Sofia')).hour

start = sys.argv[1] if len(sys.argv)>1 else "0000"
rows=L
last={}
cnt=collections.Counter(); tot=0
for r in rows:
    b=board_of(r)
    act=[x for x in b if x[1]!="wait" and x[3]!="weak"]
    slow={l:i for i,l in enumerate(TFS)}
    best=max(b,key=lambda x:(RANK[x[3]],x[2],slow[x[0]])) if act else b[0]
    new_dir=best[1] if act else None
    now=r['run_utc']
    if not act and last.get('key'): last.pop('key',None)
    отч=sorted({f"{d}:{t}" for _l,d,_s,t in b if t!="weak" and d!="wait"})
    key=f"{len(отч)}|"+";".join(отч)
    mins=None
    if last.get('sent_utc'):
        mins=(pd.Timestamp(now)-pd.Timestamp(last['sent_utc'])).total_seconds()/60
    tier_up = bool(new_dir) and RANK.get(best[3],0)>RANK.get(last.get('tier','weak'),0) and new_dir==last.get('dir')
    cool_ok = (mins is None or mins>=45 or (new_dir is not None and new_dir!=last.get('dir') and mins>=15) or tier_up)
    key_age=None
    if last.get('key')==key and last.get('key_since'):
        key_age=(pd.Timestamp(now)-pd.Timestamp(last['key_since'])).total_seconds()/3600
    trade_open = r.get('trade') is not None
    reoffer = (bool(act) and not trade_open and new_dir is not None
               and RANK.get(best[3],0)>=RANK.get(РЕОФЕР_КЛАС,1)
               and mins is not None and mins>=REOFFER_H*60
               and key_age is not None and key_age<=REOFFER_MAX_AGE_H
               and 0<=sofia_hour(now)<=23)
    should = bool(act) and (last.get('key')!=key or tier_up or reoffer) and cool_ok
    gate_ok = bool((r.get('gate') or {}).get('ok'))
    # коя врата е БИНДИНГ (първата, която затваря)
    if not act: door='0 · дъската е weak/wait (actionable=[])'
    elif not should:
        if last.get('key')==key and key_age is not None and key_age>REOFFER_MAX_AGE_H: door='1 · сетъпът >12ч (REOFFER_MAX_AGE_H)'
        elif last.get('key')==key and mins is not None and mins<REOFFER_H*60: door='2 · <6ч от последната карта (REOFFER_H)'
        elif last.get('key')==key and trade_open: door='3 · отворена сделка блокира reoffer'
        elif not cool_ok: door='4 · 45-мин пауза'
        elif last.get('key')==key: door='5 · същият ключ, друго'
        else: door='6 · друго'
    elif not gate_ok: door='7 · КАРТА ДА, но гейтът НЕ → инфо-карта, БЕЗ вход'
    else: door='8 · ВХОД (карта+гейт)'
    if now>=start:
        tot+=1; cnt[door]+=1
    # обнови last само ако РЕАЛНО е пратен сигнал
    if any(s.startswith('signal=SENT') for s in (r.get('status') or [])):
        ks = last.get('key_since') if last.get('key')==key and last.get('key_since') else now
        last={'key':key,'dir':new_dir,'tier':best[3],'sent_utc':now,'key_since':ks}
print(f"ръна: {tot}  (прозорец от {start})")
for k in sorted(cnt): print(f"  {cnt[k]:5d}  {100*cnt[k]/tot:5.1f}%  {k}")
