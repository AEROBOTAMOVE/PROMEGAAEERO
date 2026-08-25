# -*- coding: utf-8 -*-
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, D)
os.environ.setdefault("TELEGRAM_TOKEN","x"); os.environ.setdefault("TELEGRAM_CHAT_ID","1")
import live_bot as lb

BAR = 4649.3; ИСТИНА = 58.8; SPOT = BAR - ИСТИНА

def прогон(cap, st, moved_bar, n=60):
    for i in range(1, n+1):
        nt = []
        bar = moved_bar if moved_bar else BAR
        v = lb._basis_update(st, "basis_g", {"mid": bar - ИСТИНА, "src": "swq"}, bar, nt,
                             cap=cap, now_utc="2026-08-21T10:30")
        if abs(v - ИСТИНА) < 0.5:
            return i, v
    return None, st.get("basis_g")

print("=== 1) РОЛОВЪР, барът скача заедно с базиса (moved=True) — тук cap НАИСТИНА решава ===")
for cap, ет in ((40.0, "cap=40 (убитият)"), (lb._basis_cap(BAR), "cap=92.99 (живият)")):
    st = {"basis_g": 25.515, "basis_g_bar": round(BAR - 40.0, 3)}   # предишен бар 40$ по-ниско
    i, v = прогон(cap, st, moved_bar=BAR)
    print(f"  {ет}: верен базис на рън {i} → {v:+.3f}")

print()
print("=== 2) СТУДЕН СТАРТ, празна памет ===")
for cap, ет in ((40.0, "cap=40 (убитият)"), (lb._basis_cap(BAR), "cap=92.99 (живият)")):
    st = {}
    i, v = прогон(cap, st, moved_bar=None)
    print(f"  {ет}: верен базис на рън {i} → {v:+.3f}")

print()
print("=== 3) МОЖЕ ЛИ cap=40 да ЗАКЛЮЧИ ЗАВИНАГИ? 500 ръна, истина 200$ (далеч над всеки таван) ===")
ИСТИНА = 200.0
for cap, ет in ((40.0, "cap=40"), (lb._basis_cap(BAR), "cap=92.99")):
    st = {"basis_g": 25.515, "basis_g_bar": round(BAR, 3)}
    i, v = прогон(cap, st, moved_bar=None, n=500)
    print(f"  {ет}: верен базис на рън {i} → {v:+.3f}")
