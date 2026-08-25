# -*- coding: utf-8 -*-
"""СКЕПТИК Р6: КОНТРОЛА: чупя НЕПОЛЗВАНА зона на находката — липсва САМО Europe/Berlin,
   Europe/Sofia работи. Твърди се «рънът стига до пращането». Проверявам."""
import sys, zoneinfo, traceback
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "_skep_tzz"); sys.path.insert(0, ".")
import lb_pre

_ORIG = zoneinfo.ZoneInfo
class Частична:
    def __new__(cls, key):
        if key == "Europe/Berlin":
            raise zoneinfo.ZoneInfoNotFoundError("No time zone found with key Europe/Berlin")
        return _ORIG(key)

_ист = lb_pre._outbox_flush
ПРАТЕНО = []
def _следен(*a, **k):
    ПРАТЕНО.append(1); return _ист(*a, **k)
lb_pre._outbox_flush = _следен

zoneinfo.ZoneInfo = Частична
sys.argv = ["live_bot.py", "--stats", "backtest_stats.json", "--out", "_skep_tzz/out"]
код = "0 (мина докрай)"
try:
    lb_pre.main()
except SystemExit as e:
    код = f"SystemExit {e.code}"
except Exception as e:
    код = f"ИЗКЛЮЧЕНИЕ {type(e).__name__}: {e}"
    tb = traceback.extract_tb(sys.exc_info()[2])
    вътре = [f for f in tb if "lb_pre" in f.filename]
    if вътре:
        print(f"\n>>> умря на lb_pre.py:{вътре[-1].lineno}  ->  {вътре[-1].line}")
finally:
    zoneinfo.ZoneInfo = _ORIG

print("\n=== РАВНОСМЕТКА (само Europe/Berlin липсва) ===")
print("изход                :", код)
print("_outbox_flush извикан:", len(ПРАТЕНО), "пъти")
print("ТВЪРДЕНИЕТО беше: «рънът стига до пращането»")
