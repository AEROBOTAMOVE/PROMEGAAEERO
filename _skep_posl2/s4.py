# -*- coding: utf-8 -*-
import sys, io, os, itertools
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, BASE); os.chdir(BASE)
import live_bot as lb, json

# МОЖЕ ЛИ ИЗОБЩО ДА СЕ ОТВОРИ СДЕЛКА В «бар−базис» СВЕТА (т.е. spot_g is None)?
# Сделка се отваря САМО при _adv_ok (ред 4132: if open_tr is None and new_dir and _adv_ok)
стат = {"long": {"n": 99, "wr": 0.7, "ev": 3.0}, "short": {"n": 99, "wr": 0.7, "ev": 3.0}}
ок_истина = []
n = 0
for посока in ("long","short"):
  for streak in (0,1,2,3,5):
    for shield in (False,True):
      for guard_n in (0,1):
        for fast in (None, 12.0):
          for dd in (None, -5.0):
            n += 1
            txt, ok = lb._advice_entry(посока, streak, стат, fast, shield, guard_n,
                                       sym="XAUUSD", stale_price=True, dd20=dd)
            ок_истина.append(ok)
print(f"_advice_entry(stale_price=True) пуснато {n} пъти по всички комбинации")
print("   брой ok=True :", sum(ок_истина), " → сделка може ли да се отвори без жив спот?",
      "ДА" if any(ок_истина) else "НЕ")
txt, ok = lb._advice_entry("long", 2, стат, None, False, 0, sym="XAUUSD", stale_price=True)
print("   примерен текст:", txt[:120])
print()
# КОНТРОЛА: същото, но със ЖИВ спот — трябва да има поне едно ДА, иначе тестът е сляп
ок2 = []
for посока in ("long","short"):
  for streak in (0,1,2,3,5):
    txt2, o2 = lb._advice_entry(посока, streak, стат, None, False, 0, sym="XAUUSD", stale_price=False)
    ок2.append(o2)
print("КОНТРОЛА (stale_price=False):", sum(ок2), "от", len(ок2), "казват ДА → тестът НЕ е сляп")
