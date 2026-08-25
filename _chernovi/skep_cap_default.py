# -*- coding: utf-8 -*-
import sys, io, importlib.util, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, D)
os.environ.setdefault("TELEGRAM_TOKEN","x"); os.environ.setdefault("TELEGRAM_CHAT_ID","1")
import live_bot as LB

print("подпис по подразбиране:", LB._basis_update.__defaults__)
import inspect
print("ред на дефиницията:", inspect.getsourcelines(LB._basis_update)[1])
print("BASIS_STUCK_N =", LB.BASIS_STUCK_N, "· _basis_cap(4649.3)=", round(LB._basis_cap(4649.3,"XAUUSD"),2),
      "· _roll_jump(4649.3)=", round(LB._roll_jump(4649.3,"XAUUSD"),2))
print()

BAR = 4649.3
ИСТИНА = 58.8
SPOT = BAR - ИСТИНА

def прогон(cap_kw, n=40, старо=25.515, етикет=""):
    st = {"basis_g": старо, "basis_g_bar": round(BAR,3)}
    посл = None
    for i in range(1, n+1):
        notes = []
        kw = {} if cap_kw is None else {"cap": cap_kw}
        v = LB._basis_update(st, "basis_g", {"mid": SPOT, "src": "swq"}, BAR, notes, **kw)
        if any("🔓" in x for x in notes):
            print(f"  [{етикет}] рън {i}: ОСВОБОДЕН → {v:+.3f} | {notes[0][:80]}")
            посл = i
            break
    print(f"  [{етикет}] след {n} ръна: базис={st['basis_g']:+.3f} брояч={st.get('basis_g_отказ')} "
          f"освободен_на={посл}")
    return st, посл

print("=== A) БЕЗ cap=  (тоест поведението по подразбиране ДНЕС) ===")
прогон(None, етикет="без cap")
print()
print("=== B) с cap=40.0  (СТАРАТА стойност по подразбиране, твърдяният убит дефект) ===")
прогон(40.0, етикет="cap=40")
print()
print("=== C) с cap=_basis_cap(4649.3)=92.99 (както са живите извиквачи) ===")
прогон(LB._basis_cap(BAR,"XAUUSD"), етикет="cap=92.99")
