# -*- coding: utf-8 -*-
"""СКЕПТИК Р8: ФИКСЪТ вече е в живия v14.2. Обажда ли се наистина?"""
import sys, zoneinfo, traceback
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
import live_bot as lb
print("версия:", lb.VERSION)

_ORIG = zoneinfo.ZoneInfo
class Частична:
    def __new__(cls, key):
        if key == "America/New_York":
            raise zoneinfo.ZoneInfoNotFoundError("No time zone found with key America/New_York")
        return _ORIG(key)

_ист = lb._outbox_flush
ПРАТЕНО = []
def _следен(*a, **k):
    ПРАТЕНО.append(1); return _ист(*a, **k)
lb._outbox_flush = _следен

zoneinfo.ZoneInfo = Частична
sys.argv = ["live_bot.py", "--stats", "backtest_stats.json", "--out", "_skep_tzz/out"]
import io
буф = io.StringIO(); истински = sys.stdout
sys.stdout = буф
код = "0 (мина докрай)"
try:
    lb.main()
except SystemExit as e:
    код = f"SystemExit {e.code}"
except Exception as e:
    код = f"ИЗКЛЮЧЕНИЕ {type(e).__name__}: {e}"
finally:
    sys.stdout = истински
    zoneinfo.ZoneInfo = _ORIG

изход = буф.getvalue()
print("изход на бота        :", код)
print("знамето вдигнато ли е:", repr(lb.ЧАСОВИ_ЗОНИ_СЧУПЕНИ))
print("_outbox_flush        :", len(ПРАТЕНО), "пъти")
print("бележката ОТПЕЧАТАНА :", "ЛИПСВА — уикенд-пазачът" in изход)
print("последни редове от бота:")
for r in изход.strip().splitlines()[-4:]:
    print("   ", r)
