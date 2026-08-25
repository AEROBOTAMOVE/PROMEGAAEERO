# -*- coding: utf-8 -*-
import json, collections, io
P="live/sent_log.jsonl"
rows=[json.loads(l) for l in io.open(P,encoding="utf-8") if l.strip()]
print("записи:",len(rows), rows[0]["utc"], rows[-1]["utc"])
by=collections.OrderedDict()
for r in rows:
    by.setdefault(r["utc"],[]).append(r["tag"])
print("уникални минути/секунди:",len(by))
EXIT=("exit","s-exit","sh-exit","brain-exit")
SIG=("signal","s-signal")
def isexit(t): return t.split(":")[0] in EXIT
def issig(t): return t.split(":")[0] in SIG
both=0; naru=0
for u,tags in by.items():
    if any(isexit(t) for t in tags) and any(issig(t) for t in tags):
        both+=1
        # индекс на първи сигнал и последен изход
        fi=min(i for i,t in enumerate(tags) if issig(t))
        li=max(i for i,t in enumerate(tags) if isexit(t))
        bad = fi<li
        naru+= 1 if bad else 0
        print(("НАРУШЕН " if bad else "ОК      "),u,tags)
print("минути с ИЗХОД+ВХОД:",both,"нарушени:",naru)
# разбивка по видове изход
c=collections.Counter(r["tag"].split(":")[0] for r in rows)
print(c)
