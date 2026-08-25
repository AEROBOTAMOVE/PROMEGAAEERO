import sys, json, datetime as dt
sys.stdout.reconfigure(encoding='utf-8')
sys.argv=["x"]; import live_bot as lb
rows=[json.loads(l) for l in open('live/live_journal.jsonl',encoding='utf-8') if l.strip()]
rows=[r for r in rows if isinstance(r.get("board"),dict) and r["board"] and r["run_utc"]>="2026-08-18T05:00"]
rows.sort(key=lambda r:r["run_utc"])
sig=set()
for l in open('live/sent_log.jsonl',encoding='utf-8'):
    if l.strip():
        d=json.loads(l)
        if d["tag"]=="signal": sig.add(d["utc"][:16])
def key_of(b):
    o=sorted({f"{v[0]}:{v[2]}" for v in b.values() if v[2]!="weak" and v[0]!="wait"})
    return f"{len(o)}|"+";".join(o)
last={}
maxage=0; хапе=0
for r in rows:
    k=key_of(r["board"]); now=dt.datetime.fromisoformat(r["run_utc"])
    age=None
    if last.get("key")==k and last.get("key_since"):
        age=(now-last["key_since"]).total_seconds()/3600
    if age is not None:
        maxage=max(maxage,age)
        if age>lb.REOFFER_MAX_AGE_H: хапе+=1
    if r["run_utc"][:16] in sig:
        ks=last["key_since"] if last.get("key")==k and last.get("key_since") else now
        last={"key":k,"key_since":ks}
        print("  ⟶ ПРАТЕН СИГНАЛ", r["run_utc"], "key=",k,"key_since=",ks)
print(f"след ОДИТ-67: макс key_age_h = {maxage:.2f}ч; ръна с възраст НАД тавана 12ч = {хапе}")
print("живото сравнение (действителен ред от дневника, v12.8):")
for r in rows:
    for n in (r.get("notes") or []):
        if "предлагане" in n or "стоящ сетъп" in n: print("   ", r["run_utc"], r.get("v"), n)
