import json, io
from collections import defaultdict
runs = []
for line in io.open('live/live_journal.jsonl', encoding='utf-8'):
    line = line.strip()
    if not line:
        continue
    try:
        r = json.loads(line)
    except Exception:
        continue
    if r.get('weekend') or 'spot' not in r:
        continue
    runs.append(r)
runs.sort(key=lambda r: r['run_utc'])
a = defaultdict(int); b = defaultdict(int); c = defaultdict(int)
for r in runs:
    d = r['run_utc'][:10]
    c[d] += 1
    if r.get('spot') is None:
        a[d] += 1
    if r.get('spot_rejected'):
        b[d] += 1
print('den         ryna   spot=None   spot_rejected')
for d in sorted(c):
    if d >= '2026-08-17':
        print(f'{d}   {c[d]:4d}      {a[d]:4d}          {b[d]:4d}')
print()
print('tvyrdeniyata na agenta: 08-19 194/303, 08-20 294/295, 08-21 93/94, 08-11 333 ryna')
print('mereno ot men (gore).  08-11 ryna =', c['2026-08-11'])
