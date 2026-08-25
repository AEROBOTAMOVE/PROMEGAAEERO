# -*- coding: utf-8 -*-
import sys, io, json, datetime, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def T(s): return datetime.datetime.strptime(str(s)[:16], "%Y-%m-%dT%H:%M")

rows = []
for ln in open('live/live_journal.jsonl', encoding='utf-8'):
    ln = ln.strip()
    if not ln: continue
    try: r = json.loads(ln)
    except Exception: continue
    if r.get("run_utc") and r.get("date"): rows.append((T(r["run_utc"]), str(r["date"])))
rows.sort()

# за всяка календарна дата на рънa: докога 'date' е още вчерашна
по_ден = collections.defaultdict(list)
for ts, d in rows: по_ден[ts.date()].append((ts, d))

print("=== КОЛКО ДЪЛГО 'date' е още ВЧЕРАШНА след полунощ UTC ===")
print("    (guard.json вече се е нулирал по календар; замразената причина — не)")
дълж = []
for ден in sorted(по_ден):
    сп = по_ден[ден]
    стари = [ts for ts, d in сп if str(d) < str(ден)]
    ако = [ts for ts, d in сп if str(d) == str(ден)]
    if стари and ако:
        край = min(ако); нач = min(стари)
        ч = (край - нач).total_seconds()/3600
        дълж.append(ч)
        print(f"   {ден} {ден.strftime('%a')}: вчерашна от {нач:%H:%M} до {край:%H:%M} UTC = {ч:5.2f} ч · {len(стари)} рънa")
    elif стари and not ако:
        ч = (max(стари)-min(стари)).total_seconds()/3600
        дълж.append(ч)
        print(f"   {ден} {ден.strftime('%a')}: ЦЕЛИЯТ ДЕН вчерашна ({len(стари)} рънa, {ч:.2f} ч) — НЕ мръдна изобщо")

if дълж:
    дълж.sort()
    n = len(дълж)
    print()
    print(f"   n={n} дни · медиана {дълж[n//2]:.2f} ч · мин {дълж[0]:.2f} ч · макс {дълж[-1]:.2f} ч")

# най-дългата непрекъсната серия с една и съща 'date'
print()
print("=== НАЙ-ДЪЛГАТА непрекъсната серия с ЕДНА И СЪЩА 'date' ===")
best = None; тек_d = None; нач = None; посл = None; бр = 0
серии = []
for ts, d in rows:
    if d != тек_d:
        if тек_d is not None: серии.append((тек_d, нач, посл, бр))
        тек_d, нач, бр = d, ts, 0
    посл = ts; бр += 1
серии.append((тек_d, нач, посл, бр))
серии.sort(key=lambda x: (x[2]-x[1]).total_seconds(), reverse=True)
for d, a, b, n in серии[:6]:
    print(f"   date={d}: от {a:%Y-%m-%d %H:%M} до {b:%Y-%m-%d %H:%M} = {(b-a).total_seconds()/3600:6.2f} ч · {n} рънa")
