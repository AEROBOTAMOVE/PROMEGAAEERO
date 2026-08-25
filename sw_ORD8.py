# -*- coding: utf-8 -*-
import json,io,collections
FIX="2026-08-12T18:22"   # 21:22 София = 18:22 UTC
J=[json.loads(l) for l in io.open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
post=[r for r in J if r["run_utc"]>=FIX]
print("рънове СЛЕД ОДИТ-63:",len(post))
rows=[json.loads(l) for l in io.open("live/sent_log.jsonl",encoding="utf-8") if l.strip()]
by=collections.OrderedDict()
for r in rows: by.setdefault(r["utc"],[]).append(r["tag"])
def base(t): return t.split(":")[0]
EXIT=("exit","s-exit","sh-exit","brain-exit")
n=bad=0
for u,tg in by.items():
    if u<FIX: continue
    if any(base(t) in ("signal","s-signal") for t in tg) and any(base(t) in EXIT for t in tg):
        n+=1
        fi=min(i for i,t in enumerate(tg) if base(t) in ("signal","s-signal"))
        lx=max(i for i,t in enumerate(tg) if base(t) in EXIT)
        b=fi<lx; bad+=b
        print("  ",u,tg,"НАРУШЕН" if b else "ок")
print("СЛЕД фикса: минути с изход+сигнал =",n,"нарушени =",bad)
print("сигнали след фикса:",sum(1 for r in rows if r["utc"]>=FIX and r["tag"]=="signal"))
print("brain-exit след фикса:",sum(1 for r in rows if r["utc"]>=FIX and base(r["tag"])=="brain-exit"))
