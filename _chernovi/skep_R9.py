# -*- coding: utf-8 -*-
import sys, io, json, ast, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
src = open('live_bot.py', encoding='utf-8').read()
tree = ast.parse(src)
ns = {}
for n in ast.walk(tree):
    if isinstance(n, ast.FunctionDef) and n.name == '_reentry_ban':
        exec(compile(ast.get_source_segment(src, n), 'lb', 'exec'), ns)
ban = ns['_reentry_ban']

# ── дали чистещият блок е наистина БЕЗУСЛОВЕН (отстъп 4 = тяло на функцията) ──
редове = src.splitlines()
i = next(k for k,l in enumerate(редове) if 'if meta.get("reentry_ban"):' in l)
print(f"чистещ блок на ред {i+1}, отстъп {len(редове[i])-len(редове[i].lstrip())} "
      f"(4 = право в тялото на main → БЕЗУСЛОВЕН)")
j = next(k for k,l in enumerate(редове) if l.strip().startswith('if closed_kinds and actionable'))
print(f"'if closed_kinds' на ред {j+1}, отстъп {len(редове[j])-len(редове[j].lstrip())}")
print(f"чистенето е ПРЕДИ closed_kinds: {i < j}")

# ── истински (run_utc, date) двойки от продукцията ──
rows = []
for ln in open('live/live_journal.jsonl', encoding='utf-8'):
    ln = ln.strip()
    if not ln: continue
    r = json.loads(ln)
    if r.get('run_utc') and r.get('date'): rows.append((r['run_utc'], str(r['date'])))
rows.sort()

print()
print("═══ ОСТАТЪКЪТ · чистенето виси на 'date' (бар от Yahoo), не на календара ═══")
print("Забрана, сложена на 2026-08-20 (стрийк 2, long). Пускам ИСТИНСКИТЕ рънове от 21.08:")
meta = {}
ban(meta, 'long', 2, why='2 стопа днес в тази посока — спирам до утре', set_it=True, ден='2026-08-20')
блокирани = 0; първо_свободно = None
for ru, dt in rows:
    if not ru.startswith('2026-08-21'): continue
    з, защо = ban(meta, 'long', 2, ден=dt)
    if з:
        блокирани += 1
        if блокирани <= 3 or блокирани % 20 == 0:
            print(f"   {ru} UTC · date={dt} → ЗАБРАНЕН: «{защо}»")
    else:
        първо_свободно = ru
        print(f"   {ru} UTC · date={dt} → СВОБОДЕН (забраната падна)")
        break
print(f"\n   блокирани рънове на 21.08 СЛЕД полунощ: {блокирани}")
print(f"   забраната пада чак в: {първо_свободно} UTC")
h0 = datetime.datetime.strptime(rows[0][0][:16], '%Y-%m-%dT%H:%M')
if първо_свободно:
    a = datetime.datetime.strptime('2026-08-21T00:00', '%Y-%m-%dT%H:%M')
    b = datetime.datetime.strptime(първо_свободно[:16], '%Y-%m-%dT%H:%M')
    print(f"   ⇒ «до утре» се проточва {(b-a).total_seconds()/3600:.2f} ч в новото денонощие")
print()
print("   а guard.json се нулира по СОФИЙСКИ календар (21:00 UTC предния ден)")
print(f"   ⇒ разминаване guard=0 стопа, но замразената причина още казва «2 стопа днес»:")
print(f"     от 2026-08-20 21:00 UTC до {първо_свободно} UTC ≈ "
      f"{(datetime.datetime.strptime(първо_свободно[:16],'%Y-%m-%dT%H:%M')-datetime.datetime.strptime('2026-08-20T21:00','%Y-%m-%dT%H:%M')).total_seconds()/3600:.2f} ч")
