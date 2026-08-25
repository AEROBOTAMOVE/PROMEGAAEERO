# -*- coding: utf-8 -*-
import sys, io, json, collections, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
D = datetime.date
def d(s): return D(*map(int, str(s)[:10].split('-')))

лаг = collections.Counter(); буден = collections.Counter()
дни = {}
for ln in open('live/live_journal.jsonl', encoding='utf-8'):
    ln = ln.strip()
    if not ln: continue
    try: r = json.loads(ln)
    except Exception: continue
    ru, dt = r.get("run_utc"), r.get("date")
    if not (ru and dt): continue
    L = (d(ru) - d(dt)).days
    wd = d(ru).weekday()           # 0=пон … 5=съб 6=нед
    лаг[L] += 1
    буден[(L, wd)] += 1
    дни.setdefault(d(ru), set()).add(dt)

общо = sum(лаг.values())
print(f"=== ИЗОСТАВАНЕ 'date' (бар от Yahoo) спрямо деня на рънa · {общо} ИСТИНСКИ рънa ===")
for L in sorted(лаг):
    print(f"   изоставане {L} дни : {лаг[L]:5d} рънa  ({100*лаг[L]/общо:5.1f}%)")

имена = ['пон','вто','сря','чет','пет','съб','нед']
print()
print("=== САМО РАБОТНИ ДНИ (пон-пет) — там, където ботът търгува ===")
раб = {k: v for k, v in буден.items() if k[1] <= 4}
т = sum(раб.values())
по_лаг = collections.Counter()
for (L, wd), n in раб.items(): по_лаг[L] += n
for L in sorted(по_лаг):
    print(f"   изоставане {L} дни : {по_лаг[L]:5d} рънa ({100*по_лаг[L]/т:5.1f}%)")
print()
print("=== работни дни с изоставане ≥1 (разбито по ден от седмицата) ===")
for (L, wd), n in sorted(раб.items()):
    if L >= 1:
        print(f"   {имена[wd]} · изоставане {L} : {n} рънa")
print()
print("=== календарни дни, в които 'date' НЕ Е мръднала спрямо предишния ден ===")
пред = None
for ден in sorted(дни):
    тек = sorted(дни[ден])
    ако = " ⟵ ЗАМРЪЗНАЛА" if пред is not None and тек == пред else ""
    if ако or (пред is not None and set(тек) & set(пред)):
        print(f"   {ден} ({имена[ден.weekday()]}) date={тек}{ако}")
    пред = тек
