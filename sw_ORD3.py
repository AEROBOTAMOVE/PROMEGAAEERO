# -*- coding: utf-8 -*-
import json, io, collections
rows=[json.loads(l) for l in io.open("live/sent_log.jsonl",encoding="utf-8") if l.strip()]
by=collections.OrderedDict()
for r in rows: by.setdefault(r["utc"],[]).append(r)
EXIT=("exit","s-exit","sh-exit","brain-exit")
def base(t): return t.split(":")[0]
# 1) колко от 48-те 'signal' карти са ИСТИНСКИ вход (не «БЕЗ ВХОД»)
sig=[r for r in rows if r["tag"]=="signal"]
bezvhod=[r for r in sig if "БЕЗ ВХОД" in r["text"] or "размер: НУЛА" in r["text"]]
print("signal общо:",len(sig)," от тях «БЕЗ ВХОД/НУЛА»:",len(bezvhod)," истински вход:",len(sig)-len(bezvhod))
# 2) мозък-карта преди мозък-изход в един рън
a=b=0
for u,rs in by.items():
    tg=[r["tag"] for r in rs]
    if any(base(t)=="brain" for t in tg) and any(base(t)=="brain-exit" for t in tg):
        a+=1
        fb=min(i for i,t in enumerate(tg) if base(t)=="brain")
        lx=max(i for i,t in enumerate(tg) if base(t)=="brain-exit")
        if fb<lx: b+=1; print("  мозък-карта ПРЕДИ мозък-изход:",u,tg)
print("рънове с мозък-карта И мозък-изход:",a,"нарушени:",b)
# 3) signal + brain-exit заедно
c=d=0
for u,rs in by.items():
    tg=[r["tag"] for r in rs]
    if any(t in ("signal","s-signal") for t in tg) and any(base(t)=="brain-exit" for t in tg):
        c+=1
        fs=min(i for i,t in enumerate(tg) if t in ("signal","s-signal"))
        lx=max(i for i,t in enumerate(tg) if base(t)=="brain-exit")
        if fs<lx: d+=1
        print("  signal+brain-exit:",u,tg,"нарушен" if fs<lx else "ок")
print("рънове signal+brain-exit:",c,"нарушени:",d)
# 4) реален изход (exit/s-exit) спрямо signal — обещанието на коментара
e=f=0
for u,rs in by.items():
    tg=[r["tag"] for r in rs]
    if any(base(t) in ("exit","s-exit") for t in tg) and any(t in ("signal","s-signal") for t in tg):
        e+=1
        fs=min(i for i,t in enumerate(tg) if t in ("signal","s-signal"))
        lx=max(i for i,t in enumerate(tg) if base(t) in ("exit","s-exit"))
        if fs<lx: f+=1; print("  РЕАЛЕН изход след сигнал:",u,tg)
print("рънове реален-изход+сигнал:",e,"нарушени:",f)
print("общо рънове със записи:",len(by))
