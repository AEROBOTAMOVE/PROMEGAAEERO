# -*- coding: utf-8 -*-
"""S6: КОНТРАФАКТ. Ако вратата не се затваряше от възрастта, щеше ли да има ВХОД днес?
`_adv_ok` (gate.ok) НЕ зависи от историята на сигналите — зависи от streak/макро/стара цена —
затова взимането му от дневника е коректно и при друг таван."""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0,".")
import pandas as pd, live_bot as LB
rank={"premium":3,"strong":2,"medium":1,"weak":0}
_бавност={l:i for i,(l,*_) in enumerate(LB.TFS)}
recs=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]

def прогон(cap, gate_since_reset=False, слепи=False):
    last={}; сделка=None; входове=[]; карти=0; сляпо_мин=0.0; пред=None; пред_ok=False
    for r in recs:
        now=r["run_utc"]; bd=r.get("board") or {}
        board=[(l,v[0],v[1],v[2],"") for l,v in bd.items()]
        if not board: continue
        act=[b for b in board if b[1]!="wait" and b[3]!="weak"]
        best=max(board,key=lambda x:(rank[x[3]],x[2],_бавност.get(x[0],0))) if act else board[0]
        nd=best[1] if act else None
        _о=sorted({f"{d}:{t}" for _l,d,_s,t,_ in board if t!="weak" and d!="wait"})
        key=f"{len(_о)}|"+";".join(_о)
        g=r.get("gate") or {}; gok=bool(g.get("ok"))
        if not act and last.get("key"): last={k:v for k,v in last.items() if k!="key"}; сляпо_мин=0.0
        ms=(pd.Timestamp(now)-pd.Timestamp(last["sent_utc"])).total_seconds()/60 if last.get("sent_utc") else None
        tu=bool(nd and rank.get(best[3],0)>rank.get(last.get("tier","weak"),0) and nd==last.get("dir"))
        cool=(ms is None or ms>=45 or (nd and nd!=last.get("dir") and ms>=15) or tu)
        # ── ПОПРАВКА 2: гейтът си има свой часовник
        база=last.get("key_since")
        if gate_since_reset and last.get("key")==key and gok and not пред_ok and last.get("key_since"):
            last["key_since"]=now; база=now
        # ── ПОПРАВКА 1: сляпото време не се брои
        if слепи and пред and last.get("key")==key and not gok:
            сляпо_мин+=(pd.Timestamp(now)-pd.Timestamp(пред)).total_seconds()/60
        ka=None
        if last.get("key")==key and база:
            ka=(pd.Timestamp(now)-pd.Timestamp(база)).total_seconds()/3600
            if слепи: ka=max(0.0, ka-сляпо_мин/60)
        ro=(bool(act) and сделка is None and nd is not None
            and rank.get(best[3],0)>=rank.get(LB.РЕОФЕР_КЛАС,1)
            and ms is not None and ms>=LB.REOFFER_H*60
            and ka is not None and ka<=cap and LB._reoffer_hour_ok(now))
        should=bool(act) and (last.get("key")!=key or tu or ro) and cool
        if should and LB._market_closed(now): should=False
        if should and nd=="short" and r.get("shield") and сделка is None: should=False
        пред=now; пред_ok=gok
        if should:
            карти+=1
            ks=last.get("key_since") if last.get("key")==key and last.get("key_since") else now
            if last.get("key")!=key: сляпо_мин=0.0
            last={"key":key,"dir":nd,"tier":best[3],"sent_utc":now,"key_since":ks}
            if сделка is None and gok:
                сделка={"dir":nd,"utc":now}; входове.append((now,nd,best[3],round(ka,2) if ka is not None else None))
    return карти,входове

for етикет,kw in [("ЖИВИЯТ КОД (таван 12ч)",dict(cap=12)),
                  ("таван 24ч",dict(cap=24)),
                  ("таван 999ч (без таван)",dict(cap=999)),
                  ("ПОПРАВКА 2: gate_since (таван 12ч)",dict(cap=12,gate_since_reset=True)),
                  ("ПОПРАВКА 1: сляпото не се брои (таван 12ч)",dict(cap=12,слепи=True))]:
    к,вх=прогон(**kw)
    print(f"{етикет:44} карти {к:3} · ВХОДОВЕ {len(вх)} {вх[:3]}")
