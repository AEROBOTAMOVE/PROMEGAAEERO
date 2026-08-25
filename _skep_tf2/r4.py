# -*- coding: utf-8 -*-
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))
os.environ.setdefault("TG_TOKEN","x"); os.environ.setdefault("TG_CHAT","x")
import pandas as pd
import live_bot as lb
def построй(цена, базис, дни=30):
    idx=pd.date_range("2026-07-20",periods=дни,freq="D",tz="UTC")
    d=pd.DataFrame({"Close":[цена]*дни},index=idx); ii,vv=[],[]
    for t in idx:
        for k in range(3): ii.append(t+pd.Timedelta(hours=k)); vv.append(цена-базис)
    return pd.DataFrame({"Close":vv},index=pd.DatetimeIndex(ii)),d

# СРЕБРОТО: cap се подава ФИКСИРАН 9.0 → ценовият таван НЕ важи тук
print("сребърен таван (фиксиран, подаден отвън):", lb.TF_BASIS_CAP_S)
for ИСТИНА in (-25.0, -60.0):
    state={"tf_basis_s":-0.173,"tf_basis_s_отказ":0,"tf_basis_s_отказани":[]}
    intra,daily=построй(69.85,ИСТИНА)
    отк=None
    for r in range(1,31):
        notes=[]; v=lb._tf_basis(state,"tf_basis_s",intra,daily,notes,cap=lb.TF_BASIS_CAP_S)
        if отк is None and abs(v-(-0.173))>1e-6: отк=r
    print("сребро истина %+7.1f$ (таван 9.0 фиксиран) → отключен на рън %s · памет %+8.3f"%(ИСТИНА,отк,state["tf_basis_s"]))

# ГЛИЧ, не истина: един изрод сред верни стойности — НЕ бива да презакотвя
state={"tf_basis_g":-61.599,"tf_basis_g_отказ":0,"tf_basis_g_отказани":[]}
ok_i,ok_d=построй(4639.0,-61.6); gl_i,gl_d=построй(4639.0,-900.0)
for r in range(1,25):
    notes=[]
    i,dd=(gl_i,gl_d) if r%6==0 else (ok_i,ok_d)   # глич на всеки 6-и рън
    lb._tf_basis(state,"tf_basis_g",i,dd,notes)
print("глич 1-от-6 за 24 ръна → памет %+8.3f (истина -61.6) · отказ=%s"%(state["tf_basis_g"],state.get("tf_basis_g_отказ")))
