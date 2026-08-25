import json, itertools, collections
L=[json.loads(l) for l in open('live/live_journal.jsonl',encoding='utf-8') if l.strip()]
F=["1мин","5м","15м","30м","1час","4час","1ден"]
n=len(L)
dis=collections.Counter()
for d in L:
    b=d['board']
    for a,c in itertools.combinations(F,2):
        if b[a]!=b[c]: dis[(a,c)]+=1
print("N руна =",n)
print("--- разминавания по двойки (моя сметка) ---")
for (a,c),v in sorted(dis.items(), key=lambda x:-x[1]):
    print(f"{a:5s} vs {c:5s}  {v:5d}  {100*v/n:6.2f}%")
zero=[p for p in itertools.combinations(F,2) if dis[p]==0]
print("--- НУЛЕВИ двойки:",[f"{a}=={c}" for a,c in zero], " общо",len(zero),"от 21")
# каква част от полето изобщо се различава
allsame=sum(1 for d in L if len({tuple(d['board'][f]) for f in F})==1)
print("руна, в които И 7-те рамки са еднакви:",allsame, f"{100*allsame/n:.2f}%")
# ако махнем 1ден - колко остават различни
F6=[f for f in F if f!="1ден"]
allsame6=sum(1 for d in L if len({tuple(d['board'][f]) for f in F6})==1)
print("руна, в които 6-те ИНТРАДЕЙ рамки са еднакви:",allsame6, f"{100*allsame6/n:.2f}%")
