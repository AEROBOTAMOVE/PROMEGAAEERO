# -*- coding: utf-8 -*-
"""СКЕПТИК · Б) контролата на твърдението + анти-глич проверка на ЖИВИЯ код."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ПЪТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ПЪТ)
import live_bot as lb
cap = lb._basis_cap(4700.0, "XAUUSD"); bar = 4700.0

def пусни(поредица, име):
    state = {"basis_g": 25.515, "basis_g_bar": bar}
    отключвания = 0
    for i, ист in enumerate(поредица, 1):
        n = []
        lb._basis_update(state, "basis_g", {"mid": bar - ист, "src": "swq"}, bar, n, cap=cap)
        отключвания += sum("🔓" in x for x in n)
    print("%-52s basis_g=%8.3f  брояч=%-4s отключвания=%d"
          % (име, state.get("basis_g"), state.get("basis_g_отказ"), отключвания))

# 1) ТВЪРДЕНИЕТО: истина 100$ НАД тавана 94$, 200 руна
пусни([100.0]*200, "1) истина 100$ (НАД cap 94$) x200")
# 2) КОНТРОЛАТА от твърдението: истина 90$, ПОД тавана
пусни([90.0]*30, "2) истина 90$ (ПОД cap 94$) x30")
# 3) АНТИ-ГЛИЧ: единичен 100$ глич сред здрави стойности, 200 руна
seq = []
for i in range(200):
    seq.append(100.0 if i % 20 == 0 else 25.5)
пусни(seq, "3) единичен глич 100$ на всеки 20 руна x200")
# 4) АНТИ-ГЛИЧ: РАЗПРЪСНАТИ гличове подред (различни стойности), 12 поредни
пусни([100.0, -300.0, 250.0, -180.0, 400.0, 95.0, -220.0, 310.0,
       -150.0, 500.0, 120.0, -400.0], "4) 12 поредни РАЗПРЪСНАТИ глича")
