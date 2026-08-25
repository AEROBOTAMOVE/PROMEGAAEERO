# -*- coding: utf-8 -*-
import sys, io, os, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = pathlib.Path(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
sys.path.insert(0, str(ROOT))
os.environ.setdefault("TG_TOKEN","x"); os.environ.setdefault("TG_CHAT","1")
import live_bot as L
import pandas as pd, numpy as np

def рамки(цена=4639.0, истина=-130.0, n=40):
    idx = pd.date_range("2026-07-01", periods=n, freq="D", tz="UTC")
    intra_idx = pd.date_range("2026-07-01", periods=n*12, freq="2h", tz="UTC")
    # интрадей: Close = цена ; дневен Close = цена + истина
    intra = pd.DataFrame({"Close": np.full(len(intra_idx), цена)}, index=intra_idx)
    daily = pd.DataFrame({"Close": np.full(n, цена + истина)}, index=idx)
    return intra, daily

def гони(истина, цена, cap=None, руна=150, старо=-61.599, key="tf_basis_g"):
    intra, daily = рамки(цена, истина)
    state = {key: старо}
    бележки_всички = []
    for i in range(руна):
        notes = []
        v = L._tf_basis(state, key, intra, daily, notes, cap=cap)
        бележки_всички.append((i+1, round(v,3), list(notes)))
    return state, бележки_всички

print("═══ A · ТОЧНО ТВЪРДЯНИЯТ СЦЕНАРИЙ: истина -130$, злато 4639$, 150 руна ═══")
st, b = гони(-130.0, 4639.0)
print("  таван, който кодът смята: max(120, 0.03*%.0f) = %.2f" % (4639.0-130.0, max(120.0, 0.03*abs(4639.0-130.0))))
print("  state след 150 руна:", {k:v for k,v in st.items() if not k.endswith("_отказани")})
print("  върнато на 150-ия рун:", b[-1][1])
print("  бележки на рун 1:", b[0][2])
print("  бележки на рун 150:", b[-1][2])
