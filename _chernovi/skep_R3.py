# -*- coding: utf-8 -*-
import sys, io, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
print("=== live/meta.json ===")
m = json.load(open('live/meta.json', encoding='utf-8'))
for k in sorted(m):
    if isinstance(m[k], (str,int,float)) and len(str(m[k]))<40:
        print("   ", k, "=", m[k])
print("   reentry_ban в живия meta:", m.get("reentry_ban", "ГО НЯМА"))

print()
print("=== brain_journal: рън-час (UTC) срещу вътрешната 'date' ===")
двойки = []
for ln in open('live/brain_journal.jsonl', encoding='utf-8'):
    ln = ln.strip()
    if not ln: continue
    try: r = json.loads(ln)
    except Exception: continue
    ts = r.get("ts") or r.get("time") or r.get("utc")
    d  = r.get("date")
    if ts and d: двойки.append((str(ts), str(d)))
print("   записи с ts+date:", len(двойки))
изостав = collections.Counter()
for ts, d in двойки:
    изостав[(ts[:10], d)] += 1
for (ден_ран, d), n in sorted(изостав.items())[-25:]:
    from datetime import date as D
    a = D(*map(int, ден_ран.split('-'))); b = D(*map(int, d.split('-')))
    print(f"   рън {ден_ран}  ·  date={d}  ·  изоставане {(a-b).days} дни  ·  {n} рънa")
