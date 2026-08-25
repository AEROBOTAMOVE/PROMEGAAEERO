# -*- coding: utf-8 -*-
"""СКЕПТИК S1: реплика на should_sig върху ЖИВИТЕ файлове, БЕЗ да вярвам на чужд изход.
Импортирам ИСТИНСКИТЕ константи и функции от live_bot.py, не ги преписвам."""
import sys, json, io
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
import pandas as pd
import live_bot as LB

print("ИМПОРТИРАНИ ОТ live_bot.py:")
print("  REOFFER_H         =", LB.REOFFER_H)
print("  REOFFER_MAX_AGE_H =", LB.REOFFER_MAX_AGE_H)
print("  REOFFER_LO/HI     =", LB.REOFFER_LO, LB.REOFFER_HI)
print("  РЕОФЕР_КЛАС       =", LB.РЕОФЕР_КЛАС)
print("  STANDING_H        =", LB.STANDING_H)

last = json.load(open("live/last_sent.json", encoding="utf-8"))
print("\nЖИВ last_sent.json:", json.dumps(last, ensure_ascii=False))

# последен запис от живия дневник
ln = [l for l in open("live/live_journal.jsonl", encoding="utf-8") if l.strip()]
rec = json.loads(ln[-1])
now_utc = rec["run_utc"]
bd = rec["board"]
# board в кода е списък от (lbl, dir, score, tier, надпис)
board = [(l, v[0], v[1], v[2], "") for l, v in bd.items()]
rank = {"premium": 3, "strong": 2, "medium": 1, "weak": 0}
actionable = [b for b in board if b[1] != "wait" and b[3] != "weak"]
_бавност = {l: i for i, (l, *_) in enumerate(LB.TFS)}
best = max(board, key=lambda x: (rank[x[3]], x[2], _бавност.get(x[0], 0))) if actionable else board[0]
new_dir = best[1] if actionable else None

# ключът — ТОЧНО както е в live_bot.py ред 3864-3865
_отч = sorted({f"{d}:{t}" for _l, d, _s, t, _ in board if t != "weak" and d != "wait"})
key = f"{len(_отч)}|" + ";".join(_отч)

mins_since = (pd.Timestamp(now_utc) - pd.Timestamp(last["sent_utc"])).total_seconds() / 60
tier_up = bool(new_dir and rank.get(best[3], 0) > rank.get(last.get("tier", "weak"), 0) and new_dir == last.get("dir"))
cool_ok = (mins_since is None or mins_since >= 45
           or (new_dir is not None and new_dir != last.get("dir") and mins_since >= 15)
           or tier_up)
key_age_h = None
if last.get("key") == key and last.get("key_since"):
    key_age_h = (pd.Timestamp(now_utc) - pd.Timestamp(last["key_since"])).total_seconds() / 3600
trade = None
reoffer = (bool(actionable) and trade is None and new_dir is not None
           and rank.get(best[3], 0) >= rank.get(LB.РЕОФЕР_КЛАС, 1)
           and mins_since is not None and mins_since >= LB.REOFFER_H * 60
           and key_age_h is not None and key_age_h <= LB.REOFFER_MAX_AGE_H
           and LB._reoffer_hour_ok(now_utc))
should_sig = bool(actionable) and (last.get("key") != key or tier_up or reoffer) and cool_ok

print(f"\n=== РЕПЛИКА при {now_utc} (последният ЖИВ рън) ===")
print("  борд          ", {l: v for l, v in bd.items()})
print("  key            ", key)
print("  last.key       ", last.get("key"))
print("  key == last.key", key == last.get("key"))
print("  actionable     ", bool(actionable), f"({len(actionable)}/7)")
print("  best           ", best[0], best[1], best[3])
print("  mins_since     ", round(mins_since, 1))
print("  tier_up        ", tier_up)
print("  cool_ok        ", cool_ok)
print("  key_age_h      ", None if key_age_h is None else round(key_age_h, 2))
print("  hour_ok(София) ", LB._reoffer_hour_ok(now_utc), "· час", LB._sofia_hour(now_utc))
print("  reoffer        ", reoffer)
print("  gate.ok (дневник)", rec["gate"]["ok"], "·", rec["gate"].get("by"))
print("  SHOULD_SIG     ", should_sig)
print("  → pending_trade възможен?", bool(should_sig and actionable and rec["gate"]["ok"]))
