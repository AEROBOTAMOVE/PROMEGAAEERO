# -*- coding: utf-8 -*-
"""ДВАТА РАЗЛИЧНИ ПРАВОПИСА на health['мъртви'] — проверка на живо."""
import sys, io
sys.argv = ["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import live_bot as lb

brd = [("1час", "long", 6, "strong", "СИЛЕН")] * 7
best = ("1час", "long", 6, "strong", "СИЛЕН")

print("A · МЪРТВИ С КРАТКИ КЛЮЧОВЕ (идват от _macro, live_bot.py:288)")
print(lb._standing_msg("long", best, 14.0, {"mid": 4365.2}, 4365.0, 4365.20, brd,
                       {"долар": True, "лихви": True, "миньори": True},
                       {"мъртви": ["лихви"]}, "2026-08-21T11:20"))

print("\nB · МЪРТВИ С ЕТИКЕТИ (идват от _макро_мъртво, live_bot.py:2850)")
print("   в тази клонка macro е {k: False for k in MACRO_LBL} — виж live_bot.py:2849")
print(lb._standing_msg("long", best, 14.0, {"mid": 4365.2}, 4365.0, 4365.20, brd,
                       {k: False for k in lb.MACRO_LBL},
                       {"мъртви": ["миньори (GDX)", "долар (DXY)", "лихви (FRED)"]},
                       "2026-08-21T11:20"))

print("\nC · СЪЩОТО, но с поправката «махни мъртвото краче» БЕЗ нормализация на името")
for етикети in (["лихви"], ["миньори (GDX)", "долар (DXY)", "лихви (FRED)"]):
    macro = ({"долар": True, "лихви": True, "миньори": True} if етикети == ["лихви"]
             else {k: False for k in lb.MACRO_LBL})
    реш = [k for k in ("долар", "лихви") if k in macro and k not in етикети]
    print(f"   мъртви={етикети} -> реш={реш}   "
          f"(живи според поправката: {len(реш)}; истински живи: "
          f"{len([k for k in ('долар','лихви') if not any(m.startswith(k) for m in етикети)])})")

print("\nD · с нормализация по ПЪРВАТА ДУМА")
for етикети in (["лихви"], ["миньори (GDX)", "долар (DXY)", "лихви (FRED)"]):
    кратки = {m.split(" ")[0] for m in етикети}
    реш = [k for k in ("долар", "лихви") if k not in кратки]
    print(f"   мъртви={етикети} -> кратки={sorted(кратки)} -> реш={реш}")
