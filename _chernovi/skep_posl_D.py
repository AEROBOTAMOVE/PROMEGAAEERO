# -*- coding: utf-8 -*-
"""СКЕПТИК·ПОСЛЕДИЦА — стъпка 4: ИМА ЛИ ЖИВО ДОКАЗАТЕЛСТВО, че клонът е палил?"""
import sys, io, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
rows = []
for line in open("live/live_journal.jsonl", encoding="utf-8"):
    line = line.strip()
    if not line: continue
    try: rows.append(json.loads(line))
    except Exception: pass
print("ръна в live_journal.jsonl:", len(rows))
print("първи:", rows[0].get("run_utc"), " последен:", rows[-1].get("run_utc"))

имащи = [r for r in rows if r.get("tf_basis") is not None]
print("ръна с записан tf_basis:", len(имащи))
# tf_basis може да е число или речник
пример = имащи[-1]["tf_basis"] if имащи else None
print("вид на полето:", type(пример).__name__, "->", пример)

def g(r):
    v = r.get("tf_basis")
    if isinstance(v, dict): return v.get("g", v.get("tf_basis_g"))
    if isinstance(v, (list, tuple)): return v[0]
    return v

сер = [(r.get("run_utc"), g(r)) for r in имащи if g(r) is not None]
print("ръна с числова стойност:", len(сер))
print("първа стойност:", сер[0], " последна:", сер[-1])
print("min/max:", min(x[1] for x in сер), max(x[1] for x in сер))
# по дни
по_дни = collections.OrderedDict()
for t, v in сер:
    по_дни.setdefault(str(t)[:10], []).append(v)
for d, vs in по_дни.items():
    print(f"  {d}: n={len(vs):4d} първа={vs[0]:+9.3f} последна={vs[-1]:+9.3f} различни={len(set(vs))}")

# най-дълга серия БЕЗ промяна
най = cur = 1; къде = None
for i in range(1, len(сер)):
    if сер[i][1] == сер[i-1][1]:
        cur += 1
        if cur > най: най, къде = cur, сер[i][0]
    else:
        cur = 1
print("най-дълга поредица с НЕПРОМЕНЕН tf_basis:", най, "ръна, край", къде)

# бележки за контрактния базис
бр = collections.Counter()
for r in rows:
    for n in (r.get("notes") or []):
        if "контрактен базис" in n or "контрактният базис" in n:
            бр[n[:70]] += 1
print("бележки за контрактния базис в ЦЕЛИЯ дневник:", sum(бр.values()))
for k, v in бр.most_common(10): print("   ", v, "×", k)
