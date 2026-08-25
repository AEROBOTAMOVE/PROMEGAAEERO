# -*- coding: utf-8 -*-
import json,io,collections
rows=[json.loads(l) for l in io.open("live/sent_log.jsonl",encoding="utf-8") if l.strip()]
by=collections.OrderedDict()
for r in rows: by.setdefault(r["utc"],[]).append(r["tag"])
def base(t): return t.split(":")[0]
EXIT=("exit","s-exit","sh-exit","brain-exit")
for name,VH in (("вход=signal/s-signal",("signal","s-signal")),
                ("вход=signal/s-signal/brain",("signal","s-signal","brain"))):
    n=bad=0; det=[]
    for u,tg in by.items():
        if any(base(t) in VH for t in tg) and any(base(t) in EXIT for t in tg):
            n+=1
            fi=min(i for i,t in enumerate(tg) if base(t) in VH)
            lx=max(i for i,t in enumerate(tg) if base(t) in EXIT)
            b=fi<lx; bad+=b; det.append((u,tg,"НАРУШЕН" if b else "ок"))
    print(f"[{name}] минути с двете: {n}, нарушени: {bad}")
    for d in det: print("   ",d[0],d[1],d[2])
