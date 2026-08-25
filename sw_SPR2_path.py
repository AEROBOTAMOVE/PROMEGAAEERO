# -*- coding: utf-8 -*-
"""Кой ПЪТ реално затваря сделките в производството: «бар» или «спот»?
Взимам всички изходни карти от sent_log.jsonl. Часът в картата е `when`:
  via='спот' -> when = now_utc (часът на РЪНА)
  via='бар'  -> when = времето на БАРА (по-старо)
София = UTC+3 (лятно)."""
import json, io, re, collections, datetime as dt
rows=[]
for ln in io.open('live/sent_log.jsonl',encoding='utf-8'):
    ln=ln.strip()
    if not ln: continue
    r=json.loads(ln); t=str(r.get('tag') or '')
    if not (t.startswith('sh-exit') or t.startswith('s-exit')): continue
    rows.append(r)
print("изходни карти:",len(rows))
res=collections.Counter(); delta=[]
for r in rows:
    kind=r['tag'].split(':')[1]
    m=re.search(r'(\d{2}):(\d{2}) София', r['text']) or re.search(r'· (\d{2}):(\d{2})\b', r['text'])
    if not m:
        res[(kind,'без час')]+=1; continue
    hh,mm=int(m.group(1)),int(m.group(2))
    u=dt.datetime.fromisoformat(r['utc'])
    sof=u+dt.timedelta(hours=3)
    ev=sof.replace(hour=hh,minute=mm,second=0,microsecond=0)
    d=(sof-ev).total_seconds()/60.0
    if d<-60: d+=1440
    delta.append((kind,round(d,1)))
    res[(kind,'спот' if d<=3 else 'бар')]+=1
print("вид × път:",{f"{k[0]}/{k[1]}":v for k,v in sorted(res.items())})
tp=[d for k,d in delta if k.startswith('tp')]
print("изоставане (мин) при ЦЕЛИ: n=%d медиана=%.1f"%(len(tp), sorted(tp)[len(tp)//2] if tp else -1))
print("разпределение:",collections.Counter(round(d) for k,d in delta).most_common(12))
