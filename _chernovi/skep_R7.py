# -*- coding: utf-8 -*-
import sys, io, json, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def T(s): return datetime.datetime.strptime(str(s)[:16], "%Y-%m-%dT%H:%M")

rows = []
for ln in open('live/live_journal.jsonl', encoding='utf-8'):
    ln = ln.strip()
    if not ln: continue
    r = json.loads(ln)
    g = r.get("gate") or {}
    if r.get("run_utc") and g.get("dir") is not None and g.get("streak") is not None:
        rows.append((T(r["run_utc"]), g["dir"], int(g["streak"])))
rows.sort()
print(f"рънове с (посока,стрийк): {len(rows)}")

серии = []; тек = None; нач = None; посл = None; бр = 0
for ts, d, s in rows:
    if (d, s) != тек:
        if тек is not None: серии.append((тек, нач, посл, бр))
        тек, нач, бр = (d, s), ts, 0
    посл = ts; бр += 1
серии.append((тек, нач, посл, бр))

print()
print("=== КОЛКО ДЪЛГО (посока,стрийк) стои НЕПРОМЕНЕН — това е ЕДИНСТВЕНОТО,")
print("    което сваляше забраната преди фикса ===")
блок = [(k,a,b,n) for k,a,b,n in серии if 1 <= k[1] <= 3]   # само тези, които РЕАЛНО блокират
блок.sort(key=lambda x: (x[2]-x[1]).total_seconds(), reverse=True)
print(f"    серии, в които стрийкът е 1..3 (забраната наистина блокира): {len(блок)}")
for k, a, b, n in блок[:10]:
    ч = (b-a).total_seconds()/3600
    print(f"   {k[0]:5s} стрийк {k[1]} : {a:%m-%d %H:%M} → {b:%m-%d %H:%M} = {ч:7.2f} ч ({ч/24:5.2f} дни) · {n} рънa")
дълж = sorted((b-a).total_seconds()/3600 for k,a,b,n in блок)
if дълж:
    n=len(дълж)
    print()
    print(f"   медиана {дълж[n//2]:.2f} ч · 90-и персентил {дълж[int(n*0.9)]:.2f} ч · МАКС {дълж[-1]:.2f} ч = {дълж[-1]/24:.2f} дни")
