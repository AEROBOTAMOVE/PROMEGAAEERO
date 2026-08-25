# -*- coding: utf-8 -*-
import json, collections
rows=[]
for ln in open("live/live_journal.jsonl", encoding="utf-8"):
    ln=ln.strip()
    if not ln: continue
    try: rows.append(json.loads(ln))
    except: pass
print("ръна в дневника:", len(rows), "от", rows[0]["run_utc"], "до", rows[-1]["run_utc"])

def st(r): return [str(x) for x in (r.get("status") or [])]

# 1) колко ръна СИЗОБЩО са докосвали таг signal
tagcnt=collections.Counter()
for r in rows:
    for s in st(r):
        if "=" in s: tagcnt[s.split("=")[0]]+=1
print("\nнай-чести тагове в statuses:", tagcnt.most_common(12))

# 2) ръна, които ОСТАВЯТ signal в пощата (неуспешно пращане)
def leaves_signal(r):
    out=[]
    for s in st(r):
        if s.startswith("signal=") or s.startswith("s-signal="):
            res=s.split("=",1)[1]
            if not res.startswith("SENT"): out.append(s)
    return out
left=[(i,r,leaves_signal(r)) for i,r in enumerate(rows) if leaves_signal(r)]
print("\nръна, в които signal/s-signal НЕ е пратен (→ остава в пощата):", len(left))
for i,r,x in left[:15]:
    print("  ", r["run_utc"], x)

# 3) от тях: следващият рън регенерира ли го?
tihi=0; regen=0
for i,r,x in left:
    if i+1>=len(rows): continue
    nxt=st(rows[i+1])
    if any(s.startswith(("signal=","s-signal=")) for s in nxt): regen+=1
    else: tihi+=1
print("  → следващият рън ГО РЕГЕНЕРИРА (дедупът говори):", regen)
print("  → следващият рън МЪЛЧИ (кандидат за тих отрез):", tihi)

# 4) колко пъти дедупът/таванът/отровното РЕАЛНО са говорили в живота
for pat,name in [("дедуп","дедуп"),("преля","таван"),("ОТРОВНО","отровно"),
                 ("повредени","повреден ред"),("DRY (остава","dry"),
                 ("ЛИПСВА TELEGRAM","без токен"),("НЕ пратен","signal НЕ пратен")]:
    n=sum(1 for r in rows if any(pat in s for s in st(r)))
    print(f"  {name:16s}: {n} ръна")
