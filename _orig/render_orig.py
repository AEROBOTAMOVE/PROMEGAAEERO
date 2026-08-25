# -*- coding: utf-8 -*-
"""Рендерира СТАРИТЕ (HEAD) дневни карти 25/26/27 — както Коста ги е виждал."""
import importlib.util, sys, json, re, html
from pathlib import Path

БАЗА = Path(__file__).resolve().parent
DEP = БАЗА.parent

def внеси(път, име):
    sp = importlib.util.spec_from_file_location(име, str(път))
    m = importlib.util.module_from_spec(sp)
    sys.modules[име] = m
    sp.loader.exec_module(m)
    return m

lb = внеси(БАЗА / "live_bot_HEAD.py", "lb_old")

def чист(t):
    return re.sub(r"<[^>]+>", "", html.unescape(str(t)))

tr = {"direction": "long", "entry": 4358.00, "opened": "2026-08-11T09:12",
      "levels": {"tp1": 4365.5, "tp2": 4370.0, "tp3": 4378.0, "sl": 4338.0},
      "hit": {"tp1": True, "tp2": True}, "sym": "XAUUSD"}

вр = БАЗА / "_tmp"
вр.mkdir(exist_ok=True)
(вр / "live_journal.jsonl").write_text(
    "\n".join(json.dumps({"date": "2026-08-11"}) for _ in range(183)), encoding="utf-8")
(вр / "sent_log.jsonl").write_text("\n".join(
    json.dumps({"utc": "2026-08-11T09:00", "tag": t}) for t in
    ("pulse", "pulse", "standing", "standing", "cq-ref")), encoding="utf-8")

К = {}
# ── 26 равносметка: с отворена сделка + 1 стоп
К["26a СТАРА РАВНОСМЕТКА (с отворена)"] = lb._digest_msg(
    вр, "2026-08-11", tr, None, {"mid": 4365.2}, None, {"long": 1})
# ── 26б равносметка: празен ден
К["26b СТАРА РАВНОСМЕТКА (празен ден)"] = lb._digest_msg(
    вр, "2026-08-11", None, None, {"mid": 4365.2}, None, {})
# ── 26в петък (седмичен раздел)
К["26c СТАРА РАВНОСМЕТКА (петък)"] = lb._digest_msg(
    вр, "2026-08-11", tr, None, {"mid": 4365.2}, None, {}, weekly_part=True)

# ── 25 кибер квант.  ВАЖНО: _cq_next_event чете e["dt"], НЕ e["date"]/e["time"].
cq_ok = {"score": 29.1, "zone": "Натрупване 🟢", "fg_crypto": 29, "fg_stock": 64,
         "clusters": {"валуация": 37, "моментум": 10, "настроения": 25, "on-chain": 47},
         "events": [{"name": "CPI — Индекс на потребителските цени (САЩ)",
                     "dt": "2026-08-12T12:30:00Z", "impact": "high"}]}
cq_no = dict(cq_ok, events=[])
try:
    К["25a СТАРА КИБЕР КВАНТ (идва събитие)"] = lb._cq_msg(cq_ok, "2026-08-11T06:01",
                                                           fng_live={"value": 34, "cls": "Fear"})
except Exception as e:
    К["25a СТАРА КИБЕР КВАНТ (идва събитие)"] = f"[гръмна: {type(e).__name__}: {e}]"
try:
    К["25b СТАРА КИБЕР КВАНТ (няма събитие)"] = lb._cq_msg(cq_no, "2026-08-11T06:01")
except Exception as e:
    К["25b СТАРА КИБЕР КВАНТ (няма събитие)"] = f"[гръмна: {type(e).__name__}: {e}]"

# ── 27 уикенд, трите слота
for сл in ("сутрин", "следобед", "вечер"):
    К[f"27 СТАРА УИКЕНД {сл}"] = lb._weekend_msg(сл, "2026-08-08")

for име, v in К.items():
    т = чист(v)
    print("=" * 64)
    print(f"{име}   [{len(т.splitlines())} реда · {len(т)} знака]")
    print("-" * 64)
    print(т)
    print()

# колко различни картички има в уикенд-пула и колко са дълги
print("=" * 64)
for сл, pool in lb.WEEKEND_MSGS.items():
    print(f"{сл}: {len(pool)} картички · най-дългата {max(len(x) for x in pool)} знака")
