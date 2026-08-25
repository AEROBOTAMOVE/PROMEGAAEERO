# -*- coding: utf-8 -*-
"""СКЕПТИК Р5: ЦЕЛИЯТ бот v13.8 с МЪРТВА база от часови зони. Праща ли, или гърми?"""
import sys, zoneinfo, traceback
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "_skep_tzz")
sys.path.insert(0, ".")

import lb_pre

_ORIG = zoneinfo.ZoneInfo
class Мъртва:
    def __new__(cls, key):
        raise zoneinfo.ZoneInfoNotFoundError(f"No time zone found with key {key}")

# следа: извикан ли е изобщо изходът към Telegram
_истински_flush = lb_pre._outbox_flush
ПРАТЕНО = []
def _следен_flush(*a, **k):
    ПРАТЕНО.append((a, k))
    return _истински_flush(*a, **k)
lb_pre._outbox_flush = _следен_flush

zoneinfo.ZoneInfo = Мъртва
sys.argv = ["live_bot.py", "--stats", "backtest_stats.json", "--out", "_skep_tzz/out"]
код = 0
try:
    lb_pre.main()
except SystemExit as e:
    код = e.code
except Exception as e:
    код = "ИЗКЛЮЧЕНИЕ"
    print("\n>>> ГРЪМНА:", type(e).__name__, e)
    tb = traceback.extract_tb(sys.exc_info()[2])
    print(">>> последен ред в live_bot:", [f"{f.filename.split(chr(92))[-1]}:{f.lineno} {f.line}" for f in tb if "lb_pre" in f.filename][-1:])
finally:
    zoneinfo.ZoneInfo = _ORIG

print(f"\n=== РАВНОСМЕТКА ===")
print("изход:", код)
print("_outbox_flush извикан:", len(ПРАТЕНО), "пъти  <- 0 значи НИЩО не е пратено")
