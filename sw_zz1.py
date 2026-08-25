# -*- coding: utf-8 -*-
import json, io, re, collections
ls = io.open('live/live_journal.jsonl', encoding='utf-8').read().splitlines()
brain_out = collections.Counter()
poison = []
dry = []
hardfail = []
soft = []
runs_with_brain = 0
for ln in ls:
    try: d = json.loads(ln)
    except Exception: continue
    st = d.get('status') or []
    bs = [s for s in st if s.startswith('brain')]
    if bs: runs_with_brain += 1
    for s in bs:
        tag, _, res = s.partition('=')
        head = res.split(':')[0].split(' ')[0]
        brain_out[head] += 1
        if 'ОТРОВНО' in res: poison.append((d['run_utc'], s))
        elif res.startswith('DRY'): dry.append((d['run_utc'], s))
        elif res.startswith('HARD_FAIL'): hardfail.append((d['run_utc'], s))
        elif res.startswith('SEND_FAILED') or res.startswith('DRY_RUN'): soft.append((d['run_utc'], s))
print('общо ръна в дневника:', len(ls))
print('ръна със статус brain*:', runs_with_brain)
print('изходи:', dict(brain_out))
print('ОТРОВНО брой:', len(poison), poison[:5])
print('DRY брой:', len(dry), dry[:5])
print('HARD_FAIL брой:', len(hardfail), hardfail[:5])
print('МЕК/без токен брой:', len(soft), soft[:5])
