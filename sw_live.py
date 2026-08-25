# -*- coding: utf-8 -*-
import sys, io, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
rows = [json.loads(x) for x in open('live/live_journal.jsonl', encoding='utf-8') if x.strip()]
print("ръна общо:", len(rows), " от", rows[0].get('run_utc'), "до", rows[-1].get('run_utc'))
g = [r for r in rows if r.get('gate')]
print("ръна с посока (gate!=None):", len(g))
c = collections.Counter((r['gate'].get('dir'), r['gate'].get('streak')) for r in g)
for k, v in sorted(c.items(), key=lambda x: -x[1]):
    print("   dir=%-5s streak=%-3s → %d" % (k[0], k[1], v))
dd = [r['gate'].get('dd20') for r in g if r['gate'].get('dd20') is not None]
print("ръна с dd20 записан:", len(dd))
if dd:
    dd_s = sorted(dd)
    import statistics
    print("   dd20 медиана %.4f  мин %.4f  макс %.4f" % (statistics.median(dd_s), dd_s[0], dd_s[-1]))
    print("   dd20 < 1.5%%: %d от %d (%.1f%%)" % (sum(1 for x in dd if x < 0.015), len(dd), 100*sum(1 for x in dd if x < 0.015)/len(dd)))
# несъответствия: by==клетка и мерено.кофа не съответства на cell
bad = 0; кофи = collections.Counter()
for r in g:
    ga = r['gate']; м = (ga.get('мерено') or {})
    кофи[(ga.get('by'), м.get('кофа'), ga.get('cell'))] += 1
    if ga.get('by') == 'клетка' and м.get('кофа') == 'връх-шорт':
        bad += 1
print("записи с кофа='връх-шорт':", bad)
print("--- (by, мерено.кофа, cell) честоти:")
for k, v in sorted(кофи.items(), key=lambda x: -x[1]):
    print("   ", k, v)
# колко пъти изобщо short с streak 2-3 в gate
s23 = [r for r in g if r['gate'].get('dir') == 'short' and r['gate'].get('streak') in (2, 3)]
print("short & streak 2-3:", len(s23))
for r in s23[:5]:
    print("   ", r.get('run_utc'), r['gate'].get('dd20'), r['gate'].get('by'), (r['gate'].get('мерено') or {}).get('кофа'), r['gate'].get('cell'))
