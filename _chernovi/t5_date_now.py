# -*- coding: utf-8 -*-
"""ПОВТОРЕНИЕ на ратчета срещу ТЕКУЩИЯ live_bot.py."""
import sys, json, hashlib
sys.path.insert(0, r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/_chernovi")
import harness as H
print("live_bot.py sha1:", hashlib.sha1(open(H.BASE/"live_bot.py","rb").read()).hexdigest())
H.patch()
sb = H.fresh("_chernovi/sand_date2")
H.set_now("2026-08-20T11:00")
H.CFG.update(gold_end="2026-12-31", intra_end="2026-08-20 10:55", gold_px=4600.0, spot_mid=4600.0)
H.run(sb, ["--send"])
r = H.last_journal(sb); m = json.load(open(sb/"meta.json", encoding="utf-8"))
print(f"рун 1 (Yahoo дава 2026-12-31): date={r['date']} status={r['status']} meta.pulse_14={m.get('pulse_14')}")
H.set_now("2026-08-21T11:00")
H.CFG.update(gold_end="2026-08-21", intra_end="2026-08-21 10:55")
H.run(sb, ["--send"])
r = H.last_journal(sb); m = json.load(open(sb/"meta.json", encoding="utf-8"))
g = json.load(open(sb/"guard.json", encoding="utf-8"))
print(f"рун 2 (Yahoo дава 2026-08-21): date={r['date']} status={r['status']}")
print(f"   meta.date={m.get('date')} pulse_14={m.get('pulse_14')} guard.date={g.get('date')}")
