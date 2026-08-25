# -*- coding: utf-8 -*-
"""СКЕПТИК · възпроизвеждане на твърдението: «прекъсвачът е зад същия таван».
Точно сценарият от твърдението: cap=94$, ИСТИНА=+100$ (НАД тавана),
замразена стойност 25.515, 200 поредни руна.
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ПЪТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ПЪТ)
import live_bot as lb

print("файл:", lb.__file__)
print("BASIS_STUCK_N =", lb.BASIS_STUCK_N)
cap = lb._basis_cap(4700.0, "XAUUSD")
print("cap = _basis_cap(4700.0,'XAUUSD') = %.2f$" % cap)

ИСТИНА = 100.0                     # базисът наистина е +100$ — НАД тавана 94$
bar = 4700.0
state = {"basis_g": 25.515, "basis_g_bar": 4700.0}
notes_all = []
първо_отключване = None
for i in range(1, 201):
    notes = []
    out = lb._basis_update(state, "basis_g", {"mid": bar - ИСТИНА, "src": "swq"},
                           bar, notes, cap=cap, now_utc=None)
    if any("🔓" in n for n in notes) and първо_отключване is None:
        първо_отключване = (i, notes[:])
    notes_all += [(i, n) for n in notes]

print("\n--- след 200 руна ---")
print("basis_g =", state.get("basis_g"), " брояч _отказ =", state.get("basis_g_отказ"))
print("първо отключване:", първо_отключване)
print("\nпървите 3 бележки:")
for i, n in notes_all[:3]:
    print("  рун %d: %s" % (i, n))
print("последната бележка:")
if notes_all:
    print("  рун %d: %s" % notes_all[-1])
