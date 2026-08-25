# -*- coding: utf-8 -*-
import json, io
sent=[json.loads(l) for l in io.open('live/sent_log.jsonl',encoding='utf-8') if l.strip()]
for s in sent:
    if s['tag'].startswith('brain') and s['utc'][:10]=='2026-08-17':
        print(s['utc'], s['tag'])
print('---- всички brain в sent_log с час ----')
for s in sent:
    if s['tag'].startswith('brain:'):
        print(s['utc'], s['tag'])
