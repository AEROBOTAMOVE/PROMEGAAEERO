# -*- coding: utf-8 -*-
"""СКЕПТИК S3: реплей на ЦЕЛИЯ жив дневник с ДНЕШНАТА формула за ключ (ОДИТ-67).
Въпросът: заключва ли се вратата и с ТЕКУЩИЯ код, и КОЛКО СТРУВА това."""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0,".")
import pandas as pd
import live_bot as LB

rank={"premium":3,"strong":2,"medium":1,"weak":0}
_бавност={l:i for i,(l,*_) in enumerate(LB.TFS)}
recs=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]

def прогон(старключ=False, отваряй_сделки=False):
    last={}; ред=[]
    сделка=None
    for r in recs:
        now=r["run_utc"]; bd=r.get("board") or {}
        board=[(l,v[0],v[1],v[2],"") for l,v in bd.items()]
        if not board: continue
        actionable=[b for b in board if b[1]!="wait" and b[3]!="weak"]
        best=max(board,key=lambda x:(rank[x[3]],x[2],_бавност.get(x[0],0))) if actionable else board[0]
        new_dir=best[1] if actionable else None
        if старключ:   # СТАРАТА формула: по един запис на РАМКА (копия) — за сравнение
            key="|".join(f"{l}:{d}:{t}" for l,d,_s,t,_ in board)
        else:
            _отч=sorted({f"{d}:{t}" for _l,d,_s,t,_ in board if t!="weak" and d!="wait"})
            key=f"{len(_отч)}|"+";".join(_отч)
        if not actionable and last.get("key"):
            last={k:v for k,v in last.items() if k!="key"}
        mins_since=None
        if last.get("sent_utc"):
            mins_since=(pd.Timestamp(now)-pd.Timestamp(last["sent_utc"])).total_seconds()/60
        tier_up=bool(new_dir and rank.get(best[3],0)>rank.get(last.get("tier","weak"),0) and new_dir==last.get("dir"))
        cool_ok=(mins_since is None or mins_since>=45
                 or (new_dir is not None and new_dir!=last.get("dir") and mins_since>=15) or tier_up)
        key_age_h=None
        if last.get("key")==key and last.get("key_since"):
            key_age_h=(pd.Timestamp(now)-pd.Timestamp(last["key_since"])).total_seconds()/3600
        reoffer=(bool(actionable) and сделка is None and new_dir is not None
                 and rank.get(best[3],0)>=rank.get(LB.РЕОФЕР_КЛАС,1)
                 and mins_since is not None and mins_since>=LB.REOFFER_H*60
                 and key_age_h is not None and key_age_h<=LB.REOFFER_MAX_AGE_H
                 and LB._reoffer_hour_ok(now))
        should=bool(actionable) and (last.get("key")!=key or tier_up or reoffer) and cool_ok
        причина=None
        if should and not (last.get("key")!=key or tier_up):
            причина="reoffer"
        elif should: причина="нов ключ/tier"
        weekend=LB._market_closed(now)
        спрян=None
        if should and weekend: should=False; спрян="уикенд"
        if should and new_dir=="short" and r.get("shield") and сделка is None: should=False; спрян="US-щит"
        gate=r.get("gate") or {}
        gok=bool(gate.get("ok"))
        # защо НЕ should, при жив сетъп
        блокер=None
        if actionable and not should and спрян is None:
            if last.get("key")==key and not tier_up:
                if key_age_h is not None and key_age_h>LB.REOFFER_MAX_AGE_H: блокер="ВЪЗРАСТ>12ч"
                elif not cool_ok: блокер="45-мин пауза"
                elif mins_since is not None and mins_since<LB.REOFFER_H*60: блокер="<6ч от карта"
                elif not LB._reoffer_hour_ok(now): блокер="нощен час"
                elif key_age_h is None: блокер="няма key_since"
                else: блокер="друго"
            elif not cool_ok: блокер="45-мин пауза"
            else: блокер="друго"
        ред.append(dict(utc=now,act=bool(actionable),key=key,key_age=key_age_h,should=should,
                        блокер=блокер,спрян=спрян,gok=gok,gate_by=gate.get("by"),
                        dir=new_dir,tier=best[3],причина=причина,weekend=weekend))
        if should:
            ks=last.get("key_since") if last.get("key")==key and last.get("key_since") else now
            last={"key":key,"dir":new_dir,"tier":best[3],"sent_utc":now,"key_since":ks}
            if отваряй_сделки and gok: сделка={"dir":new_dir,"opened":now}
    return ред

for етикет,ск in [("НОВА формула (ОДИТ-67, днешният код)",False),("СТАРА формула (по рамки)",True)]:
    ред=прогон(старключ=ск)
    n=len(ред)
    act=[x for x in ред if x["act"]]
    вз=[x for x in act if x["блокер"]=="ВЪЗРАСТ>12ч"]
    скъпи=[x for x in вз if x["gok"]]
    карти=[x for x in ред if x["should"]]
    print(f"\n══════ {етикет} ══════")
    print(f"  ръна {n} · с жив сетъп {len(act)} · пратени карти {len(карти)}")
    print(f"  спрени ТОЧНО от «възраст>12ч»: {len(вз)} ({100*len(вз)/max(1,len(act)):.1f}% от живите сетъпи)")
    print(f"  от тях с gate.ok=True (реално изяден вход): {len(скъпи)}")
    if вз:
        print(f"  макс възраст на ключа: {max(x['key_age'] for x in вз):.1f}ч")
    # най-дълга НЕПРЕКЪСНАТА поредица «възраст>12ч»
    best=(0,None,None); cur=0; st=None
    for x in ред:
        if x["блокер"]=="ВЪЗРАСТ>12ч":
            if cur==0: st=x["utc"]
            cur+=1; 
            if cur>best[0]: best=(cur,st,x["utc"])
        else: cur=0
    if best[1]:
        h=(pd.Timestamp(best[2])-pd.Timestamp(best[1])).total_seconds()/3600
        print(f"  най-дълга непрекъсната: {best[1]} → {best[2]} = {h:.1f}ч, {best[0]} ръна")
