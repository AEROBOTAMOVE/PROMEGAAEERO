# -*- coding: utf-8 -*-
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, D)
os.environ.setdefault("TELEGRAM_TOKEN","x"); os.environ.setdefault("TELEGRAM_CHAT_ID","1")
import live_bot as lb

_БАР76 = 4649.3

def тестП76д(етикет):
    """ДОСЛОВНО кодът на теста от selftest.py §П76д (редове 5064-5071)."""
    _ст76д = {"basis_g": 25.515, "basis_g_bar": _БАР76 - 2}
    _н76д = []
    _сп76д = {"bid": _БАР76 - 58.8, "ask": _БАР76 - 58.6, "mid": _БАР76 - 58.8, "src": "т"}
    for _ in range(20):
        _b76д = lb._basis_update(_ст76д, "basis_g", _сп76д, _БАР76, _н76д, now_utc="2026-08-21T10:30")
    ok = abs(_b76д - 58.8) < 0.5
    print(f"  [{етикет}] по подразбиране cap={lb._basis_update.__defaults__[0]!r} → "
          f"базис {_b76д:+.2f} · тестът е {'ЗЕЛЕН ✅' if ok else 'ЧЕРВЕН ❌'}")
    return ok

print("=== Проверявам ЗАЩИТАВА ЛИ предложеният тест срещу връщането на дефекта ===")
тестП76д("както е сега (cap=None)")
lb._basis_update.__defaults__ = (40.0, None, None)   # връщам УБИТИЯ дефект
тестП76д("РЕГРЕСИЯ, върнат cap=40.0")
