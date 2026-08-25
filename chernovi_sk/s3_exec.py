import sys, os, json, textwrap
sys.path.insert(0, os.getcwd())
import live_bot as lb
import pandas as pd

src = open('live_bot.py', encoding='utf-8').read().splitlines()
i0 = next(i for i, l in enumerate(src) if 'BROYACH'.lower() in l.lower() or 'СУХИТЕ РЪНА' in l)
i1 = next(i for i, l in enumerate(src) if i > i0 and '_сухо_карта' in l and 'insert(0' in l)
block = textwrap.dedent("\n".join(src[i0:i1 + 1]))
print('=== IZPYLNYAVAM ISTINSKIYA blok live_bot.py redove %d-%d ===' % (i0 + 1, i1 + 1))
code = compile(block, '<blok-ot-live_bot>', 'exec')


def run(spot_g, meta, rejected, now, weekend=False):
    ns = {'СУХИ_МАКС': lb.СУХИ_МАКС, 'СУХИ_ПОВТОР_Ч': lb.СУХИ_ПОВТОР_Ч,
          '_сухо_msg': lb._сухо_msg, 'pd': pd, 'json': json,
          'spot_g': spot_g, 'spot_rejected_g': rejected, 'meta': meta,
          'now_utc': now, 'weekend': weekend, 'notes': [], 'new_msgs': [],
          '_сухо_карта': None}
    exec(code, ns)
    return ns


# SCENARIY = REALNATA AVARIYA 19.08: spot rejected ot sanitito, run na 5 min
meta = {}
t0 = pd.Timestamp('2026-08-19T13:16')
fired = []
for k in range(40):
    t = (t0 + pd.Timedelta(minutes=5 * k)).isoformat(timespec='minutes')
    ns = run(None, meta, True, t)
    meta = ns['meta']
    if ns['new_msgs']:
        fired.append((k + 1, t))
        if len(fired) == 1:
            print('>>> KARTA plamna na SUH RUN #%d (%s), suhi_ryna=%d' % (k + 1, t, meta['сухи_ръна']))
            print(ns['new_msgs'][0][1])
            print()
print('paleniya v 40 poredni suhi ryna:', len(fired), fired)
print('notes na 40-ya run:', ns['notes'])
print()

# VYZSTANOVYAVANE: pyrvata zhiva cena nulira li broyacha?
ns = run(4621.25, meta, False, '2026-08-19T16:40')
meta = ns['meta']
print('sled ZHIVA cena: suhi_ryna =', meta['сухи_ръна'], '| notes:', ns['notes'])
print('suhi_ot iztrit:', 'сухи_от' not in meta)

# pali li PAK sled vyzstanovyavane (t.e. ne se zaklyuchva sled edno palene)?
for k in range(30):
    t = (pd.Timestamp('2026-08-19T16:45') + pd.Timedelta(minutes=5 * k)).isoformat(timespec='minutes')
    ns = run(None, meta, False, t)
    meta = ns['meta']
    if ns['new_msgs']:
        print('PAK pali na suh run #%d (%s) -> pazachyt NE se izrazhda' % (k + 1, t))
        break
else:
    print('NE pali povtorno -> POTENCIALNO ZAKLYUCHVANE')

# UIKEND: broyachyt spi li?
ns = run(None, dict(meta), False, '2026-08-23T10:00', weekend=True)
print('uikend run -> suhi_ryna =', ns['meta'].get('сухи_ръна'), '(ne raste, tova e vyarno)')
