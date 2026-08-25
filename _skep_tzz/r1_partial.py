# -*- coding: utf-8 -*-
"""СКЕПТИК Р1: сам възпроизвеждам ЧАСТИЧНАТА загуба срещу v13.8 (ПРЕДИ фикса)."""
import sys, io, importlib, zoneinfo, datetime as _dt
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

_ORIG = zoneinfo.ZoneInfo

def патч(липсва):
    class Z:
        def __new__(cls, key):
            if key == липсва:
                raise zoneinfo.ZoneInfoNotFoundError(f"No time zone found with key {key}")
            return _ORIG(key)
    zoneinfo.ZoneInfo = Z

def мери(lb):
    съб = "2026-08-22T12:00:00"      # СЪБОТА
    cme = "2026-08-20T21:30:00"      # 17:30 NY (лятно = UTC-4)
    щит = "2026-08-20T12:40:00"      # 08:40 ET  → в щита 8:25-9:15
    из = {}
    из["market_closed_СЪБОТА"] = lb._market_closed(съб)
    из["cme_pause_17ч_NY"]     = lb._cme_pause(cme)
    из["in_shield"]            = lb._in_shield(щит)
    из["shield_label"]         = lb._shield_sofia_label()
    из["sofia_hour"]           = lb._sofia("2026-08-20T12:00:00")
    return из

# --- 1. здрава система ---
zoneinfo.ZoneInfo = _ORIG
import lb_pre as lb
здрав = мери(lb)
print("здрава система      :", здрав)

# --- 2. само America/New_York липсва ---
патч("America/New_York")
buf = io.StringIO(); стар = sys.stdout; sys.stdout = buf
счупен = мери(lb)
sys.stdout = стар
print("без America/New_York:", счупен)
print("отпечатано от бота  :", repr(buf.getvalue()))
print()
for к in здрав:
    if здрав[к] != счупен[к]:
        print(f"  РАЗЛИКА  {к}: {здрав[к]!r} -> {счупен[к]!r}")
zoneinfo.ZoneInfo = _ORIG
