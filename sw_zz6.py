# -*- coding: utf-8 -*-
import json, io, collections
rows=[json.loads(l) for l in io.open('live/brain_journal.jsonl',encoding='utf-8') if l.strip()]
print('записи в brain_journal:', len(rows))
c=collections.Counter()
for r in rows:
    z=r.get('застудяване')
    k = 'МЪЛЧИ(застудяване)' if z and 'мълчи' in str(z) else (str(z).split('·')[0].strip() if z else ('ПРАТЕНА' if r.get('праща') else 'без причина'))
    c[k]+=1
for k,v in c.most_common(): print(f'  {v:6d}  {k}')
print()
print('праща=True:', sum(1 for r in rows if r.get('праща')))
print()
print('живо brain_state.json:')
print(io.open('live/brain_state.json',encoding='utf-8').read())
