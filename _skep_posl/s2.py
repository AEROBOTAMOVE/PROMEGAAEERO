# -*- coding: utf-8 -*-
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, D)
os.environ.setdefault("TELEGRAM_TOKEN","x"); os.environ.setdefault("TELEGRAM_CHAT_ID","1")
import pandas as pd, numpy as np
import live_bot as LB

def строй(цена, истина, n=60):
    idx = pd.date_range("2026-06-01", periods=n*12, freq="2h", tz="UTC")
    intra = pd.DataFrame({"Close": np.full(len(idx), float(цена))}, index=idx)
    didx = pd.date_range("2026-06-01", periods=n, freq="1D", tz="UTC")
    daily = pd.DataFrame({"Close": np.full(n, float(цена + истина))}, index=didx)
    return intra, daily

def пусни(ключ, истина, цена, руна, cap=None, етикет="", старо=None):
    st = {}
    if старо is not None: st[ключ] = старо
    журнал = []
    for i in range(руна):
        notes = []
        v = LB._tf_basis(st, ключ, *строй(цена, истина), notes, cap=cap)
        журнал.append((i+1, round(v,3), list(notes)))
    print(f"\n=== {етикет} · истина {истина:+g} · цена {цена} · cap={cap} · старо={старо} ===")
    for i, v, n in журнал:
        if n or i in (1, руна):
            print(f"  рън {i:>3}: върнато {v:+9.3f}  " + (" | ".join(n) if n else ""))
    print("  краен state:", {k: vv for k, vv in st.items()})

# A) злато, истина НАД дори процентния таван
пусни("tf_basis_g", -300.0, 4639.0, 30, етикет="ЗЛАТО истина -300$ (над таван 135)", старо=-61.599)
# B) сребро — фиксиран cap 9.0, истина -9.6 (точно случая от находката)
пусни("tf_basis_s", -9.6, 65.0, 30, cap=LB.TF_BASIS_CAP_S, етикет="СРЕБРО истина -9.6$ (таван 9.0)", старо=-0.173)
