# ИЗПЪЛНЕНИЕ на ИСТИНСКАТА _съгласни от live_bot.py (изрязана по AST, не преписана)
import ast, json, collections, itertools
src=open('live_bot.py',encoding='utf-8').read()
t=ast.parse(src); lines=src.splitlines()
for n in ast.walk(t):
    if isinstance(n,ast.FunctionDef) and n.name=='_съгласни':
        code="\n".join(lines[n.lineno-1:n.end_lineno])
ns={}; exec(code, ns); _съгласни=ns['_съгласни']

L=[json.loads(l) for l in open('live/live_journal.jsonl',encoding='utf-8') if l.strip()]
F=["1мин","5м","15м","30м","1час","4час","1ден"]
rank={"premium":3,"strong":2,"medium":1,"weak":0}
same=0; diff=0; ex=[]
for d in L:
    b=d['board']
    full =[(f,)+tuple(b[f]) for f in F]
    fixed=[(f,)+tuple(b[f]) for f in F if f!="1мин"]
    for посока in ("long","short"):
        a=_съгласни(full,посока); c=_съгласни(fixed,посока)
        if a==c: same+=1
        else:
            diff+=1
            if len(ex)<5: ex.append((d['run_utc'],посока,a,c))
print("ИЗПЪЛНЕНО с истинската _съгласни, ",len(L),"руна x 2 посоки")
print("  ЕДНАКЪВ отчет (пълна дъска vs дъска без «1мин»):",same)
print("  РАЗЛИЧЕН отчет:",diff)
for e in ex: print("   пример",e)

# --- дни ---
days=collections.Counter(d['run_utc'][:10] for d in L)
print("\nразлични ДНИ в дневника:",len(days))
print("първи/последен рън:",L[0]['run_utc'],"->",L[-1]['run_utc'])
print("руна/ден медиана:",sorted(days.values())[len(days)//2],"средно %.1f"%(len(L)/len(days)))
# анюализация
import datetime as dt
d0=dt.datetime.fromisoformat(L[0]['run_utc']); d1=dt.datetime.fromisoformat(L[-1]['run_utc'])
span=(d1-d0).total_seconds()/86400
print("обхват дни: %.2f  ->  руна/год = %.0f"%(span, len(L)/span*365))

# --- дневно струпване на разминаванията при двойките, които СЕ различават ---
print("\n--- в колко РАЗЛИЧНИ ДНИ се случва разминаване (за двойките, които изобщо се различават) ---")
for a,c in itertools.combinations(F,2):
    dd={d['run_utc'][:10] for d in L if d['board'][a]!=d['board'][c]}
    nn=sum(1 for d in L if d['board'][a]!=d['board'][c])
    if nn: print(f"  {a:5s} vs {c:5s}: {nn:4d} руна, но само {len(dd):2d} различни дни -> {sorted(dd)}" if len(dd)<=6 else f"  {a:5s} vs {c:5s}: {nn:4d} руна в {len(dd)} дни")
