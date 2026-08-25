# -*- coding: utf-8 -*-
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
m = json.load(open(D+"/live/meta.json", encoding="utf-8"))
print("meta.json ключове с 'basis':")
for k,v in m.items():
    if "basis" in k or "отказ" in k or "презакот" in k: print("   ", k, "=", v)

# трендът от живия дневник
import collections
дни = collections.OrderedDict()
цени = collections.OrderedDict()
n=0
for ред in open(D+"/live/live_journal.jsonl", encoding="utf-8", errors="replace"):
    ред=ред.strip()
    if not ред: continue
    try: o=json.loads(ред)
    except Exception: continue
    n+=1
    ts=str(o.get("ts") or o.get("time") or "")[:10]
    tb=o.get("tf_basis")
    if tb is None:
        tb=(o.get("diag") or {}).get("tf_basis") if isinstance(o.get("diag"),dict) else None
    if ts and tb is not None:
        дни.setdefault(ts,[]).append(float(tb))
    p=o.get("price") or o.get("gold") or (o.get("diag") or {}).get("price")
    if ts and isinstance(p,(int,float)): цени.setdefault(ts,[]).append(float(p))
print("\nпрочетени записа:", n, "| дни с tf_basis:", len(дни))
for d in list(дни)[-14:]:
    v=дни[d]; c=цени.get(d)
    print(f"  {d}  tf_basis посл.={v[-1]:+8.3f}  n={len(v):>4}" +
          (f"  цена посл.={c[-1]:.1f}  таван_3%={0.03*c[-1]:.1f}" if c else ""))
