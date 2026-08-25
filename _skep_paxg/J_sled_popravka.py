# -*- coding: utf-8 -*-
"""J · СЪЩИЯТ сценарий срещу ЖИВИЯ файл (v14.0, поправката вече е вътре)."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import live_bot as lb
print("файл:", os.path.basename(lb.__file__), lb.VERSION, " РЕЗЕРВА_ОТКОТВИ =", lb.РЕЗЕРВА_ОТКОТВИ,
      " PAXG_ПРЕМИЯ =", lb.PAXG_ПРЕМИЯ)
ИСТИНА = 47.0
state = {"basis_g": 25.515, "basis_g_bar": 4400.0}
notes = []; bar = 4400.0
първа = None
for i in range(1, 201):
    bar += 1.3
    n = []
    lb._basis_update(state, "basis_g", {"mid": bar - ИСТИНА, "src": "paxg-cb"}, bar, n,
                     cap=lb._basis_cap(bar), now_utc=None)
    for x in n:
        notes.append((i, x))
        if първа is None: първа = (i, x)
print("първа бележка:", първа)
print("общо бележки за 200 руна:", len(notes))
print("първите закотвяния:", [i for i, x in notes if "🔓" in x][:6])
print("базис накрая: %.3f (истина %.1f)  брояч резерва: %s" % (state["basis_g"], ИСТИНА, state.get("basis_g_резерва")))
следа = {}
ok = lb._spot_sane({"mid": bar-ИСТИНА, "bid":0, "ask":0}, bar - state["basis_g"], 8.0,
                   bar_rng=3.3, spot_jump=0.5, следа=следа)
print("санити накрая: мина=%s разлика=%.2f$" % (следа["мина"], следа["разлика"]))
