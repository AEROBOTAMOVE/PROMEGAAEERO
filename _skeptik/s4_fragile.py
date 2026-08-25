import json, itertools, collections, math
L=[json.loads(l) for l in open('live/live_journal.jsonl',encoding='utf-8') if l.strip()]
F=["1мин","5м","15м","30м","1час","4час","1ден"]
INTRA=[f for f in F if f!="1ден"]
days=sorted({d['run_utc'][:10] for d in L})
print("дни:",len(days))

def zeros(subset):
    S=[d for d in L if d['run_utc'][:10] in subset]
    z=[p for p in itertools.combinations(INTRA,2) if all(d['board'][p[0]]==d['board'][p[1]] for d in S)]
    return z,len(S)

z,n=zeros(set(days))
print(f"\nЦЕЛИЯТ дневник ({n} руна, {len(days)} дни): бит-идентични интрадей двойки = {len(z)} от 15")
for a,b in z: print("   ",a,"==",b)

# КОЛКО КРЕХКО Е: махам ЕДИН ден
print("\n--- LEAVE-ONE-DAY-OUT: колко двойки стават «бит-идентични, 0 разминавания» ---")
for dd in days:
    sub=set(days)-{dd}
    z2,n2=zeros(sub)
    if len(z2)>len(z):
        extra=[f"{a}=={b}" for a,b in z2 if (a,b) not in z]
        print(f"  без {dd} ({n2} руна): {len(z2)} от 15 идентични  (+{len(extra)}) -> {extra}")
# махам двата "шумни" дни
sub=set(days)-{'2026-08-03','2026-08-04'}
z3,n3=zeros(sub)
print(f"\n  без 03.08 И 04.08 ({n3} руна, {len(sub)} дни): {len(z3)} от 15 двойки са 'бит-идентични'")
for a,b in z3: print("     ",a,"==",b)

# Правило на тройката (0 успеха) - честната граница вместо изроден бутстрап
print("\n--- ЧЕСТНАТА ГРАНИЦА при 0 разминавания (правило на тройката) ---")
print(f"  на ниво РЪН   : 0/{len(L)}  -> горна 95% граница {3/len(L)*100:.4f}% от ръновете")
print(f"  на ниво ДЕН   : 0/{len(days)} -> горна 95% граница {3/len(days)*100:.2f}% от дните")
print("  (блоков бутстрап на КОНСТАНТА винаги връща същата константа -> [100,100] не е измерване)")
# демонстрация че бутстрапът е изроден
import random
random.seed(7)
bydays=collections.defaultdict(list)
for d in L: bydays[d['run_utc'][:10]].append(d['board']['1мин']==d['board']['5м'])
res=[]
for _ in range(4000):
    s=[]; 
    for _ in range(len(days)): s+=bydays[random.choice(days)]
    res.append(100*sum(s)/len(s))
res.sort()
print(f"  моят блоков бутстрап (4000): {res[len(res)//2]:.3f}  95% [{res[100]:.3f} .. {res[3899]:.3f}]  <- възпроизвежда се, но е ИЗРОДЕН")
