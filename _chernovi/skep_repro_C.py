# -*- coding: utf-8 -*-
"""СКЕПТИК · В) СЪЩИЯТ тест срещу СТАРИЯ v13.6 (commit 3b08ec96) и срещу ЖИВИЯ HEAD."""
import sys, io, os, importlib.util
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
БАЗА = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def зареди(път, име):
    sys.path.insert(0, os.path.dirname(път))
    сп = importlib.util.spec_from_file_location(име, път)
    м = importlib.util.module_from_spec(сп); sys.modules[име] = м
    сп.loader.exec_module(м)
    sys.path.pop(0)
    return м

def тест(м, етикет):
    cap = м._basis_cap(4700.0, "XAUUSD"); bar = 4700.0
    state = {"basis_g": 25.515, "basis_g_bar": bar}
    отключвания = 0; първа = None
    for i in range(200):
        n = []
        м._basis_update(state, "basis_g", {"mid": bar - 100.0, "src": "swq"}, bar, n, cap=cap)
        if any("🔓" in x for x in n) and първа is None: първа = (i+1, n[0])
        отключвания += sum("🔓" in x for x in n)
    print("\n%s  (VERSION=%s)" % (етикет, getattr(м, "VERSION", "?")))
    print("   cap=%.1f$  истина=100$  ->  basis_g=%s  брояч=%s  отключвания=%d"
          % (cap, state.get("basis_g"), state.get("basis_g_отказ"), отключвания))
    print("   първо отключване:", "НЯМА (ЗАКЛЮЧЕН)" if първа is None else "рун %d · %s" % първа)

тест(зареди(os.path.join(БАЗА, "_chernovi", "star", "live_bot.py"), "стар_lb"),
     "СТАР v13.6 (3b08ec96) — версията, цитирана в твърдението")
тест(зареди(os.path.join(БАЗА, "live_bot.py"), "жив_lb"),
     "ЖИВ HEAD 3b6a915e — файлът, който тече сега")
