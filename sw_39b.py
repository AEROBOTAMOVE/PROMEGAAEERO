# -*- coding: utf-8 -*-
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
rows=[json.loads(l) for l in open('live/live_journal.jsonl',encoding='utf-8') if l.strip()]
sent=[json.loads(l) for l in open('live/sent_log.jsonl',encoding='utf-8') if l.strip()]
print("sent_log ключове:", sorted(set(sent[-1])))
рей={r["run_utc"] for r in rows if r.get("spot_rejected")}
# кои карти са пратени в рън, в който живата цена е била изхвърлена
броене={}
for s in sent:
    t=s.get("run_utc") or s.get("ts") or s.get("utc")
    if t in рей: броене[s.get("tag","?")]=броене.get(s.get("tag","?"),0)+1
print("карти, пратени в рън с ИЗХВЪРЛЕНА жива цена:", броене, "| общо", sum(броене.values()))
print("пример на рей-рън:", [ {k:r[k] for k in ('run_utc','spot_rejected','spot_src','bar_age_min','spot','bar')} for r in rows if r.get('spot_rejected')][-2:])
