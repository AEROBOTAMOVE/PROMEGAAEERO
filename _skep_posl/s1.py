# -*- coding: utf-8 -*-
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, D)
os.environ.setdefault("TELEGRAM_TOKEN","x"); os.environ.setdefault("TELEGRAM_CHAT_ID","1")
import pandas as pd, numpy as np
import live_bot as LB

print("TF_BASIS_CAP =", LB.TF_BASIS_CAP, "| PCT =", LB.TF_BASIS_CAP_PCT,
      "| STUCK_N =", LB.TF_BASIS_STUCK_N, "| CAP_S =", LB.TF_BASIS_CAP_S)

def строй(цена_интра, истина, n=60):
    """intra 5м бара за n дни; daily = intra + истина (значи Close_d - Close = истина)."""
    idx = pd.date_range("2026-06-01", periods=n*12, freq="2h", tz="UTC")
    intra = pd.DataFrame({"Close": np.full(len(idx), float(цена_интра))}, index=idx)
    didx = pd.date_range("2026-06-01", periods=n, freq="1D", tz="UTC")
    daily = pd.DataFrame({"Close": np.full(n, float(цена_интра + истина))}, index=didx)
    return intra, daily

def пусни(истина, цена, руна, cap=None, етикет=""):
    st = {}
    видени = {}
    for i in range(руна):
        notes = []
        v = LB._tf_basis(st, "tf_basis_g", *строй(цена, истина), notes, cap=cap)
        for b in notes:
            видени[b] = видени.get(b, 0) + 1
    print(f"\n--- {етикет}: истина {истина:+g}$ · цена {цена}$ · {руна} руна · cap={cap} ---")
    print("  state:", {k: v2 for k, v2 in st.items() if not k.endswith('_отказани')})
    print("  върнато:", v)
    for b, c in видени.items():
        print(f"   [{c}x] {b}")

# 1) точният сценарий на находката: истина -130, злато ~4639
пусни(-130.0, 4639.0, 150, етикет="ТВЪРДЕНИЕТО (-130$ при 4639$)")
