# -*- coding: utf-8 -*-
import json, io, collections
ls = io.open('live/live_journal.jsonl', encoding='utf-8').read().splitlines()
res = collections.Counter(); bytag = collections.Counter()
fails = []
for ln in ls:
    try: d = json.loads(ln)
    except Exception: continue
    for s in (d.get('status') or []):
        if '=' not in s: continue
        tag, _, r = s.partition('=')
        head = r.split(':')[0].split(' ')[0]
        res[head] += 1
        bytag[(tag.split(':')[0], head)] += 1
        if head not in ('SENT',): fails.append((d['run_utc'], s[:120]))
print('ВСИЧКИ изходи на пощата:', dict(res))
print()
for k, v in sorted(bytag.items()):
    print(k, v)
print()
print('НЕ-SENT общо:', len(fails))
for f in fails[:25]: print(' ', f)
