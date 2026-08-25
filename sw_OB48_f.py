# -*- coding: utf-8 -*-
"""ОБОРВАНЕ 48/финал: работи ли ЦЕЛИЯТ уикенд-път end-to-end (без --send)?"""
import sys, tempfile, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8'); sys.argv=["x"]
import live_bot as lb
out=Path(tempfile.mkdtemp(prefix="ob48_")); (out/"data").mkdir(parents=True, exist_ok=True)
for iso in ["2026-08-08T07:00","2026-08-08T13:00","2026-08-08T18:00","2026-08-08T02:00"]:
    print(f"— now_utc={iso} · София {lb._sofia_hour(iso)}ч · market_closed={lb._market_closed(iso)}")
    lb._weekend_cycle(out, iso, False)     # send=False → DRY
print("\nдневникът, който пътят записа:")
for ln in (out/"live_journal.jsonl").read_text(encoding="utf-8").splitlines():
    print("  ", ln)
print("\nweekend.json:", (out/"weekend.json").read_text(encoding="utf-8"))
