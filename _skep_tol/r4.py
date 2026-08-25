import json, collections, pathlib, re
p = pathlib.Path(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/live/live_journal.jsonl")
recs=[json.loads(l) for l in p.read_text(encoding="utf-8",errors="replace").splitlines() if l.strip()]
zdravi=[r for r in recs if str(r.get("date","")) < "2026-08-19"]
bolni =[r for r in recs if str(r.get("date","")) >= "2026-08-19"]
print(f"ЗДРАВИ (<19.08): {len(zdravi)} ръна | отрязани: {sum(1 for r in zdravi if r.get('spot_rejected'))} "
      f"({100*sum(1 for r in zdravi if r.get('spot_rejected'))/max(1,len(zdravi)):.1f}%)")
print(f"БОЛНИ  (>=19.08): {len(bolni)} ръна | отрязани: {sum(1 for r in bolni if r.get('spot_rejected'))} "
      f"({100*sum(1 for r in bolni if r.get('spot_rejected'))/max(1,len(bolni)):.1f}%)")
print("\n=== АГЕНТЪТ твърди: здрави=3532 ръна, отрязани=375 (10.6%) ===")
# извади РАЗЛИКАТА и ДОПУСКА от бележката 'живата цена отрязана'
rx=re.compile(r"разминава с ([\d.]+)\$ при допуск ([\d.]+)\$")
d=[]
for r in recs:
    for n in (r.get("notes") or []):
        m=rx.search(str(n))
        if m: d.append((r.get("date"), float(m.group(1)), float(m.group(2))))
print("\nбележки със ЗАПИСАНА следа (разлика+допуск):", len(d))
if d:
    dz=[x for x in d if str(x[0])<"2026-08-19"]
    print("  от тях на здрави дни:", len(dz))
    allow=collections.Counter(round(x[2],2) for x in d)
    print("  разпределение на ДОПУСКА:", allow.most_common(8))
    import statistics as st
    r_=[x[1] for x in d]
    r_.sort()
    print(f"  разлика: p10 {r_[len(r_)//10]:.2f} p50 {r_[len(r_)//2]:.2f} p90 {r_[len(r_)*9//10]:.2f} max {max(r_):.2f}")
    # колко биха минали при НОВИЯ допуск (0.40% от бара)?
    import sys; sys.path.insert(0,r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
    import live_bot as lb
    passed=0; tot=0
    for r in recs:
        for n in (r.get("notes") or []):
            m=rx.search(str(n))
            if not m: continue
            tot+=1
            bar=r.get("bar")
            if bar and float(m.group(1)) <= lb._spot_tol(bar): passed+=1
    print(f"\n  ПУСНАТО през ТЕКУЩИЯ _spot_tol: биха минали {passed} от {tot} "
          f"({100*passed/max(1,tot):.1f}%) — дефектът вече е поправен")
