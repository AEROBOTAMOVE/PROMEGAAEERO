# -*- coding: utf-8 -*-
"""Прави ВЕРНО копие на живия файл със СВАЛЕНА поправка (= състоянието v13.7),
за да проверя дали механизмът от твърдението изобщо се случва."""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(BASE, "live_bot.py"), encoding="utf-8").read()
нач = src.index('    if str(raw_spot.get("src") or "").startswith("paxg"):')
кр = src.index('    if old is None:', нач)
блок = src[нач:кр]
print("--- махам блок от %d знака (%d реда) ---" % (len(блок), блок.count("\n")))
нов = ('    if str(raw_spot.get("src") or "").startswith("paxg"):\n'
       '        return state.get(key, round(now_b, 3))\n')
out = src[:нач] + нов + src[кр:]
out = out.replace('VERSION = "v14.0"', 'VERSION = "v13.7-ПРЕДИ-ПОПРАВКАТА"', 1)
open(os.path.join(BASE, "_skep_paxg", "lb_pre.py"), "w", encoding="utf-8").write(out)
print("записан lb_pre.py, разлика в знаци:", len(src) - len(out))
