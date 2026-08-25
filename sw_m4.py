# -*- coding: utf-8 -*-
import json
from collections import Counter
rows=[]
for f in ["live/archive/live_journal-2026-07.jsonl","live/live_journal.jsonl"]:
    for l in open(f,encoding="utf-8"):
        l=l.strip()
        if l:
            try: rows.append(json.loads(l))
            except: pass
def S(r): return [str(x) for x in (r.get("status") or [])]

# --- епизодът 22.07: непратен signal → регенерира ли се СЛЕДВАЩИЯ рън?
idx=[i for i,r in enumerate(rows) if any(s.startswith("signal=HARD") or s.startswith("signal=SEND_FAILED") for s in S(r))]
print("ръна с НЕПРАТЕН золотен signal:", len(idx), "от", rows[idx[0]]["run_utc"], "до", rows[idx[-1]]["run_utc"])
regen=0; tih=0
for i in idx:
    if i+1>=len(rows): continue
    nxt=S(rows[i+1])
    if any(s.startswith("signal=") for s in nxt): regen+=1
    else:
        tih+=1; print("   ТИХ КАНДИДАТ:", rows[i+1]["run_utc"], nxt)
print("следващият рън ПАК опитва signal (значи е регенериран → защитен):", regen)
print("следващият рън МЪЛЧИ за signal (кандидат за тих отрез):", tih)

# --- ОДИТ-26 картата «виждам, но не предлагам»
sp=[(r["run_utc"],s) for r in rows for s in S(r) if s.startswith("спряна")]
print("\nкарти «спряна:<посока>» (ОДИТ-26 обяснява защо НЯМА вход):", len(sp), sp[:6])
# --- бележките за спирачките
nt=Counter()
for r in rows:
    for n in (r.get("notes") or []):
        n=str(n)
        for k in ("уикенд","US-щит","стоп-пазач","макро събитие","насрещен непремиум","flip-лентата"):
            if k in n: nt[k]+=1
print("бележки за спирачки (те са причината should_sig да падне):", dict(nt))
