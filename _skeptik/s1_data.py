# -*- coding: utf-8 -*-
"""СКЕПТИК ТЕСТ 1 — датата-ратчет.
Пуска ИСТИНСКИЯ main() на ДВЕ версии (преди/след поправката) с една и съща
поредица дни. Отровата влиза САМО през ДАННИТЕ (дневен бар с бъдеща дата),
никой не пипа meta.json на ръка.
Аргумент: път до live_bot.py"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import rig

BOT = sys.argv[1]
TAG = sys.argv[2]
POISON = sys.argv[3]          # дата на отровния дневен бар
rig.load(BOT, name="lb_" + TAG)
rig.patch()
import hashlib
print(f"### ВЕРСИЯ {TAG}  sha1={hashlib.sha1(Path(BOT).read_bytes()).hexdigest()[:16]}")
print(f"### отровен бар: {POISON}")

OUT = Path(__file__).parent / ("out_" + TAG)


def ден(now_iso, bar_end, етикет):
    rig.CFG.clear()
    rig.CFG.update(gold_end=bar_end, intra_end=now_iso[:10] + " 12:00", gold_px=4600.0)
    rig.set_now(now_iso)
    rig.run(OUT, argv_extra=["--send"])
    j = rig.last_journal(OUT)
    m = rig.meta(OUT)
    пулс = [s for s in j.get("status") or [] if "pulse" in str(s)]
    print(f"  {етикет:34s} bar={bar_end}  ботът смята date={j['date']:10s} "
          f"meta.date={m.get('date'):10s} pulse_14={str(m.get('pulse_14')):10s} "
          f"пулс={'ДА ' + str(пулс) if пулс else 'НЯМА'}")
    return j, m


print("--- ден 1: чисто, 2026-08-19 14:00 София (11:00 UTC) ---")
rig.fresh(OUT)
ден("2026-08-19T11:00:00", "2026-08-19", "контрола д1")
print("--- ден 2: ОТРОВА — Yahoo дава бъдещ бар ---")
ден("2026-08-20T11:00:00", POISON, "ОТРОВЕН рън")
print("--- следващите дни: Yahoo Е СЪВСЕМ ЗДРАВ ---")
for d in ("2026-08-21", "2026-08-24", "2026-08-25", "2026-08-26"):
    ден(d + "T11:00:00", d, "здрав " + d)
