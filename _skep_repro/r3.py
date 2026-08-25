# -*- coding: utf-8 -*-
import sys, io, os, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = pathlib.Path(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
sys.path.insert(0, str(ROOT)); os.environ.setdefault("TG_TOKEN","x"); os.environ.setdefault("TG_CHAT","1")
import live_bot as L
import pandas as pd, numpy as np
def рамки(цена, истина, n=40):
    i2 = pd.date_range("2026-07-01", periods=n*12, freq="2h", tz="UTC")
    i1 = pd.date_range("2026-07-01", periods=n, freq="D", tz="UTC")
    return (pd.DataFrame({"Close": np.full(len(i2), цена)}, index=i2),
            pd.DataFrame({"Close": np.full(n, цена+истина)}, index=i1))
def гони(истина, цена, cap=None, руна=40, старо=-61.599, key="tf_basis_g"):
    intra, daily = рамки(цена, истина); state={key:старо}; out=[]
    for i in range(руна):
        notes=[]; v=L._tf_basis(state,key,intra,daily,notes,cap=cap); out.append((i+1,round(v,3),notes))
    return state,out

print("═══ B · ИСТИНА ДАЛЕЧ НАД ТАВАНА: -300$ при злато 4639 (таван ~130) ═══")
st,o = гони(-300.0, 4639.0)
for i,v,n in o:
    if n or i in (1,11,12,13,24,25,40): print("  рун %3d → %10.3f  %s" % (i,v,"; ".join(n)))
print("  край:", {k:v for k,v in st.items()})

print()
print("═══ C · СРЕБРО: истина -20$ при таван cap=9.0 (както в находката) ═══")
st,o = гони(-20.0, 65.0, cap=L.TF_BASIS_CAP_S, старо=-0.173, key="tf_basis_s")
for i,v,n in o:
    if n or i in (1,12,13,40): print("  рун %3d → %10.3f  %s" % (i,v,"; ".join(n)))
print("  край:", {k:v for k,v in st.items()})

print()
print("═══ D · ТВЪРДЕНИЕТО «-9.6$ пази стария завинаги» при сребро ═══")
st,o = гони(-9.6, 65.0, cap=L.TF_BASIS_CAP_S, старо=-0.173, key="tf_basis_s", руна=40)
print("  краен state:", {k:v for k,v in st.items()})
print("  последна бележка:", o[-1][2])
