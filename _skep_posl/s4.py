# -*- coding: utf-8 -*-
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, D); os.environ.setdefault("TELEGRAM_TOKEN","x"); os.environ.setdefault("TELEGRAM_CHAT_ID","1")
import pandas as pd, numpy as np, live_bot as LB

def строй(цена, истина, n=60):
    idx = pd.date_range("2026-06-01", periods=n*12, freq="2h", tz="UTC")
    intra = pd.DataFrame({"Close": np.full(len(idx), float(цена))}, index=idx)
    didx = pd.date_range("2026-06-01", periods=n, freq="1D", tz="UTC")
    daily = pd.DataFrame({"Close": np.full(n, float(цена + истина))}, index=didx)
    return intra, daily

# ПРОДЪЛЖАВАМЕ ЖИВИЯ ТРЕНД: -61.6$ днес, -3.04$/ден (мерено), цена 4639 замразена
# (най-лошият случай: цената НЕ расте, значи таванът НЕ расте с нея)
st = {"tf_basis_g": -61.599}
истина = -61.599
макс_греш = 0.0; отключвания = 0; ден = 0
руна_на_ден = 24
print(" ден  истина    върнато   грешка   таван    бележка")
for ден in range(1, 61):
    for r in range(руна_на_ден):
        истина -= 3.039 / руна_на_ден
        notes = []
        v = LB._tf_basis(st, "tf_basis_g", *строй(4639.0, истина), notes)
        г = abs(v - истина); макс_греш = max(макс_греш, г)
        if any("🔓" in n for n in notes): отключвания += 1
    _cap = max(LB.TF_BASIS_CAP, LB.TF_BASIS_CAP_PCT * abs(4639.0 + истина))
    if ден % 5 == 0 or (notes and ден < 40):
        print(f" {ден:>3} {истина:8.2f} {v:9.2f} {г:8.2f} {_cap:8.1f}   " + (notes[-1][:70] if notes else ""))
print(f"\nСЛЕД 60 ДНИ ПРОДЪЛЖЕН ТРЕНД (1440 ръна):")
print(f"  истина {истина:.2f}$ · върнато {v:.2f}$ · МАКСИМАЛНА грешка за целия период: {макс_греш:.2f}$")
print(f"  отключвания: {отключвания}")
