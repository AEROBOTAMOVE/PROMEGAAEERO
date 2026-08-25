# -*- coding: utf-8 -*-
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))
os.environ.setdefault("TELEGRAM_TOKEN","x"); os.environ.setdefault("TELEGRAM_CHAT_ID","1")
import live_bot as LB
f, v = LB._reentry_ban, LB._reentry_verdict
meta = {}; guard = {"date":"2026-08-20","long":2,"short":0}

def stypka(етикет, ден_карти, date):
    global guard
    if guard.get("date") != ден_карти:
        guard = {"date": ден_карти, "long": 0, "short": 0}
    ст = meta.get("reentry_ban")
    if ст and str(ст.get("date","")) != str(date):
        meta.pop("reentry_ban", None)
    забранен, защо = f(meta, "long", 2, ден=date)
    ако_нямаше_бан = v("long", 2, False, guard.get("long", 0))
    if забранен:
        реално = (False, защо)
    else:
        реално = v("long", 2, False, guard.get("long", 0))
        if not реално[0]:
            f(meta, "long", 2, why=реално[1], set_it=True, ден=date)
    print(f"{етикет:34s} guard.long={guard['long']} | БАН={'ДА' if забранен else 'не'} "
          f"| реално пуска={реално[0]} | БЕЗ бана щеше={ако_нямаше_бан[0]}")

print("Sofia=UTC+3 · календарният ден се сменя в 21:00 UTC · дневният бар — в 04:11 UTC (мерено)\n")
stypka("20.08 18:00 UTC (2 стопа)", "2026-08-20", "2026-08-20")
stypka("20.08 21:30 UTC = Sofia 21.08 00:30", "2026-08-21", "2026-08-20")
stypka("21.08 02:00 UTC (Sofia 05:00)",       "2026-08-21", "2026-08-20")
stypka("21.08 04:06 UTC — последен стар бар",  "2026-08-21", "2026-08-20")
stypka("21.08 04:11 UTC — барът се смени",     "2026-08-21", "2026-08-21")
print("\nзапис накрая:", json.dumps(meta.get("reentry_ban"), ensure_ascii=False))
