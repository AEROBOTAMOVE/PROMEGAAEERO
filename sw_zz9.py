# -*- coding: utf-8 -*-
"""Поправено сравнение: sent_log пише часа на ФЛЪША (със секунди), brain_journal — часа на РЪНА."""
import json, io, datetime as dt
P='%Y-%m-%dT%H:%M:%S'
def t(s): return dt.datetime.fromisoformat(s)
rows=[json.loads(l) for l in io.open('live/brain_journal.jsonl',encoding='utf-8') if l.strip()]
sent=[json.loads(l) for l in io.open('live/sent_log.jsonl',encoding='utf-8') if l.strip()]
sb=[(t(s['utc']), s['tag']) for s in sent if s['tag'].startswith('brain:')]
queued=[r for r in rows if r.get('праща')]
print('ПОСТАВЕНИ В ПОЩАТА (праща=True):', len(queued))
print('ДОСТАВЕНИ (sent_log brain:):   ', len(sb))
nedost=[]
for r in queued:
    ru=t(r['utc']+':00'); tag=f"brain:{r['рамка']}:{r['посока']}"
    hit=[u for u,g in sb if g==tag and 0<=(u-ru).total_seconds()<=600]
    if not hit: nedost.append((r['utc'],tag))
print('поставени БЕЗ доставка в рамките на 10 мин:', len(nedost), nedost)
print()
last={}
ok=bad=0
for r in rows:
    k=f"{r.get('рамка')}|{r.get('посока')}"
    if r.get('праща'): last[k]=r['utc']
    z=r.get('застудяване')
    if z and 'мълчи' in str(z):
        src=last.get(k)
        ru=t(src+':00'); tag=f"brain:{r['рамка']}:{r['посока']}"
        d=[u for u,g in sb if g==tag and 0<=(u-ru).total_seconds()<=600]
        if d: ok+=1
        else: bad+=1; print('  ЗАГЛУШЕНА БЕЗ ДОСТАВКА:', r['utc'], k, 'от', src)
print(f'застудявания в живия бот: {ok+bad} · навити от ДОСТАВЕНА карта: {ok} · от НЕДОСТАВЕНА: {bad}')
