# -*- coding: utf-8 -*-
import sys, io, importlib.util, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import numpy as np, pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def zaredi(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

def ramki(delta):
    """intra (часови) + daily, така че dneven-intraden = delta точно."""
    idx = pd.date_range("2026-08-01", periods=24*10, freq="h", tz="UTC")
    intra = pd.DataFrame({"Close": np.linspace(3700.0, 3720.0, len(idx))}, index=idx)
    r = intra.resample("1D").agg(Close=("Close","last")).dropna()
    daily = pd.DataFrame({"Close": r["Close"].values + delta,
                          "Open": r["Close"].values + delta,
                          "High": r["Close"].values + delta,
                          "Low":  r["Close"].values + delta}, index=r.index)
    return intra, daily

def scenarij(M, etiket):
    print("="*70)
    print(etiket, " (реда:", sum(1 for _ in open(M.__file__, encoding='utf-8')), ", TF_BASIS_STUCK_N =", M.TF_BASIS_STUCK_N, ")")
    print("="*70)
    N = M.TF_BASIS_STUCK_N
    K = "tf_basis_g"

    # --- закотвяме честна стойност -61.6 ---
    st = {}
    intra, daily = ramki(-61.6)
    for _ in range(40):
        notes = []
        v = M._tf_basis(st, K, intra, daily, notes)
    print("ЧЕСТНО ЗАКОТВЕНО: %s" % v)

    # --- ФАЗА 1: N-1 ръна БЕЗ данни (клонът _тих) ---
    for i in range(N-1):
        notes = []
        v = M._tf_basis(st, K, None, daily, notes)
    print("\n--- ФАЗА 1: %d ръна БЕЗ данни (_тих) ---" % (N-1))
    print("  върнато:", v)
    print("  _отказ  =", st.get(K+"_отказ"))
    print("  _тих    =", st.get(K+"_тих"))
    print("  _отказани =", st.get(K+"_отказани"))
    print("  последна бележка:", notes[-1] if notes else "(няма)")

    # --- ФАЗА 2: ЕДИН изроден образец над тавана ---
    intra_g, daily_g = ramki(-900.0)
    notes = []
    v2 = M._tf_basis(st, K, intra_g, daily_g, notes)
    print("\n--- ФАЗА 2: 1 рън с ЕДИН изрод (-900) ---")
    print("  върнато:", v2)
    for n in notes: print("  бележка:", n)
    print("  state['%s'] = %s" % (K, st.get(K)))
    otrova = abs(float(st.get(K) or 0) + 900.0) < 1.0
    print("  >>> ЗАКОТВЕН НА ГЛИЧА? ", "ДА — ДЕФЕКТ" if otrova else "НЕ")

    # --- ПОСОКА (б): 12 ИСТИНСКИ съгласни наблюдения ТРЯБВА да отключат ---
    st2 = {}
    intra0, daily0 = ramki(-61.6)
    for _ in range(40):
        M._tf_basis(st2, K, intra0, daily0, [])
    intra1, daily1 = ramki(-300.0)   # истинска нова стойност над тавана, СЪГЛАСНА
    otkl = None
    for i in range(1, N+3):
        notes = []
        v3 = M._tf_basis(st2, K, intra1, daily1, notes)
        if any("🔓" in n for n in notes):
            otkl = (i, notes, v3); break
    print("\n--- ПОСОКА (б): %d СЪГЛАСНИ истински наблюдения над тавана ---" % N)
    if otkl:
        print("  ОТКЛЮЧИ на рън %d → %s" % (otkl[0], otkl[2]))
        for n in otkl[1]:
            if "🔓" in n: print("  бележка:", n)
    else:
        print("  НЕ ОТКЛЮЧИ за %d ръна — стойност %s" % (N+2, v3))
    print()

for path, tag in [(os.path.join(BASE,"_chern","live_bot_STAR.py"), "СТАР 3b6a915e (16:43) — версията, която агентът е пуснал"),
                  (os.path.join(BASE,"live_bot.py"),               "ТЕКУЩ live_bot.py (HEAD d3794e27, v14.2)")]:
    scenarij(zaredi(path, "m_"+tag[:5].strip()), tag)
