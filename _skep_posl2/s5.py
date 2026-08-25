# -*- coding: utf-8 -*-
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, BASE); os.chdir(BASE)
import live_bot as lb

stats = json.load(open("backtest_stats.json", encoding="utf-8"))   # ИСТИНСКИЯТ файл
print("stats ключове:", sorted(stats.keys())[:8], "· има fresh:", isinstance(stats.get("fresh"), dict))

комб = []
for посока in ("long","short"):
  for streak in (0,1,2,3,4,5):
    for shield in (False,True):
      for guard_n in (0,1):
        for fast in (None, 12.0):
          for dd in (None, -5.0, -25.0):
            комб.append((посока,streak,shield,guard_n,fast,dd))

for stale in (True, False):
    ок = 0
    for (п,s,sh,g,f,d) in комб:
        _, o = lb._advice_entry(п, s, stats, f, sh, g, sym="XAUUSD", stale_price=stale, dd20=d)
        ок += bool(o)
    print(f"stale_price={stale!s:5} → ok=True в {ок} от {len(комб)} комбинации")

_, ok = lb._advice_entry("long", 2, stats, None, False, 0, sym="XAUUSD", stale_price=True)
t,  ok2= lb._advice_entry("long", 2, stats, None, False, 0, sym="XAUUSD", stale_price=False)
print()
print("една и съща комбинация:  stale=True → ok =", ok, " | stale=False → ok =", ok2)
print("текстът при stale=True :", lb._advice_entry("long",2,stats,None,False,0,sym="XAUUSD",stale_price=True)[0])
