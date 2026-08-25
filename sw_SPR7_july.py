# -*- coding: utf-8 -*-
import json,io,re,collections,datetime as dt
res=collections.Counter()
for f in ('live/archive/sent_log-2026-07.jsonl','live/sent_log.jsonl'):
    for ln in io.open(f,encoding='utf-8'):
        ln=ln.strip()
        if not ln: continue
        r=json.loads(ln); t=str(r.get('tag') or '')
        if 'exit' not in t: continue
        вид=t.split(':')[1] if ':' in t else '?'
        реал = t.startswith('exit') or t.startswith('s-exit')
        m=re.search(r'(\d{2}):(\d{2}) София', r['text']) or re.search(r'· (\d{2}):(\d{2})\b', r['text'])
        if not m: res[(вид,'без час',реал)]+=1; continue
        u=dt.datetime.fromisoformat(r['utc']); sof=u+dt.timedelta(hours=3)
        d=(sof-sof.replace(hour=int(m.group(1)),minute=int(m.group(2)),second=0,microsecond=0)).total_seconds()/60
        if d<-60: d+=1440
        res[(вид,'спот' if d<=3 else 'бар','РЕАЛНА' if реал else 'сянка')]+=1
for k,v in sorted(res.items(), key=lambda x:str(x[0])): print(k,v)
цел_спот=sum(v for k,v in res.items() if k[0].startswith('tp') and k[1]=='спот')
цел_бар =sum(v for k,v in res.items() if k[0].startswith('tp') and k[1]=='бар')
print("\nЦЕЛИ общо: спот=%d бар=%d -> спот-съдникът решава %.0f%%"%(цел_спот,цел_бар,100*цел_спот/(цел_спот+цел_бар)))
