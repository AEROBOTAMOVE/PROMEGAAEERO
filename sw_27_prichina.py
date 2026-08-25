# -*- coding: utf-8 -*-
import sys, json, pathlib, tempfile, pandas as pd
sys.argv=["x"]; import live_bot as lb
sys.stdout.reconfigure(encoding='utf-8')
src=open("live_bot.py",encoding="utf-8").read().splitlines()
блок="\n".join(l[12:] if l[:12].strip()=="" else l for l in src[3644:3707])
out=pathlib.Path(tempfile.mkdtemp())
def s(n,t,r,f="15м"):
    return {"рамка":f,"посока":"long","лонг":True,"степен":"⚡","точки":t,"ранг":r,
            "повод":"свип","ниво":3300.0,"вход":3300.0,"стоп":3290.0,"цел":3320.0,"праща":True,"име":n}
_setups=[s("A",20,5),s("B",18,4),s("E",15,5),s("C",16,3),s("D",10,2)]
g=dict(vars(lb)); g.update(dict(
    _setups=_setups, _bstate={"_последна_карта":{"utc":"2026-08-19T09:58","ранг":3}},
    now_utc="2026-08-19T10:00", notes=[], out=out, regime={"streaks":{}},
    basis_g=0.0, pd=pd, json=json, sorted=sorted, float=float, int=int, len=len, round=round))
exec(блок, g)
print("--- какво стана със сетъпите ---")
for x in _setups:
    print(f"  {x['име']} точки={x['точки']:>2} ранг={x['ранг']} праща={str(x['праща']):5} причина={x.get('застудяване')}")
print("--- дневникът brain_journal.jsonl ---")
for l in (out/"brain_journal.jsonl").read_text(encoding="utf-8").splitlines():
    r=json.loads(l); print(f"  точки={r['точки']:>2} праща={str(r['праща']):5} застудяване={r['застудяване']}")
print("непратени БЕЗ причина в дневника:",
      sum(1 for l in (out/"brain_journal.jsonl").read_text(encoding='utf-8').splitlines()
          for r in [json.loads(l)] if not r["праща"] and not r["застудяване"]))
print("notes:",g["notes"])
