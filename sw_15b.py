import sys, json, datetime as dt, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.argv=["x"]; import live_bot as lb

rows=[]
for l in open('live/live_journal.jsonl',encoding='utf-8'):
    l=l.strip()
    if not l: continue
    try: r=json.loads(l)
    except Exception: continue
    rows.append(r)
rows.sort(key=lambda r: r.get("run_utc",""))

# 1) КАКВО КАЗВА ЖИВИЯТ ДНЕВНИК
c=collections.Counter()
prim={}
for r in rows:
    for n in (r.get("notes") or []):
        for w in ("повторно предлагане","стоящ сетъп","сетъпът изчезна"):
            if n.startswith(w):
                c[w]+=1; prim.setdefault(w,(r["run_utc"],n))
print("В ЖИВИЯ ДНЕВНИК (3554 ръна, 02.08→19.08):")
for w in ("повторно предлагане","стоящ сетъп","сетъпът изчезна"):
    print(f"  {w!r}: {c[w]}", ("| пример: "+str(prim.get(w))) if c[w] else "")

# 2) симулация на key_age_h
sig={}
for l in open('live/sent_log.jsonl',encoding='utf-8'):
    if not l.strip(): continue
    d=json.loads(l)
    if d["tag"]=="signal": sig[d["utc"][:16]]=1
def key_of(b):
    отч = sorted({f"{v[0]}:{v[2]}" for v in b.values() if v[2]!="weak" and v[0]!="wait"})
    return f"{len(отч)}|" + ";".join(отч)
last={}; ages=[]
for r in rows:
    b=r.get("board")
    if not isinstance(b,dict) or not b: continue
    k=key_of(b); now=dt.datetime.fromisoformat(r["run_utc"])
    age=None
    if last.get("key")==k and last.get("key_since"):
        age=(now-last["key_since"]).total_seconds()/3600
    ages.append((r["run_utc"],k,age))
    if r["run_utc"][:16] in sig:
        ks = last["key_since"] if last.get("key")==k and last.get("key_since") else now
        last={"key":k,"key_since":ks}
имa=[a for _,_,a in ages if a is not None]
print(f"\nСИМУЛАЦИЯ на key_age_h ({len(ages)} ръна):")
print(f"  key_age_h е None (ключът НЕ съвпада с последната карта): {sum(1 for _,_,a in ages if a is None)}")
print(f"  key_age_h ≤ 12ч: {sum(1 for a in имa if a<=12)}")
print(f"  key_age_h  > 12ч (ТАВАНЪТ ХАПЕ): {sum(1 for a in имa if a>12)}")
print(f"  в прозореца за реофер 6-12ч: {sum(1 for a in имa if 6<=a<=12)}")
print("  макс възраст:", round(max(имa),1) if имa else None)
