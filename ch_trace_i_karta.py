# -*- coding: utf-8 -*-
"""`_gate_trace` вече носи ВСИЧКИ числа на клетката — и е в обхват на картата."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.argv = ["x"]
import live_bot as lb
from pathlib import Path

S = json.loads(Path("backtest_stats.json").read_text(encoding="utf-8"))
lb._сребро_разход(S, None)

print("=== _gate_trace СЛЕД ЖИВО ИЗВИКВАНЕ (ред 3263-3267) ===")
for d, s_n in (("long", 1), ("long", 2), ("long", 5), ("short", 1)):
    tr = {}
    txt, ok = lb._advice_entry(d, s_n, S, None, False, 0, sym="XAUUSD", trace=tr)
    print("  %-5s стрийк=%d вход=%-3s trace=%s" % (d, s_n, "ДА" if ok else "не",
                                                   json.dumps(tr, ensure_ascii=False)))
print("  -> `мерено` носи КОФА, WIN, NET, N, LO, HI. Всичко нужно, вече сметнато.")
print("  -> НО `_gate_trace` НЕ се подава на `_sig_msg` (ред 3507-3513). В обхват е.")

print()
print("=== КАК ИЗГЛЕЖДА КАРТАТА ДНЕС (изпълнено `_sig_msg`) ===")
entry = 3400.00
lv = lb._levels(entry, "long")
print("  _levels ->", lv)
tr = {}
advice, ok = lb._advice_entry("long", 1, S, None, False, 0, sym="XAUUSD", trace=tr)
spot = {"mid": 3400.30, "src": "gold"}
m = lb._sig_msg("long", 7.0, 3, "premium", spot, 3400.10, None, lv, entry,
                advice, {}, 1, {"streaks": {"long": 1}}, S,
                balance=5000.0, risk_pct=1.0, adv_ok=ok,
                zone=("A", "силна зона"))
print(lb._strip_html(m))
print()
print("  РЕДОВЕ:", len(m.split(chr(10))))
