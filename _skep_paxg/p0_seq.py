# -*- coding: utf-8 -*-
import sys, json, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
rows=[]
for ln in open('live/live_journal.jsonl',encoding='utf-8'):
    try: d=json.loads(ln)
    except: continue
    rows.append((d.get('run_utc'), d.get('spot_src'), d.get('date')))
rows.sort(key=lambda r: str(r[0]))
print('общо реда:', len(rows))
print(collections.Counter(r[1] for r in rows).most_common())
# най-дълга поредица от paxg
best=0; cur=0; best_at=None; runs=[]
for t,s,_ in rows:
    if s and str(s).startswith('paxg'):
        cur+=1
        if cur>best: best=cur; best_at=t
    else:
        if cur: runs.append(cur)
        cur=0
if cur: runs.append(cur)
print('най-дълга поредица paxg:', best, 'край при', best_at)
print('разпределение на поредиците:', collections.Counter(runs).most_common())
print('брой отделни епизоди:', len(runs))
# и за None
best=0;cur=0;runs2=[]
for t,s,_ in rows:
    if s is None:
        cur+=1; best=max(best,cur)
    else:
        if cur: runs2.append(cur)
        cur=0
if cur: runs2.append(cur)
print('най-дълга поредица None:', best, collections.Counter(runs2).most_common(8))
