# -*- coding: utf-8 -*-
"""Всяко ЕДНО застудяване в живия бот — навито ли е от РЕАЛНО ДОСТАВЕНА карта?"""
import json, io
rows=[json.loads(l) for l in io.open('live/brain_journal.jsonl',encoding='utf-8') if l.strip()]
# кои тагове са РЕАЛНО пратени и кога (от sent_log)
sent=[json.loads(l) for l in io.open('live/sent_log.jsonl',encoding='utf-8') if l.strip()]
sent_brain=[(s['utc'],s['tag']) for s in sent if s['tag'].startswith('brain:')]
print('brain карти в sent_log (РЕАЛНО доставени):', len(sent_brain))
last_send={}
for r in rows:
    key=f"{r.get('рамка')}|{r.get('посока')}"
    if r.get('праща'): last_send[key]=r['utc']
    z=r.get('застудяване')
    if z and 'мълчи' in str(z):
        src=last_send.get(key)
        # има ли РЕАЛНА доставка на този таг в същия рън?
        ok=any(u==src for u,t in sent_brain if t.startswith(f"brain:{r.get('рамка')}:"))
        print(f"  {r['utc']}  {key:14s} заглушена от карта на {src}  → доставена в sent_log: {ok}")
