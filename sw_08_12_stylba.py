# -*- coding: utf-8 -*-
"""Находки 8 и 12: стоп на входа + два ✅ + «+0.00$» на един ред."""
import sys, json, tempfile, os
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.argv = ["x"]
import live_bot as lb

tr = {"direction": "long", "entry": 3300.00, "sym": "XAUUSD",
      "levels": {"tp1": 3310.0, "tp2": 3320.0, "tp3": 3340.0, "sl": 3300.0},
      "hit": {"tp1": True, "tp2": True}, "hit_px": {"tp1": 3310.0, "tp2": 3320.0}}
spot = {"mid": 3300.00, "src": "тест", "age": 5}

гола = (spot["mid"] - tr["entry"])
пл, n = lb._отворена_стълба(tr, spot)
print("гола разлика (старото число):  %+.2f$" % гола)
print("по стълбата (_отворена_стълба): %+.2f$  прибрани=%d" % (пл, n))

print("\n===== 8 · КЪДЕ СМЕ (--status) =====")
try:
    print(lb._status_msg(board=[], new_dir="long", trade=tr, s_trade=None,
                         spot_g=spot, spot_s=None, basis_g=0.0, basis_s=0.0,
                         guard={}, shield=False, date="2026-08-19", macro=None))
except Exception as e:
    import traceback; traceback.print_exc()

print("\n===== 12 · 🌙 Как мина денят =====")
d = Path(tempfile.mkdtemp())
(d / "live_journal.jsonl").write_text(
    "\n".join(json.dumps({"date": "2026-08-19", "run_utc": f"2026-08-19T{h:02d}:05:00"})
              for h in range(0, 21)), encoding="utf-8")
(d / "sent_log.jsonl").write_text(
    json.dumps({"utc": "2026-08-19T10:00:00"}) + "\n", encoding="utf-8")
try:
    print(lb._digest_msg(d, "2026-08-19", tr, None, spot, None, {}))
except Exception:
    import traceback; traceback.print_exc()
