# -*- coding: utf-8 -*-
"""A · ТОЧНО сценарият на твърдението, срещу ПРЕДИ-поправката (v13.7-PRE)."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import _skep_lb_pre as lb

print("файл:", lb.__file__, lb.VERSION)
state = {"basis_g": 25.515, "basis_g_bar": 4400.0}
print("начален базис:", state["basis_g"])
print("BASIS_STUCK_N =", lb.BASIS_STUCK_N, " таван при 4639 =", round(lb._basis_cap(4639.0), 2))

notes = []
ИСТИНСКИ_БАЗИС = 47.0      # допускането на твърдението
bar = 4400.0
for i in range(200):
    bar += 1.3            # злато +260$ за 200 руна
    lb._basis_update(state, "basis_g", {"mid": bar - ИСТИНСКИ_БАЗИС, "src": "paxg-cb"},
                     bar, notes, cap=lb._basis_cap(bar), now_utc=None)
print("\nслед 200 руна САМО с резервата:")
print("  базис =", state.get("basis_g"))
print("  бележки:", notes)
print("  брояч basis_g_отказ =", state.get("basis_g_отказ"))
print("  ключ basis_g_отказани =", state.get("basis_g_отказани"))
print("  ключ basis_g_резерва =", state.get("basis_g_резерва"))

следа = {}
ref = bar - state["basis_g"]
res = lb._spot_sane({"mid": bar - ИСТИНСКИ_БАЗИС, "bid": 0, "ask": 0}, ref, 8.0,
                    bar_rng=3.3, spot_jump=0.5, следа=следа)
print("\nсанити при бар %.1f, замразен базис %.2f, истинска цена %.1f:" %
      (bar, state["basis_g"], bar - ИСТИНСКИ_БАЗИС))
print("  _spot_sane →", res, " следа:", следа)
