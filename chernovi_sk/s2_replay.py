import sys, os; sys.path.insert(0, os.getcwd())
# Реплей на РЕАЛНИЯ live_journal.jsonl през ИСТИНСКИТЕ правила от live_bot.py
import json, sys
import live_bot as lb

runs=[]
with open('live/live_journal.jsonl',encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if not line: continue
        try: r=json.loads(line)
        except Exception: continue
        if r.get('weekend'): continue
        if 'spot' not in r: continue
        runs.append(r)
runs.sort(key=lambda r: r['run_utc'])
print('nevikend runs:', len(runs), runs[0]['run_utc'], '->', runs[-1]['run_utc'])
print('SPAL_MIN =', lb.СПАЛ_МИН, ' SUHI_MAKS =', lb.СУХИ_МАКС, ' VERSION =', lb.VERSION)
print()

# --- 1) ПЪРВИЯТ будилник: най-дългата дупка в ТЪРГОВСКИ минути, по дни
from collections import defaultdict
maxgap=defaultdict(float); cnt=defaultdict(int)
prev=None
gap_alarms=0
for r in runs:
    d=r['run_utc'][:10]; cnt[d]+=1
    if prev:
        g=lb._търговски_минути(prev, r['run_utc'])
        if g>maxgap[d]: maxgap[d]=g
        if g>=lb.СПАЛ_МИН: gap_alarms+=1
    prev=r['run_utc']
print('PARVI budilnik (dupka >= 45 targ.min):')
for d in sorted(cnt):
    print(f'  {d}  runs={cnt[d]:4d}  nay-dylga dupka={maxgap[d]:6.1f} targ.min')
print('  OBSHTO paleniya na parviya budilnik:', gap_alarms)
print()

# --- 2) ВТОРИЯТ будилник: реплей на брояча сухи_ръна с ИСТИНСКИЯ праг
meta={}
firsts=[]   # (utc, брой) кога картата би пламнала
maxstreak=0; maxfrom=None; maxto=None
dry_by_day=defaultdict(int)
for r in runs:
    d=r['run_utc'][:10]
    spot = r.get('spot')
    if spot is not None:
        meta['сухи_ръна']=0
        meta['сухи_последно_жив']=r['run_utc']
    else:
        dry_by_day[d]+=1
        meta['сухи_ръна']=int(meta.get('сухи_ръна',0))+1
        if meta['сухи_ръна']>maxstreak:
            maxstreak=meta['сухи_ръна']; maxto=r['run_utc']
            maxfrom=meta.get('сухи_последно_жив')
        if meta['сухи_ръна']==lb.СУХИ_МАКС:
            firsts.append((r['run_utc'], meta['сухи_ръна'], r.get('spot_rejected')))
print('VTORI budilnik (suhi_ryna >= %d):' % lb.СУХИ_МАКС)
for d in sorted(cnt):
    print(f'  {d}  runs={cnt[d]:4d}  bez zhiva cena={dry_by_day[d]:4d}')
print('  nay-dylga poredica bez zhiva cena:', maxstreak, 'ryna', maxfrom, '->', maxto)
print('  KOGA kartata bi plamnala parvi pyt (prag %d):' % lb.СУХИ_МАКС)
for u,n_,rej in firsts:
    print(f'    {u}   suhi={n_}  spot_rejected={rej}')
