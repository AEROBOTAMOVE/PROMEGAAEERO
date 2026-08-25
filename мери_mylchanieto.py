# -*- coding: utf-8 -*-
"""
ИЗМЕРВАНЕ · ОТКЪДЕ ИДВА МЪЛЧАНИЕТО

Не теория. Броя от живия дневник какво реално е спряло всеки от ръновете.
"""
import json, io, collections, datetime as dt

r = [json.loads(l) for l in io.open("live/live_journal.jsonl", encoding="utf-8") if l.strip()]
n = len(r)
print("=" * 74)
print(f"ЖИВИЯТ ДНЕВНИК · {n} ръна · {r[0].get('run_utc')} → {r[-1].get('run_utc')}")
print("=" * 74)

# ── 1 · какъв е статусът на всеки рън ─────────────────────────────────────
ст = collections.Counter()
for x in r:
    s = x.get("status")
    s = s if isinstance(s, list) else [s]
    for q in s:
        ст[str(q)[:58]] += 1
print("\n1 · СТАТУС НА РЪНОВЕТЕ")
for k, v in ст.most_common(14):
    print(f"    {v:5d} · {v/n*100:5.1f}% · {k}")

# ── 2 · гейтът ────────────────────────────────────────────────────────────
print("\n2 · ГЕЙТЪТ (мереното правило)")
g = collections.Counter()
for x in r:
    q = x.get("gate")
    g[json.dumps(q, ensure_ascii=False)[:70] if not isinstance(q, str) else q[:70]] += 1
for k, v in g.most_common(10):
    print(f"    {v:5d} · {v/n*100:5.1f}% · {k}")

# ── 3 · бележките — там се пише КОЙ е спрял ───────────────────────────────
print("\n3 · БЕЛЕЖКИТЕ · кой праг колко пъти се обажда")
b = collections.Counter()
for x in r:
    for q in (x.get("notes") or []):
        b[str(q)[:66]] += 1
for k, v in b.most_common(22):
    print(f"    {v:5d} · {v/n*100:5.1f}% · {k}")

# ── 4 · колко карти реално са тръгнали ────────────────────────────────────
print("\n4 · КОЛКО КАРТИ СА ТРЪГНАЛИ")
try:
    s = [json.loads(l) for l in io.open("live/archive/sent_log.jsonl", encoding="utf-8") if l.strip()]
except Exception:
    import glob
    ff = glob.glob("live/**/sent*.jsonl", recursive=True)
    s = []
    for f in ff:
        s += [json.loads(l) for l in io.open(f, encoding="utf-8") if l.strip()]
    print(f"    (от {ff})")
вид = collections.Counter(str(x.get("kind") or x.get("вид") or "?")[:40] for x in s)
print(f"    общо пратени: {len(s)}")
for k, v in вид.most_common(16):
    print(f"      {v:5d} · {k}")

# ── 5 · ритъмът на самите ръна ────────────────────────────────────────────
print("\n5 · РИТЪМ · будилникът работи ли")
ч = []
for x in r:
    try:
        ч.append(dt.datetime.fromisoformat(str(x["run_utc"]).replace("Z", "")))
    except Exception:
        pass
ч.sort()
пр = [(ч[i + 1] - ч[i]).total_seconds() / 60 for i in range(len(ч) - 1)]
пр = [p for p in пр if 0 < p < 2000]
if пр:
    пр_с = sorted(пр)
    print(f"    интервал между ръна: медиана {пр_с[len(пр_с)//2]:.0f} мин · "
          f"най-дълъг {max(пр):.0f} мин")
    print(f"    дупки над 60 мин: {sum(1 for p in пр if p > 60)} / {len(пр)} = "
          f"{sum(1 for p in пр if p>60)/len(пр)*100:.1f}%")
    дни = collections.Counter(x.date() for x in ч)
    сед = collections.Counter()
    for d, c in дни.items():
        сед["ПНВТСРЧТПТСБНД"[d.weekday()*2:d.weekday()*2+2]] += c
    print("    ръна по ден от седмицата:", dict(сед))
