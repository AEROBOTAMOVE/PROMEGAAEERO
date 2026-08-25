# -*- coding: utf-8 -*-
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))
os.environ.setdefault("TG_TOKEN","x"); os.environ.setdefault("TG_CHAT","x")
import pandas as pd, numpy as np
import live_bot as lb

def построй(цена, базис, дни=30):
    idx = pd.date_range("2026-07-20", periods=дни, freq="D", tz="UTC")
    d = pd.DataFrame({"Close":[цена]*дни}, index=idx)
    ii,vv=[],[]
    for t in idx:
        for k in range(3): ii.append(t+pd.Timedelta(hours=k)); vv.append(цена-базис)
    return pd.DataFrame({"Close":vv}, index=pd.DatetimeIndex(ii)), d

for ИСТИНА in (-238.0, -400.0, +150.0):
    state={"tf_basis_g":-61.599,"tf_basis_g_отказ":0,"tf_basis_g_отказани":[]}
    intra,daily=построй(4639.0, ИСТИНА)
    отключен=None
    for r in range(1,41):
        notes=[]; v=lb._tf_basis(state,"tf_basis_g",intra,daily,notes)
        if отключен is None and abs(v-(-61.599))>0.001: отключен=r
    print("роловър/истина %+8.1f$ → отключен на рън %s · финална памет %+8.3f"
          % (ИСТИНА, отключен, state["tf_basis_g"]))

# ЗАБАВЕНИЯТ клон: 'няма данни' (тихият) — пада ли на 0.00?
state={"tf_basis_g":-61.599}
for r in range(1,15):
    notes=[]; v=lb._tf_basis(state,"tf_basis_g",None,None,notes)
    if r in (1,11,12,13): print("тих рън %2d: върнато %+7.3f | %s" % (r,v,notes[0] if notes else ""))
