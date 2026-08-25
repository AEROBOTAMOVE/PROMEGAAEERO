# -*- coding: utf-8 -*-
import sys, io, json, collections, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
rows=[json.loads(l) for l in open('live/live_journal.jsonl',encoding='utf-8') if l.strip()]
с_гейт=[r for r in rows if (r.get('gate') or {}).get('streak') is not None]
print("рънове ОБЩО:",len(rows)," с gate.streak:",len(с_гейт))
print("обхват на gate:", с_гейт[0]['run_utc'], "→", с_гейт[-1]['run_utc'])
print("обхват на журнала:", rows[0]['run_utc'], "→", rows[-1]['run_utc'])
c=collections.Counter(int(r['gate']['streak']) for r in с_гейт)
print()
print("=== разпределение на стрийка ===")
for k in sorted(c): print(f"   стрийк {k}: {c[k]:5d} рънa ({100*c[k]/len(с_гейт):5.1f}%)  {'⟵ ТУК забраната блокира' if 1<=k<=3 else ''}")
# колко рънa имат exits (затваряне) — чистещият клон
изх=collections.Counter()
for r in rows:
    e=r.get('exits')
    изх[bool(e)]+=1
print()
print("=== рънове със ЗАТВОРЕН изход (единственото място, където се викаше _reentry_ban) ===")
print("   с exits:", изх[True], " без exits:", изх[False],
      f" → чистещият клон е недостижим в {100*изх[False]/len(rows):.2f}% от рънoвете")
