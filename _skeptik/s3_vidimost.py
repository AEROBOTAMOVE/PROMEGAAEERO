# -*- coding: utf-8 -*-
"""СКЕПТИК ТЕСТ 3 — чува ли се поправката?
Поправката пише в `notes`. Ред 4609 слага notes в live_journal.jsonl.
Въпрос: влиза ли този ред В НЯКОЯ ПРАТЕНА КАРТА (SENT)?"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import rig

rig.load("live_bot.py", name="lb3")
rig.patch()
OUT = rig.fresh(Path(__file__).parent / "v_out")

rig.CFG.update(gold_end="2026-08-19", intra_end="2026-08-19 12:00", gold_px=4600.0)
rig.set_now("2026-08-19T11:00:00")
rig.run(OUT, argv_extra=["--send"])

# ОТРОВЕН рън
rig.CFG.update(gold_end="2026-12-31", intra_end="2026-08-20 12:00")
rig.set_now("2026-08-20T11:00:00")
rig.run(OUT, argv_extra=["--send"])

j = rig.last_journal(OUT)
бел = [n for n in j["notes"] if "БЪДЕЩЕТО" in str(n)]
print("date след отровата :", j["date"])
print("бележка в журнала  :", бел or "НЯМА")
print("пратени карти      :", len(rig.SENT))
в_карта = [t[:80] for t in rig.SENT if "БЪДЕЩЕТО" in t]
print("карти, в които се СПОМЕНАВА:", в_карта or "🔴 НИТО ЕДНА — собственикът НЕ го вижда в Telegram")
