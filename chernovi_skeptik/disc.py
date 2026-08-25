# -*- coding: utf-8 -*-
import sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from collections import defaultdict
recs=[]
for line in open('live/live_journal.jsonl',encoding='utf-8'):
    line=line.strip()
    if not line: continue
    try: d=json.loads(line)
    except: continue
    recs.append(d)
print("ВСИЧКИ редове (вкл. уикенд):", len(recs))
for den in ['2026-08-19','2026-08-20','2026-08-21']:
    dd=[d for d in recs if str(d.get('run_utc',''))[:10]==den]
    we=[d for d in dd if d.get('weekend')]
    spot_none=[d for d in dd if d.get('spot') is None]
    rej=[d for d in dd if d.get('spot_rejected')]
    both=[d for d in dd if d.get('spot') is None or d.get('spot_rejected')]
    print(f"{den}: редове={len(dd)} уикенд={len(we)} | spot=None:{len(spot_none)} | spot_rejected:{len(rej)} | (None ИЛИ rejected):{len(both)}")
