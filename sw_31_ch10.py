# -*- coding: utf-8 -*-
import sys, json, pathlib, tempfile, datetime as dt
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,".")
import importlib.util
spec=importlib.util.spec_from_file_location("ab","audit_bot.py")
ab=importlib.util.module_from_spec(spec); sys.modules["ab"]=ab
sys.argv=["audit_bot.py"]
spec.loader.exec_module(ab)

live=pathlib.Path(tempfile.mkdtemp())
t0=dt.datetime(2026,8,10,0,0)
карти=[]; цени=[]
for i in range(20):
    t=t0+dt.timedelta(hours=5*i)
    праща=(i%2==0)                      # ПРАТЕНИТЕ ще удрят стоп, непратените — цел
    карти.append({"utc":t.isoformat(timespec="minutes"),"рамка":"15м","посока":"LONG",
                  "степен":"✅ ГОТОВ","точки":15,"вход":3300.0,"стоп":3290.0,"цел":3310.0,
                  "базис":0.0,"праща":праща})
    for m in range(0,241,5):
        p=3300.0
        if m==10: p = 3289.0 if праща else 3311.0
        цени.append({"run_utc":(t+dt.timedelta(minutes=m)).isoformat(timespec="minutes"),
                     "spot":p,"basis":0.0})
(live/"brain_journal.jsonl").write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in карти),encoding="utf-8")
(live/"live_journal.jsonl").write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in цени),encoding="utf-8")

ab.A.rows.clear()
R,Y,L=ab.check_mozak(live)
print("--- редове от check_mozak ---"); [print("  ",x) for x in L]
print("--- A.rows (това чете диспечерът) ---")
for r in ab.A.rows: print("  ",r["level"],r["code"],r["name"],"|",r["detail"],"|",r["fix"])
print("--- жълти в отчета ---")
for r in ab.A.yellows: print("  ⚠️",r["code"],r["name"],"—",r["detail"])
print("Ч10 присъства в A.rows:", any(r["code"]=="Ч10" for r in ab.A.rows))
