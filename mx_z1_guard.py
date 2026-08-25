# -*- coding: utf-8 -*-
import sys, json, io, pathlib, tempfile
sys.stdout.reconfigure(encoding="utf-8"); sys.argv = ["x"]
import live_bot as lb
spot_g = {"mid": 4365.20, "src": "twelve"}; spot_s = {"mid": 65.150, "src": "twelve"}

print("### s_long / s_short в реда «спрени днес» на КЪДЕ СМЕ")
for g in ({"date": "2026-08-21", "long": 2, "short": 0, "s_long": 0, "s_short": 0},
          {"date": "2026-08-21", "long": 0, "short": 0, "s_long": 2, "s_short": 0},
          {"date": "2026-08-21", "long": 0, "short": 0, "s_long": 0, "s_short": 3},
          {"date": "2026-08-21", "long": 2, "short": 2, "s_long": 0, "s_short": 0}):
    т = lb._status_msg([], None, None, None, spot_g, spot_s, None, None,
                       g, False, "2026-08-21", {})
    ред = [r for r in т.split("\n") if r.startswith("🛑")]
    print(f"  guard={ {k:v for k,v in g.items() if k!='date'} }")
    print(f"     -> {ред or 'НЯМА РЕД'}")
print()
print("### същият guard във вечерната равносметка")
tmp = pathlib.Path(tempfile.mkdtemp(prefix="mxz1c_"))
(tmp/"live_journal.jsonl").write_text("", encoding="utf-8")
(tmp/"sent_log.jsonl").write_text("", encoding="utf-8")
for g in ({"date":"x","long":2,"short":0,"s_long":0,"s_short":0},
          {"date":"x","long":0,"short":0,"s_long":2,"s_short":0},
          {"date":"x","long":2,"short":1,"s_long":1,"s_short":0}):
    т = lb._digest_msg(tmp, "2026-08-21", None, None, spot_g, spot_s, g)
    ред = [r for r in т.split("\n") if r.startswith("🛑")]
    print(f"  guard={ {k:v for k,v in g.items() if k!='date'} } -> {ред or 'НЯМА РЕД'}")
print()
print("### ПАЗАЧЪТ БЛОКИРА ПРИ >=2, а равносметката брои и ЕДИН стоп")
print("   _advice_entry прагът:", "guard_n >= 2  (live_bot.py:995)")
print("   _status_msg прагът: н >= 2  (live_bot.py:1924)")
print("   _digest_msg прагът: sum(...)  — БЕЗ праг, брои и 1")
