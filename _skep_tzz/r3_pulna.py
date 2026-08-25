# -*- coding: utf-8 -*-
"""СКЕПТИК Р3: ПЪЛНАТА загуба (реалистичната) — шумна ли е наистина?"""
import sys, zoneinfo, importlib.util, os
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding="utf-8")

_ORIG = zoneinfo.ZoneInfo

print("=== как се намират зоните на ТАЗИ машина ===")
print("TZPATH:", zoneinfo.TZPATH)
spec = importlib.util.find_spec("tzdata")
print("пакет tzdata инсталиран:", bool(spec), spec.origin if spec else "")
if spec:
    d = os.path.dirname(spec.origin)
    зони = []
    for корен, _, файлове in os.walk(d):
        зони += [os.path.join(корен, f) for f in файлове if not f.endswith((".py", ".pyc"))]
    print("файлове със зони в пакета tzdata:", len(зони))
    print("  America/New_York присъства:", os.path.exists(os.path.join(d, "zoneinfo", "America", "New_York")))
    print("  Europe/Sofia    присъства:", os.path.exists(os.path.join(d, "zoneinfo", "Europe", "Sofia")))

print("\n=== ПЪЛНА загуба: гърми ли редът, който няма try (ред 4100) ===")
class Мъртва:
    def __new__(cls, key):
        raise zoneinfo.ZoneInfoNotFoundError(f"No time zone found with key {key}")
zoneinfo.ZoneInfo = Мъртва
try:
    # ТОЧНИЯТ израз от ред 4100 на v13.8
    from zoneinfo import ZoneInfo
    sof_now = datetime.now(timezone.utc).astimezone(ZoneInfo("Europe/Sofia"))
    print("  НЕ гръмна ->", sof_now)
except Exception as e:
    print(f"  ГРЪМНА: {type(e).__name__}: {e}")
    print("  ред 4100 е ПРЕДИ _outbox_flush (ред 4414) -> нищо не се праща, изход 1")
zoneinfo.ZoneInfo = _ORIG
